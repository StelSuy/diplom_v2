"""add last_seen_at to terminals

Revision ID: 004_add_terminal_last_seen
Revises: 003_add_terminal_is_active
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_terminal_last_seen'
down_revision = '003_add_terminal_is_active'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'terminals',
        sa.Column('last_seen_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('terminals', 'last_seen_at')
