from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order
from app.models.product import Product


def add(db: Session, order: Order) -> Order:
    db.add(order)
    db.flush()
    return order


def get_by_id(db: Session, order_id: int, *, lock: bool = False) -> Order | None:
    query = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    if lock:
        query = query.with_for_update()
    return db.scalar(query)


def list_for_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 20
) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


def list_all(db: Session, skip: int = 0, limit: int = 20) -> list[Order]:
    return list(
        db.scalars(
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


def decrement_stock_if_available(
    db: Session, product_id: int, quantity: int
) -> bool:
    result = db.execute(
        update(Product)
        .where(Product.id == product_id, Product.stock >= quantity)
        .values(stock=Product.stock - quantity)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount == 1


def restore_stock(db: Session, product_id: int, quantity: int) -> None:
    db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(stock=Product.stock + quantity)
        .execution_options(synchronize_session=False)
    )
