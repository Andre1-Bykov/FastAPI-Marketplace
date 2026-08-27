from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.product import create_product, get_products, get_product, update_product, delete_product
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
):
    return create_product(db, product)

@router.get("/", response_model=list[ProductRead])
def get_products_route(
    db: Session = Depends(get_db),
):
    return get_products(db)

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
):
    product = delete_product(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product