from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database.base import Base
from app.dependencies.database import get_db
from app.main import app
from app.models.user import User


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)


def override_get_db():
    with Session(bind=engine) as db:
        yield db


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def seed_users():
    with Session(bind=engine) as db:
        db.query(User).delete()
        db.add_all(
            [
                User(
                    username="user",
                    email="user@example.com",
                    hashed_password=hash_password("password"),
                    is_active=True,
                    is_admin=False,
                ),
                User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=hash_password("password"),
                    is_active=True,
                    is_admin=True,
                ),
            ]
        )
        db.commit()


def login(email: str) -> str:
    response = client.post(
        "/users/login",
        json={"email": email, "password": "password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_current_user_requires_authentication_and_returns_user():
    seed_users()

    unauthorized = client.get("/users/me")
    assert unauthorized.status_code == 401

    token = login("user@example.com")
    authorized = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert authorized.status_code == 200
    assert authorized.json()["email"] == "user@example.com"


def test_admin_permission_protects_user_list():
    seed_users()

    user_token = login("user@example.com")
    user_response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert user_response.status_code == 403

    admin_token = login("admin@example.com")
    admin_response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_response.status_code == 200
    assert len(admin_response.json()) == 2


def test_login_accepts_oauth2_form_payload():
    seed_users()

    response = client.post(
        "/users/login",
        data={"username": "user@example.com", "password": "password"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
