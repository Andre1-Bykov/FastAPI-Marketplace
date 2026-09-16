from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.category import create_category, get_categories, get_category, update_category, delete_category
from app.dependencies.auth import require_admin
from app.dependencies.database import get_db
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.post("/", response_model=CategoryRead)
def create_category_route(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    return create_category(db, category)

@router.get("/", response_model=list[CategoryRead])
def get_categories_route(
    db: Session = Depends(get_db),
        ):
    return get_categories(db)

@router.get("/{category_id}", response_model=CategoryRead)
def get_category_route(
    category_id: int,
    db: Session = Depends(get_db),
):
    category = get_category(db, category_id)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    return category

@router.put("/{category_id}", response_model=CategoryRead)
def update_category_route(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    category = update_category(db, category_id, category_data)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    return category

@router.delete("/{category_id}", response_model=CategoryRead)
def delete_category_route(
    category_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    category = delete_category(db, category_id)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    return category