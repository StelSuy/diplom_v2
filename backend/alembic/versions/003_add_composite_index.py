"""add composite index on employee_id and ts

Revision ID: 003
Revises: 002
Create Date: 2026-01-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Створюємо складений індекс для швидких запитів
    op.create_index(
        'ix_events_employee_ts',
        'events',
        ['employee_id', 'ts'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_events_employee_ts', table_name='events')
