from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserRead

def create_user(
        db: Session,
        user: UserCreate
) -> User:
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "id",
        order: str = "asc"
) -> list[User]:
    query = db.query(User)
    sort_column = {
            "id": User.id,
            "username": User.username,
            "email": User.email
        }.get(sort_by, User.id)
    
    if order == "desc":
            query = query.order_by(sort_column.desc())
    else:
            query = query.order_by(sort_column.asc())
    
    return query.offset(skip).limit(limit).all()

def get_user_by_id(
        db: Session,
        user_id: int
) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def update_user(
        db: Session,
        user_id: int,
        user_update: UserCreate
) -> User | None:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        return None

    db_user.username = user_update.username
    db_user.email = user_update.email
    db_user.hashed_password = hash_password(user_update.password)       

    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(
          db: Session,
          user_id: int
) -> User:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user is None:
                return None
        
        db.delete(db_user)
        db.commit()
        return db_user

def authenticate_user(
        db: Session,
        username: str,
        password: str
) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user