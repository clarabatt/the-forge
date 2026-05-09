"""remove intermediate pipeline statuses

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-09

PENDING_APPROVAL, TAILORING, VALIDATING, and PENDING_RETRY are removed from
the pipeline. The analysis run now transitions directly to READY. Any existing
rows with those statuses are moved to READY.
"""
from typing import Union

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels = None
depends_on = None

_REMOVED = ("PENDING_APPROVAL", "TAILORING", "VALIDATING", "PENDING_RETRY")


def upgrade() -> None:
    removed = ", ".join(f"'{s}'" for s in _REMOVED)
    op.execute(
        f"UPDATE applications SET status = 'READY' WHERE status IN ({removed})"
    )


def downgrade() -> None:
    pass
