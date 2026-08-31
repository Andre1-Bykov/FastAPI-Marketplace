from sqlalchemy.orm import Session
from app.crud.category import get_category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category_id=product.category_id,
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product

def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
            ) -> list[Product]:
    if category_id is not None:
        query = db.query(Product).filter(Product.category_id == category_id)

        if min_price is not None:
            query = query.filter(Product.price >= min_price)

        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        return (
            query
            .offset(skip)
            .limit(limit)
                .all()
            )
    elif category_id is None:
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
                query = query.filter(Product.price <= max_price)
        
        return (
                query
                .offset(skip)
                .limit(limit)
                    .all()
                )
    return (
        db.query(Product)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_product(
    db: Session,
    product_id: int,
) -> Product | None:
    return (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

def update_product(
    db: Session,
    product_id: int,
    product_data: ProductUpdate,
) -> Product | None:
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        return None

    product.name = product_data.name
    product.description = product_data.description
    product.price = product_data.price
    product.stock = product_data.stock
    product.category_id = product_data.category_id

    db.commit()
    db.refresh(product)

    return product

def delete_product(
    db: Session,
    product_id: int,
) -> Product | None:
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        return None

    db.delete(product)
    db.commit()

    return product