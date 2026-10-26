from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.user import User


def add(db: Session, user: User) -> User:
    db.add(user)
    return user


def list_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "id",
    order: str = "asc",
) -> list[User]:
    query = db.query(User)
    sort_column = {
        "id": User.id,
        "username": User.username,
        "email": User.email,
    }.get(sort_by, User.id)
    query = query.order_by(
        sort_column.desc() if order == "desc" else sort_column.asc()
    )
    return query.offset(skip).limit(limit).all()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_by_login(db: Session, login: str) -> User | None:
    return (
        db.query(User)
        .filter(or_(User.email == login, User.username == login))
        .first()
    )


def delete(db: Session, user: User) -> None:
    db.delete(user)
