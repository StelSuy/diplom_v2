"""add is_active to terminals

Revision ID: 003_add_terminal_is_active
Revises: e511f0b8ab3c
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = '003_add_terminal_is_active'
down_revision = 'e511f0b8ab3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active column with default True (all existing terminals stay active)
    op.add_column(
        'terminals',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1')
    )


def downgrade() -> None:
    op.drop_column('terminals', 'is_active')
