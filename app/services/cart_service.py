from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.repositories import cart_repository
from app.schemas.cart import CartItemCreate, CartItemUpdate
from app.services._transactions import commit


class CartOperationError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = cart_repository.get_for_user(db, user_id)
    if cart is None:
        cart = cart_repository.add_cart(db, Cart(user_id=user_id))
    return cart


def get_my_cart(db: Session, user_id: int) -> Cart:
    cart = _get_or_create_cart(db, user_id)
    commit(db)
    return cart_repository.get_for_user(db, user_id) or cart


def add_to_cart(db: Session, user_id: int, payload: CartItemCreate) -> Cart:
    try:
        product = cart_repository.get_product(db, payload.product_id)
        if product is None:
            raise CartOperationError("Product not found", 404)
        cart = _get_or_create_cart(db, user_id)
        item = cart_repository.get_item_for_product(db, cart.id, product.id)
        quantity = payload.quantity + (item.quantity if item is not None else 0)
        if quantity > product.stock:
            raise CartOperationError("Requested quantity exceeds available stock", 409)
        if item is None:
            cart_repository.add_item(
                db,
                CartItem(
                    cart_id=cart.id,
                    product_id=product.id,
                    quantity=quantity,
                ),
            )
        else:
            item.quantity = quantity
        commit(db)
    except Exception:
        db.rollback()
        raise
    return cart_repository.get_for_user(db, user_id) or _get_or_create_cart(db, user_id)


def update_cart_item(
    db: Session, user_id: int, item_id: int, payload: CartItemUpdate
) -> Cart | None:
    try:
        cart = cart_repository.get_for_user(db, user_id)
        if cart is None:
            return None
        item = cart_repository.get_item_for_cart(db, cart.id, item_id)
        if item is None:
            return None
        product = cart_repository.get_product(db, item.product_id)
        if product is None:
            raise CartOperationError("Product is no longer available", 409)
        if payload.quantity > product.stock:
            raise CartOperationError("Requested quantity exceeds available stock", 409)
        item.quantity = payload.quantity
        commit(db)
    except Exception:
        db.rollback()
        raise
    return cart_repository.get_for_user(db, user_id)


def remove_cart_item(db: Session, user_id: int, item_id: int) -> bool:
    cart = cart_repository.get_for_user(db, user_id)
    if cart is None:
        return False
    item = cart_repository.get_item_for_cart(db, cart.id, item_id)
    if item is None:
        return False
    cart_repository.delete_item(db, item)
    commit(db)
    return True


def clear_cart(db: Session, user_id: int) -> Cart:
    try:
        cart = _get_or_create_cart(db, user_id)
        cart_repository.clear_items(db, cart.id)
        commit(db)
    except Exception:
        db.rollback()
        raise
    return cart_repository.get_for_user(db, user_id) or cart
