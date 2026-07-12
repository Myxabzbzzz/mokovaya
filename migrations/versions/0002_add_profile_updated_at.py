"""Add users.profile_updated_at

Revision ID: 0002_add_profile_updated_at
Revises: 0001_initial
Create Date: 2026-07-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_profile_updated_at"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("profile_updated_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "profile_updated_at")
