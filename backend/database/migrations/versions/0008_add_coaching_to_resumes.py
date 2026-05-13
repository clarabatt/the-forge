"""add coaching fields to resumes

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-12
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("coaching_status", sa.String(20), nullable=False, server_default="pending"))
    op.add_column("resumes", sa.Column("coaching_analysis", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "coaching_analysis")
    op.drop_column("resumes", "coaching_status")
