from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.cache import invalidate_catalog_cache
from app.models.product import Product
from app.repositories import product_repository
from app.schemas.product import ProductCreate, ProductUpdate
from app.services._transactions import commit


def create_product(db: Session, product: ProductCreate) -> Product:
    result = product_repository.add(
        db,
        Product(
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
            category_id=product.category_id,
        ),
    )
    commit(db)
    db.refresh(result)
    invalidate_catalog_cache()
    return result


def get_products(
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
    return product_repository.list_products(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        name_of_product=name_of_product,
        sort_by=sort_by,
        order=order,
    )


def get_product(db: Session, product_id: int) -> Product | None:
    return product_repository.get_by_id(db, product_id)


def update_product(
    db: Session, product_id: int, product_data: ProductUpdate
) -> Product | None:
    product = product_repository.get_by_id(db, product_id)
    if product is None:
        return None
    product.name = product_data.name
    product.description = product_data.description
    product.price = product_data.price
    product.stock = product_data.stock
    product.category_id = product_data.category_id
    commit(db)
    db.refresh(product)
    invalidate_catalog_cache()
    return product


def delete_product(db: Session, product_id: int) -> Product | None:
    product = product_repository.get_by_id(db, product_id)
    if product is None:
        return None
    product_repository.delete(db, product)
    commit(db)
    invalidate_catalog_cache()
    return product
