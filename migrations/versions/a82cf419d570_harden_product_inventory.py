"""harden product inventory and add catalog index

Revision ID: a82cf419d570
Revises: 9e4b7f10c2a1
Create Date: 2026-10-08 13:10:00
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a82cf419d570"
down_revision: Union[str, Sequence[str], None] = "9e4b7f10c2a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_products_stock_nonnegative", "products", "stock >= 0"
    )
    op.create_index("ix_products_category_id", "products", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_constraint("ck_products_stock_nonnegative", "products", type_="check")
