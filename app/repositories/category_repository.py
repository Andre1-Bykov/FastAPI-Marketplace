from sqlalchemy.orm import Session

from app.models.category import Category


def add(db: Session, category: Category) -> Category:
    db.add(category)
    return category


def list_all(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.id).all()


def get_by_id(db: Session, category_id: int) -> Category | None:
    return db.get(Category, category_id)


def delete(db: Session, category: Category) -> None:
    db.delete(category)
