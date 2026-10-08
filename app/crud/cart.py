from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.schemas.cart import CartItemCreate, CartItemUpdate


class CartOperationError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _cart_query(user_id: int):
    return (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).joinedload(CartItem.product))
    )


def get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.scalar(_cart_query(user_id))
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.flush()
    return cart


def get_my_cart(db: Session, user_id: int) -> Cart:
    cart = get_or_create_cart(db, user_id)
    db.commit()
    return db.scalar(_cart_query(user_id)) or cart


def add_to_cart(db: Session, user_id: int, payload: CartItemCreate) -> Cart:
    try:
        product = db.get(Product, payload.product_id)
        if product is None:
            raise CartOperationError("Product not found", 404)
        cart = get_or_create_cart(db, user_id)
        item = db.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == product.id,
            )
        )
        new_quantity = payload.quantity + (item.quantity if item else 0)
        if new_quantity > product.stock:
            raise CartOperationError("Requested quantity exceeds available stock", 409)
        if item is None:
            db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=new_quantity))
        else:
            item.quantity = new_quantity
        db.commit()
    except Exception:
        db.rollback()
        raise
    return db.scalar(_cart_query(user_id)) or get_or_create_cart(db, user_id)


def update_cart_item(
    db: Session, user_id: int, item_id: int, payload: CartItemUpdate
) -> Cart | None:
    try:
        cart = db.scalar(select(Cart).where(Cart.user_id == user_id))
        if cart is None:
            return None
        item = db.scalar(
            select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
        )
        if item is None:
            return None
        product = db.get(Product, item.product_id)
        if product is None:
            raise CartOperationError("Product is no longer available", 409)
        if payload.quantity > product.stock:
            raise CartOperationError("Requested quantity exceeds available stock", 409)
        item.quantity = payload.quantity
        db.commit()
    except Exception:
        db.rollback()
        raise
    return db.scalar(_cart_query(user_id))


def remove_cart_item(db: Session, user_id: int, item_id: int) -> bool:
    cart = db.scalar(select(Cart).where(Cart.user_id == user_id))
    if cart is None:
        return False
    item = db.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True


def clear_cart(db: Session, user_id: int) -> Cart:
    cart = get_or_create_cart(db, user_id)
    cart.items.clear()
    db.commit()
    return db.scalar(_cart_query(user_id)) or cart