"""add manual events fields

Revision ID: e511f0b8ab3c
Revises: 001
Create Date: 2026-01-24 20:33:56.600183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e511f0b8ab3c'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column('events', sa.Column('is_manual', sa.Boolean(), default=False))
    op.add_column('events', sa.Column('created_by_user_id', sa.Integer(), nullable=True))
    op.add_column('events', sa.Column('comment', sa.String(500), nullable=True))
    op.add_column('events', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_events_created_by_user', 'events', 'users', ['created_by_user_id'], ['id'])

def downgrade() -> None:
    pass


