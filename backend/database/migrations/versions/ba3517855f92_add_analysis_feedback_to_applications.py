"""add_analysis_feedback_to_applications

Revision ID: ba3517855f92
Revises: 0001
Create Date: 2026-04-27 16:18:03.728774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ba3517855f92'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('applications', sa.Column('analysis_feedback', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('applications', 'analysis_feedback')
