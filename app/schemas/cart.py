from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=10000)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0, le=10000)


class CartProductRead(BaseModel):
    id: int
    name: str
    price: Decimal
    stock: int

    model_config = ConfigDict(from_attributes=True)


class CartItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: CartProductRead

    model_config = ConfigDict(from_attributes=True)


class CartRead(BaseModel):
    id: int
    items: list[CartItemRead]

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def total_amount(self) -> Decimal:
        return sum(
            (item.product.price * item.quantity for item in self.items),
            start=Decimal("0.00"),
        )
