from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product


def get_for_user(db: Session, user_id: int, *, lock: bool = False) -> Cart | None:
    query = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).joinedload(CartItem.product))
    )
    if lock:
        query = query.with_for_update()
    return db.scalar(query)


def add_cart(db: Session, cart: Cart) -> Cart:
    db.add(cart)
    db.flush()
    return cart


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_item_for_cart(db: Session, cart_id: int, item_id: int) -> CartItem | None:
    return db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.id == item_id,
        )
    )


def get_item_for_product(db: Session, cart_id: int, product_id: int) -> CartItem | None:
    return db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
    )


def add_item(db: Session, item: CartItem) -> CartItem:
    db.add(item)
    return item


def delete_item(db: Session, item: CartItem) -> None:
    db.delete(item)


def clear_items(db: Session, cart_id: int) -> None:
    db.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
