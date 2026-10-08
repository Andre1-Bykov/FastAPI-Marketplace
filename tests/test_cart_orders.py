from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.database.base import Base
from app.dependencies.database import get_db
from app.main import app
from app.models.category import Category
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User


@pytest.fixture
def marketplace():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(bind=engine) as db:
            yield db

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    with Session(bind=engine) as db:
        user = User(
            username="buyer",
            email="buyer@example.com",
            hashed_password=hash_password("password123"),
            is_active=True,
            is_admin=False,
        )
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password("password123"),
            is_active=True,
            is_admin=True,
        )
        category = Category(name="Tools", description="Tool category")
        db.add_all([user, admin, category])
        db.flush()
        product = Product(
            name="Hammer",
            description="A hammer",
            price=Decimal("12.50"),
            stock=5,
            category_id=category.id,
        )
        db.add(product)
        db.commit()
        user_id = user.id
        admin_id = admin.id
        product_id = product.id

    client = TestClient(app)
    headers = {
        "buyer": {
            "Authorization": f"Bearer {create_access_token(str(user_id))}"
        },
        "admin": {
            "Authorization": f"Bearer {create_access_token(str(admin_id))}"
        },
    }
    yield client, headers, engine, product_id
    client.close()
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_cart_add_update_remove_and_clear(marketplace):
    client, headers, _, product_id = marketplace
    buyer = headers["buyer"]

    added = client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 2},
        headers=buyer,
    )
    assert added.status_code == 201
    cart = added.json()
    assert cart["items"][0]["quantity"] == 2
    assert cart["total_amount"] == "25.00"

    item_id = cart["items"][0]["id"]
    updated = client.patch(
        f"/cart/items/{item_id}",
        json={"quantity": 3},
        headers=buyer,
    )
    assert updated.status_code == 200
    assert updated.json()["items"][0]["quantity"] == 3

    removed = client.delete(f"/cart/items/{item_id}", headers=buyer)
    assert removed.status_code == 204
    assert client.get("/cart/", headers=buyer).json()["items"] == []

    client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 1},
        headers=buyer,
    )
    cleared = client.delete("/cart/", headers=buyer)
    assert cleared.status_code == 200
    assert cleared.json()["items"] == []


def test_checkout_decrements_stock_clears_cart_and_lists_order(marketplace):
    client, headers, engine, product_id = marketplace
    buyer = headers["buyer"]
    client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 2},
        headers=buyer,
    )

    response = client.post("/orders/", headers=buyer)
    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "pending"
    assert order["total_amount"] == "25.00"
    assert order["items"][0]["product_name"] == "Hammer"
    assert order["items"][0]["subtotal"] == "25.00"
    assert client.get("/cart/", headers=buyer).json()["items"] == []
    assert [item["id"] for item in client.get("/orders/", headers=buyer).json()] == [
        order["id"]
    ]
    with Session(bind=engine) as db:
        assert db.get(Product, product_id).stock == 3


def test_failed_checkout_preserves_cart_stock_and_creates_no_order(marketplace):
    client, headers, engine, product_id = marketplace
    buyer = headers["buyer"]
    client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 5},
        headers=buyer,
    )
    with Session(bind=engine) as db:
        db.query(Product).filter(Product.id == product_id).update({"stock": 2})
        db.commit()

    response = client.post("/orders/", headers=buyer)
    assert response.status_code == 409
    assert "Insufficient stock" in response.json()["detail"]
    assert len(client.get("/cart/", headers=buyer).json()["items"]) == 1
    with Session(bind=engine) as db:
        assert db.get(Product, product_id).stock == 2
        assert db.scalar(select(Order)) is None


def test_orders_are_private_and_admin_can_update_status(marketplace):
    client, headers, _, product_id = marketplace
    buyer = headers["buyer"]
    admin = headers["admin"]
    client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 1},
        headers=buyer,
    )
    order_response = client.post("/orders/", headers=buyer)
    order_id = order_response.json()["id"]

    assert client.get("/orders/admin", headers=buyer).status_code == 403
    assert client.get(f"/orders/{order_id}", headers=admin).status_code == 404
    assert client.get("/orders/admin", headers=admin).status_code == 200

    updated = client.patch(
        f"/orders/admin/{order_id}/status",
        json={"status": "processing"},
        headers=admin,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "processing"

    invalid_transition = client.patch(
        f"/orders/admin/{order_id}/status",
        json={"status": "delivered"},
        headers=admin,
    )
    assert invalid_transition.status_code == 409
    current = client.get(f"/orders/{order_id}", headers=buyer)
    assert current.json()["status"] == "processing"


def test_invalid_cart_quantities_and_empty_checkout_are_rejected(marketplace):
    client, headers, _, product_id = marketplace
    buyer = headers["buyer"]
    assert (
        client.post(
            "/cart/items",
            json={"product_id": product_id, "quantity": 0},
            headers=buyer,
        ).status_code
        == 422
    )
    assert client.post("/orders/", headers=buyer).status_code == 400


def test_cancelling_an_unshipped_order_restores_stock_once(marketplace):
    client, headers, engine, product_id = marketplace
    buyer = headers["buyer"]
    admin = headers["admin"]
    client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": 2},
        headers=buyer,
    )
    order_id = client.post("/orders/", headers=buyer).json()["id"]
    cancelled = client.patch(
        f"/orders/admin/{order_id}/status",
        json={"status": "cancelled"},
        headers=admin,
    )
    assert cancelled.status_code == 200

    repeated_cancel = client.patch(
        f"/orders/admin/{order_id}/status",
        json={"status": "cancelled"},
        headers=admin,
    )
    assert repeated_cancel.status_code == 200
    with Session(bind=engine) as db:
        assert db.get(Product, product_id).stock == 5


def test_openapi_lists_cart_and_order_endpoints(marketplace):
    client, _, _, _ = marketplace
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/cart/items" in paths
    assert "/orders/" in paths
    assert "/orders/admin/{order_id}/status" in paths
