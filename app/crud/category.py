from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def create_category(db: Session, category: CategoryCreate) -> Category:
    db_category = Category(
        name=category.name,
        description=category.description,
    )

    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category
def get_categories(db: Session) -> list[Category]:
    return db.query(Category).all()

def get_category(db: Session, category_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()

def update_category(
    db: Session,
    category_id: int,
    category_data: CategoryUpdate,
) -> Category | None:
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if category is None:
        return None

    category.name = category_data.name
    category.description = category_data.description

    db.commit()
    db.refresh(category)

    return category

def delete_category(db: Session, category_id: int) -> Category | None:
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if category is None:
        return None

    db.delete(category)
    db.commit()

    return category