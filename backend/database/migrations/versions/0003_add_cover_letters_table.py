"""add_cover_letters_table

Revision ID: 0003
Revises: ba3517855f92
Create Date: 2026-05-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "ba3517855f92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cover_letters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("content", sqlmodel.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cover_letters_application_id", "cover_letters", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_cover_letters_application_id", table_name="cover_letters")
    op.drop_table("cover_letters")
