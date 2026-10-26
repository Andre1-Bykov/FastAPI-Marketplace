from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models.product import Product


def add(db: Session, product: Product) -> Product:
    db.add(product)
    return product


def list_products(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    category_id: int | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    name_of_product: str | None = None,
    sort_by: str = "id",
    order: str = "asc",
) -> list[Product]:
    query = db.query(Product).options(joinedload(Product.category))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if name_of_product is not None:
        query = query.filter(Product.name.ilike(f"%{name_of_product}%"))

    sort_column = {
        "id": Product.id,
        "name": Product.name,
        "price": Product.price,
        "stock": Product.stock,
        "category_id": Product.category_id,
    }.get(sort_by, Product.id)
    query = query.order_by(
        sort_column.desc() if order == "desc" else sort_column.asc()
    )
    return query.offset(skip).limit(limit).all()


def get_by_id(db: Session, product_id: int) -> Product | None:
    return (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.id == product_id)
        .first()
    )


def delete(db: Session, product: Product) -> None:
    db.delete(product)
