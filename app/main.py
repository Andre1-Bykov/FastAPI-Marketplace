from fastapi import FastAPI

from app.models import Category, Product, User
from app.routes.category import router as category_router
from app.routes.product import router as product_router


app = FastAPI()

app.include_router(category_router)
app.include_router(product_router)