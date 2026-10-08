from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.order import OrderStatus


class OrderItemRead(BaseModel):
    id: int
    product_id: int | None
    product_name: str
    unit_price: Decimal
    quantity: int

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


class OrderRead(BaseModel):
    id: int
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderListQuery(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
