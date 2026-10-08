import logging
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies.database import get_db
from app.models import Category, Product, User, Cart, CartItem, Order, OrderItem
from app.routes.cart import router as cart_router
from app.routes.category import router as category_router
from app.routes.order import router as order_router
from app.routes.product import router as product_router
from app.routes.user import router as user_router

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("app.request")

app = FastAPI(
    title="FastAPI Marketplace",
    version="1.0.0",
    description="Marketplace API for catalog, carts, and orders.",
)


@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError):
    logger.info(
        "Database constraint rejected request",
        extra={"path": request.url.path},
    )
    return JSONResponse(
        status_code=409,
        content={"detail": "The operation conflicts with existing data"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Request failed",
            extra={"request_id": request_id, "path": request.url.path},
        )
        raise
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        },
    )
    return response


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    from app.core.cache import get_redis_client

    db.execute(text("SELECT 1"))
    redis_client = get_redis_client()
    if redis_client is not None:
        redis_client.ping()
    return {"status": "ok"}

app.include_router(category_router)
app.include_router(product_router)
app.include_router(user_router)
app.include_router(cart_router)
app.include_router(order_router)