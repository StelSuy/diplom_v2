"""make terminal_id nullable in events

Revision ID: 002
Revises: e511f0b8ab3c
Create Date: 2026-01-24 21:50:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = 'e511f0b8ab3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Робимо terminal_id nullable для підтримки ручних подій
    op.alter_column('events', 'terminal_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade() -> None:
    # Якщо потрібно повернути назад
    op.alter_column('events', 'terminal_id',
                    existing_type=sa.Integer(),
                    nullable=False)
