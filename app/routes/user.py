from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud.user import authenticate_user, create_user, get_users, get_user_by_id, update_user, delete_user
from app.dependencies.database import get_db
from app.schemas.user import UserCreate, UserRead, UserUpdate
router = APIRouter(
    prefix='/users',
    tags=['Users'],
)

@router.post('/', response_model=UserRead)
def create_user_route(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    return create_user(db, user)

@router.get("/", response_model=list[UserRead])
def get_users_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("id", pattern="^(id|username|email)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    return get_users(
        db,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order
    )

@router.get('/{user_id}', response_model=UserRead)
def get_user_by_id_route(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put('/{user_id}', response_model=UserRead)
def update_user_route(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    updated_user = update_user(db, user_id, user_update)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete('/{user_id}', response_model=UserRead)
def delete_user_route(
    user_id: int,
    db: Session = Depends(get_db)
):
    deleted_user = delete_user(db, user_id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user

@router.post('/{user_id}/verify-password')
def verify_user_password_route( 
    user_id: int,
    password: str,
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_valid = authenticate_user(user, password)
    return {"is_valid": is_valid}