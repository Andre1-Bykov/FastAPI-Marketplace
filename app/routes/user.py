from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.crud.user import authenticate_user, create_user, get_users, get_user_by_id, update_user, delete_user
from app.dependencies.auth import get_current_active_user, get_current_admin, require_admin
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserCreate, UserRead, UserUpdate
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


@router.post('/login', response_model=Token)
async def login_route(
    request: Request,
    db: Session = Depends(get_db)
):
    form_data = await request.form() if "application/x-www-form-urlencoded" in request.headers.get("content-type", "") or "multipart/form-data" in request.headers.get("content-type", "") else None

    if form_data is not None:
        email = str(form_data.get("username") or form_data.get("email") or "")
        password = str(form_data.get("password") or "")
    else:
        try:
            body = await request.json()
        except Exception:
            body = {}
        email = str(body.get("email") or body.get("username") or "")
        password = str(body.get("password") or "")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email/username and password are required",
        )

    user = authenticate_user(db, email, password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/admin/me", response_model=UserRead)
def get_admin_me(
    current_admin: User = Depends(get_current_admin)
):
    return current_admin

@router.get('/me', response_model=UserRead)
def get_current_user_route(
    current_user: User = Depends(get_current_active_user),
):
    return current_user


@router.get("/", response_model=list[UserRead], dependencies=[Depends(require_admin)])
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

@router.get('/{user_id}', response_model=UserRead, dependencies=[Depends(require_admin)])
def get_user_by_id_route(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put('/{user_id}', response_model=UserRead, dependencies=[Depends(require_admin)])
def update_user_route(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    updated_user = update_user(db, user_id, user_update)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete('/{user_id}', response_model=UserRead, dependencies=[Depends(require_admin)])
def delete_user_route(
    user_id: int,
    db: Session = Depends(get_db)
):
    deleted_user = delete_user(db, user_id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user
