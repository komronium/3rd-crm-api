"""rename next_month/intro_lesson lead statuses to discount/visit_day

Revision ID: d84f6b1a93e2
Revises: c7d1f4a82e09
Create Date: 2026-08-31 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d84f6b1a93e2"
down_revision: Union[str, None] = "c7d1f4a82e09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Map old statuses -> new statuses
STATUS_MAPPING = {
    "next_month": "discount",
    "intro_lesson": "visit_day",
}


def upgrade() -> None:
    for old, new in STATUS_MAPPING.items():
        op.execute(
            sa.text("UPDATE lead SET status = :new WHERE status = :old").bindparams(
                old=old, new=new
            )
        )


def downgrade() -> None:
    reverse = {v: k for k, v in STATUS_MAPPING.items()}
    for new, old in reverse.items():
        op.execute(
            sa.text("UPDATE lead SET status = :old WHERE status = :new").bindparams(
                old=old, new=new
            )
        )
