"""store model prices per million tokens

Revision ID: 7b2d4c6e8f10
Revises: 2d31a8c7f4e2
Create Date: 2026-07-20 19:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b2d4c6e8f10"
down_revision: Union[str, Sequence[str], None] = "2d31a8c7f4e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text(
        "UPDATE models SET "
        "input_price = input_price * 1000, "
        "output_price = output_price * 1000"
    ))
    op.alter_column(
        "models",
        "input_price",
        existing_type=sa.Numeric(precision=18, scale=8),
        existing_nullable=False,
        comment="每百万 Token 输入价格",
    )
    op.alter_column(
        "models",
        "output_price",
        existing_type=sa.Numeric(precision=18, scale=8),
        existing_nullable=False,
        comment="每百万 Token 输出价格",
    )


def downgrade() -> None:
    op.execute(sa.text(
        "UPDATE models SET "
        "input_price = input_price / 1000, "
        "output_price = output_price / 1000"
    ))
    op.alter_column(
        "models",
        "input_price",
        existing_type=sa.Numeric(precision=18, scale=8),
        existing_nullable=False,
        comment="输入价格",
    )
    op.alter_column(
        "models",
        "output_price",
        existing_type=sa.Numeric(precision=18, scale=8),
        existing_nullable=False,
        comment="输出价格",
    )
