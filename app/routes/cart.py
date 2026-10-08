from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.crud.cart import (
    CartOperationError,
    add_to_cart,
    clear_cart,
    get_my_cart,
    remove_cart_item,
    update_cart_item,
)
from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/", response_model=CartRead)
def get_my_cart_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_my_cart(db, current_user.id)


@router.post("/items", response_model=CartRead, status_code=201)
def add_to_cart_route(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return add_to_cart(db, current_user.id, payload)
    except CartOperationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.patch("/items/{item_id}", response_model=CartRead)
def update_cart_item_route(
    item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        cart = update_cart_item(db, current_user.id, item_id, payload)
    except CartOperationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return cart


@router.delete("/items/{item_id}", status_code=204)
def remove_cart_item_route(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not remove_cart_item(db, current_user.id, item_id):
        raise HTTPException(status_code=404, detail="Cart item not found")
    return Response(status_code=204)


@router.delete("/", response_model=CartRead)
def clear_cart_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return clear_cart(db, current_user.id)
