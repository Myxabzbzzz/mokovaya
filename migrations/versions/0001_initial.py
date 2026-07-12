"""Initial schema — users, queue, matches

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )

    queue_role_enum = sa.Enum("interviewer", "candidate", name="queuerole")
    queue_status_enum = sa.Enum("waiting", "matched", "cancelled", name="queuestatus")

    op.create_table(
        "queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", queue_role_enum, nullable=False),
        sa.Column(
            "status", queue_status_enum, nullable=False, server_default="waiting"
        ),
        sa.Column(
            "joined_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "interviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "candidate_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "matched_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("matches")
    op.drop_table("queue")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS queuestatus")
    op.execute("DROP TYPE IF EXISTS queuerole")
