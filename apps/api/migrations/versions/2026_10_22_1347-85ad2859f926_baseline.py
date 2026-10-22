"""baseline

Revision ID: 85ad2859f926
Revises:
Create Date: 2026-10-22 13:47:31.465906

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "85ad2859f926"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
