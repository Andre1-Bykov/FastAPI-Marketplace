from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.category import Category
from app.models.product import Product
from app.crud.product import get_products


def test_get_products_sort_by_price_asc():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(bind=engine) as db:
        category = Category(name="Tools", description="Tool category")
        db.add(category)
        db.commit()
        db.refresh(category)

        db.add_all(
            [
                Product(name="A", description="", price=20, stock=1, category_id=category.id),
                Product(name="B", description="", price=10, stock=1, category_id=category.id),
                Product(name="C", description="", price=30, stock=1, category_id=category.id),
            ]
        )
        db.commit()

        products = get_products(db, sort_by="price", order="asc")
        assert [p.name for p in products] == ["B", "A", "C"]


def test_get_products_sort_by_price_desc():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    with Session(bind=engine) as db:
        category = Category(name="Tools", description="Tool category")
        db.add(category)
        db.commit()
        db.refresh(category)

        db.add_all(
            [
                Product(name="A", description="", price=20, stock=1, category_id=category.id),
                Product(name="B", description="", price=10, stock=1, category_id=category.id),
                Product(name="C", description="", price=30, stock=1, category_id=category.id),
            ]
        )
        db.commit()

        products = get_products(db, sort_by="price", order="desc")
        assert [p.name for p in products] == ["C", "A", "B"]
