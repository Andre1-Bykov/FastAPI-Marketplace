from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud.order import (
    OrderOperationError,
    create_order_from_cart,
    get_all_orders,
    get_my_order,
    get_my_orders,
    update_order_status,
)
from app.dependencies.auth import get_current_active_user, require_admin
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.order import OrderRead, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderRead, status_code=201)
def create_order_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return create_order_from_cart(db, current_user.id)
    except OrderOperationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/", response_model=list[OrderRead])
def get_my_orders_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_my_orders(db, current_user.id, skip, limit)


@router.get("/admin", response_model=list[OrderRead])
def get_all_orders_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return get_all_orders(db, skip, limit)


@router.patch("/admin/{order_id}/status", response_model=OrderRead)
def update_order_status_route(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        order = update_order_status(db, order_id, payload.status)
    except OrderOperationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/{order_id}", response_model=OrderRead)
def get_my_order_route(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    order = get_my_order(db, current_user.id, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
