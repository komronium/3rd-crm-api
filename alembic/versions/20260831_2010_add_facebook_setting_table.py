"""add facebook_setting table for frontend-editable FB credentials

Revision ID: f2a91c7e4d3b
Revises: d84f6b1a93e2
Create Date: 2026-08-31 20:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2a91c7e4d3b"
down_revision: Union[str, None] = "d84f6b1a93e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facebook_setting",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("access_token", sa.String(length=512), nullable=True),
        sa.Column("page_id", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("facebook_setting")
