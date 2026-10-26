# FastAPI Marketplace

An API marketplace built with FastAPI, SQLAlchemy, Alembic, PostgreSQL, and optional Redis catalog caching.

Application code is organized into API routes, application services (`app/services/`), and persistence repositories (`app/repositories/`). Routes handle HTTP concerns, services own business rules and transaction boundaries, and repositories encapsulate database queries and persistence operations.

## Features

- JWT authentication and admin-protected catalog/user operations.
- Product/category CRUD, validated product filters, and eager-loaded catalog queries.
- A private cart per authenticated user with add, view, quantity update, item removal, and clear operations.
- Checkout creates an order and immutable price/name snapshots of its items.
- Checkout checks and decreases stock in the same database transaction that creates the order and clears the cart. A conditional stock update prevents overselling under concurrent checkouts.
- Customers can only read their own orders. Admins can list all orders and change status.
- Order statuses: `pending` -> `processing` -> `shipped` -> `delivered`; pending and processing orders can instead be cancelled. Delivered/cancelled orders are terminal. Cancelling a pending/processing order restores its stock in the same transaction.
- SQL constraints and indexes for cart ownership, unique cart products, positive quantities, inventory, and common order/catalog lookups.
- Redis-backed, 60-second product catalog cache; product and category writes bump the cache generation. Redis is optional outside Docker.
- Request ID response headers and request/error logging, configurable CORS, and a health endpoint.
- FastAPI OpenAPI UI at `/docs`, ReDoc at `/redoc`, and schema JSON at `/openapi.json`.

## Local setup

Use Python 3.10+ and PostgreSQL. Copy `.env.example` to `.env`, replace all sample passwords/secrets with strong values, and set `DATABASE_URL` to your PostgreSQL URL. Do not commit `.env`.

Install runtime and development dependencies:

```powershell
pip install -r requirements-dev.txt -r requirements-redis.txt
```

Apply migrations and run the API:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

Set `REDIS_URL` to enable catalog caching. If Redis is configured but unavailable, requests that use the cache and `/health` return an error instead of silently bypassing the configured dependency.

## Docker Compose

Copy `.env.example` to `.env` and set a strong `SECRET_KEY` and `POSTGRES_PASSWORD`. The Compose file starts PostgreSQL, Redis, and the API; the API container applies Alembic migrations before starting Uvicorn.

```powershell
docker compose up --build
```

Open <http://localhost:8000/docs>. PostgreSQL and Redis use named persistent volumes. To stop the services without deleting their data:

```powershell
docker compose down
```

The Compose setup is a deployment baseline, not a complete production platform. Production deployments should additionally configure TLS/reverse proxy, restricted CORS origins, secret management, backups/restore drills, resource limits, monitoring, and a controlled migration job.

## API

All cart/order endpoints require `Authorization: Bearer <access_token>`.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/users/` | Register |
| `POST` | `/users/login` | Obtain a token (JSON or OAuth2 form) |
| `POST` | `/cart/items` | Add a product: `{"product_id": 1, "quantity": 2}` |
| `GET` | `/cart/` | Read the current user's cart |
| `PATCH` | `/cart/items/{item_id}` | Change quantity: `{"quantity": 3}` |
| `DELETE` | `/cart/items/{item_id}` | Remove a cart item |
| `DELETE` | `/cart/` | Clear the cart |
| `POST` | `/orders/` | Checkout the current user's cart |
| `GET` | `/orders/` | List the current user's orders (`skip`, `limit`) |
| `GET` | `/orders/{order_id}` | Get one of the current user's orders |
| `GET` | `/orders/admin` | Admin: list all orders |
| `PATCH` | `/orders/admin/{order_id}/status` | Admin: change status, e.g. `{"status":"processing"}` |
| `GET` | `/health` | Liveness/readiness check (also checks configured Redis) |

Cart quantities must be positive and within available stock at the time the cart is changed. Inventory is not reserved until checkout; checkout rechecks stock atomically. A failed checkout leaves both the stock and cart unchanged.

Database tables are normalized around users, products, categories, carts/cart items, orders/order items. `order_items` stores product name and unit-price snapshots so historical orders retain their purchase details if catalog data changes; the optional product foreign key is set to null when a product is deleted.

## Tests

Install `requirements-dev.txt` and run:

```powershell
pytest -q
```

The cart/order API tests use isolated in-memory SQLite and cover ownership, validation, totals, stock failures, transaction behavior, checkout, and admin status transitions.

## Postman

Import [`postman/FastAPI-Marketplace.postman_collection.json`](./postman/FastAPI-Marketplace.postman_collection.json). Set `baseUrl`; register/login and copy the returned token into `token` or `adminToken`. Set `productId` to an existing product and run the cart/checkout requests.
