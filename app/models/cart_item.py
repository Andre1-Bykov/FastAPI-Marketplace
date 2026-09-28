from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.product import Product

class CartItem(Base):
    __tablename__ = "cart_items"

    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "product_id",
            name="uq_cart_product",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id"),
        nullable=False,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(nullable=False)

    cart = relationship(
        "Cart",
        back_populates="items",
    )

    product = relationship(
        "Product",
        back_populates="cart_items",
    )