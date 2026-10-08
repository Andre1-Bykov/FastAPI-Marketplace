from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated

from app.schemas.category import CategoryShort


ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class ProductCreate(BaseModel):
    name: ProductName
    description: str = Field(max_length=5000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    category_id: int = Field(gt=0)


class ProductRead(BaseModel):
    id: int
    name: str
    description: str
    price: Decimal
    stock: int
    category_id: int
    category: CategoryShort
    model_config = ConfigDict(from_attributes=True)

class ProductUpdate(BaseModel):
    name: ProductName
    description: str = Field(max_length=5000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)
    category_id: int = Field(gt=0)