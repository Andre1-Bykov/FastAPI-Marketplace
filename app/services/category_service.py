from sqlalchemy.orm import Session

from app.core.cache import invalidate_catalog_cache
from app.models.category import Category
from app.repositories import category_repository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services._transactions import commit


def create_category(db: Session, category: CategoryCreate) -> Category:
    result = category_repository.add(
        db,
        Category(name=category.name, description=category.description),
    )
    commit(db)
    db.refresh(result)
    invalidate_catalog_cache()
    return result


def get_categories(db: Session) -> list[Category]:
    return category_repository.list_all(db)


def get_category(db: Session, category_id: int) -> Category | None:
    return category_repository.get_by_id(db, category_id)


def update_category(
    db: Session, category_id: int, category_data: CategoryUpdate
) -> Category | None:
    category = category_repository.get_by_id(db, category_id)
    if category is None:
        return None
    category.name = category_data.name
    category.description = category_data.description
    commit(db)
    db.refresh(category)
    invalidate_catalog_cache()
    return category


def delete_category(db: Session, category_id: int) -> Category | None:
    category = category_repository.get_by_id(db, category_id)
    if category is None:
        return None
    category_repository.delete(db, category)
    commit(db)
    invalidate_catalog_cache()
    return category
