"""Phase 2: reminders and winback fields.

Revision ID: 0003_phase2_reminders_winback
Revises: 0002_fix_interaction_api_key_schema
Create Date: 2026-08-11 15:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_phase2_reminders_winback"
down_revision: Union[str, None] = "0002_fix_interaction_api_key_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("reminded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "clients",
        sa.Column("last_winback_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clients", "last_winback_at")
    op.drop_column("bookings", "reminded_at")
