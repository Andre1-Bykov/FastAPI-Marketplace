from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserUpdate
from app.services._transactions import commit


def create_user(db: Session, user: UserCreate) -> User:
    result = user_repository.add(
        db,
        User(
            username=user.username,
            email=user.email,
            hashed_password=hash_password(user.password),
        ),
    )
    commit(db)
    db.refresh(result)
    return result


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "id",
    order: str = "asc",
) -> list[User]:
    return user_repository.list_users(db, skip, limit, sort_by, order)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return user_repository.get_by_id(db, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return user_repository.get_by_email(db, email)


def update_user(
    db: Session, user_id: int, user_update: UserUpdate
) -> User | None:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        return None
    if user_update.username is not None:
        user.username = user_update.username
    user.email = user_update.email
    user.hashed_password = hash_password(user_update.password)
    commit(db)
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> User | None:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        return None
    user_repository.delete(db, user)
    commit(db)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = user_repository.get_by_login(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
