from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.core.cache import invalidate_catalog_cache
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product


class OrderOperationError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _order_options():
    return selectinload(Order.items)


def create_order_from_cart(db: Session, user_id: int) -> Order:
    try:
        cart = db.scalar(
            select(Cart)
            .where(Cart.user_id == user_id)
            .with_for_update()
            .options(selectinload(Cart.items).joinedload(CartItem.product))
        )
        if cart is None or not cart.items:
            raise OrderOperationError("Cart is empty", 400)

        cart_items = sorted(cart.items, key=lambda item: item.product_id)
        if any(item.product is None for item in cart_items):
            raise OrderOperationError("A product in the cart is no longer available", 409)

        total = sum(
            (item.product.price * item.quantity for item in cart_items),
            start=Decimal("0.00"),
        )
        order = Order(
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
        )
        db.add(order)
        db.flush()

        for item in cart_items:
            stock_update = db.execute(
                update(Product)
                .where(Product.id == item.product_id, Product.stock >= item.quantity)
                .values(stock=Product.stock - item.quantity)
                .execution_options(synchronize_session=False)
            )
            if stock_update.rowcount != 1:
                raise OrderOperationError(
                    f"Insufficient stock for product '{item.product.name}'",
                    409,
                )

        cart.items.clear()
        db.commit()
        invalidate_catalog_cache()
    except Exception:
        db.rollback()
        raise

    return db.scalar(
        select(Order).where(Order.id == order.id).options(_order_options())
    ) or order


def get_my_orders(
    db: Session, user_id: int, skip: int = 0, limit: int = 20
) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .where(Order.user_id == user_id)
            .options(_order_options())
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


def get_my_order(db: Session, user_id: int, order_id: int) -> Order | None:
    return db.scalar(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user_id)
        .options(_order_options())
    )


def get_all_orders(db: Session, skip: int = 0, limit: int = 20) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .options(_order_options())
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


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
        order = db.scalar(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
            .options(_order_options())
        )
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
                    db.execute(
                        update(Product)
                        .where(Product.id == item.product_id)
                        .values(stock=Product.stock + item.quantity)
                        .execution_options(synchronize_session=False)
                    )
        order.status = new_status
        db.commit()
        if new_status == OrderStatus.CANCELLED:
            invalidate_catalog_cache()
    except Exception:
        db.rollback()
        raise
    return db.scalar(
        select(Order).where(Order.id == order_id).options(_order_options())
    )
