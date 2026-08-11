"""Schema alignment — superseded by 0001 UUID migration.

Revision ID: 0002_fix_interaction_api_key_schema
Revises: 0001
Create Date: 2026-08-10 15:53:02.000000

"""
from typing import Sequence, Union

revision: str = "0002_fix_interaction_api_key_schema"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: target schema is created in revision 0001."""
    pass


def downgrade() -> None:
    """No-op."""
    pass
