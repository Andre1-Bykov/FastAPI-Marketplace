from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="cart",
    )

    items: Mapped[list["CartItem"]] = relationship( # type: ignore
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
    )