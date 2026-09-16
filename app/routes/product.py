from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud.product import create_product, get_products, get_product, update_product, delete_product
from app.dependencies.auth import require_admin
from app.dependencies.database import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post("/", response_model=ProductRead)
def create_product_route(
    product: ProductCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    return create_product(db, product)

@router.get("/", response_model=list[ProductRead])
def get_products_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    name_of_product: str | None = None,
    sort_by: str = Query("id", pattern="^(id|name|price|stock|category_id)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    return get_products(
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

@router.get("/{product_id}", response_model=ProductRead)
def get_product_route(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = get_product(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product

@router.put("/{product_id}", response_model=ProductRead)
def update_product_route(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    product = update_product(db, product_id, product_data)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product

@router.delete("/{product_id}", response_model=ProductRead)
def delete_product_route(
    product_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    product = delete_product(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product