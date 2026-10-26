from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.cache import invalidate_catalog_cache
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.repositories import cart_repository, order_repository
from app.services._transactions import commit


class OrderOperationError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def create_order_from_cart(db: Session, user_id: int) -> Order:
    try:
        cart = cart_repository.get_for_user(db, user_id, lock=True)
        if cart is None or not cart.items:
            raise OrderOperationError("Cart is empty", 400)

        cart_items = sorted(cart.items, key=lambda item: item.product_id)
        if any(item.product is None for item in cart_items):
            raise OrderOperationError(
                "A product in the cart is no longer available", 409
            )
        total = sum(
            (item.product.price * item.quantity for item in cart_items),
            start=Decimal("0.00"),
        )
        order = order_repository.add(
            db,
            Order(
                user_id=user_id,
                status=OrderStatus.PENDING,
                total_amount=total,
                items=[
                    OrderItem(
                        product_id=item.product.id,
                        product_name=item.product.name,
                        unit_price=item.product.price,
                        quantity=item.quantity,
                    )
                    for item in cart_items
                ],
            ),
        )

        for item in cart_items:
            if not order_repository.decrement_stock_if_available(
                db, item.product_id, item.quantity
            ):
                raise OrderOperationError(
                    f"Insufficient stock for product '{item.product.name}'",
                    409,
                )
        cart_repository.clear_items(db, cart.id)
        commit(db)
    except Exception:
        db.rollback()
        raise

    invalidate_catalog_cache()
    return order_repository.get_by_id(db, order.id) or order


def get_my_orders(
    db: Session, user_id: int, skip: int = 0, limit: int = 20
) -> list[Order]:
    return order_repository.list_for_user(db, user_id, skip, limit)


def get_my_order(db: Session, user_id: int, order_id: int) -> Order | None:
    order = order_repository.get_by_id(db, order_id)
    return order if order is not None and order.user_id == user_id else None


def get_all_orders(db: Session, skip: int = 0, limit: int = 20) -> list[Order]:
    return order_repository.list_all(db, skip, limit)


def update_order_status(
    db: Session, order_id: int, new_status: OrderStatus
) -> Order | None:
    transitions = {
        OrderStatus.PENDING: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
        OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
        OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
        OrderStatus.DELIVERED: set(),
        OrderStatus.CANCELLED: set(),
    }
    try:
        order = order_repository.get_by_id(db, order_id, lock=True)
        if order is None:
            return None
        if new_status == order.status:
            return order
        if new_status not in transitions[order.status]:
            raise OrderOperationError(
                f"Cannot change order status from '{order.status.value}' "
                f"to '{new_status.value}'",
                409,
            )
        if new_status == OrderStatus.CANCELLED:
            for item in order.items:
                if item.product_id is not None:
                    order_repository.restore_stock(
                        db, item.product_id, item.quantity
                    )
        order.status = new_status
        commit(db)
    except Exception:
        db.rollback()
        raise

    if new_status == OrderStatus.CANCELLED:
        invalidate_catalog_cache()
    return order_repository.get_by_id(db, order_id)
