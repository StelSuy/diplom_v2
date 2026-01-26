"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Terminals
    op.create_table(
        'terminals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('api_key', sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terminals_id'), 'terminals', ['id'], unique=False)
    op.create_index(op.f('ix_terminals_name'), 'terminals', ['name'], unique=True)
    op.create_index(op.f('ix_terminals_api_key'), 'terminals', ['api_key'], unique=True)

    # Employees
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=128), nullable=False),
        sa.Column('nfc_uid', sa.String(length=64), nullable=False),
        sa.Column('public_key_b64', sa.String(length=2048), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('position', sa.String(length=64), nullable=True),
        sa.Column('comment', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employees_id'), 'employees', ['id'], unique=False)
    op.create_index(op.f('ix_employees_full_name'), 'employees', ['full_name'], unique=False)
    op.create_index(op.f('ix_employees_nfc_uid'), 'employees', ['nfc_uid'], unique=True)

    # Events
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('terminal_id', sa.Integer(), nullable=False),
        sa.Column('direction', sa.String(length=8), nullable=False),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['terminal_id'], ['terminals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_index(op.f('ix_events_employee_id'), 'events', ['employee_id'], unique=False)
    op.create_index(op.f('ix_events_terminal_id'), 'events', ['terminal_id'], unique=False)
    op.create_index(op.f('ix_events_direction'), 'events', ['direction'], unique=False)
    op.create_index(op.f('ix_events_ts'), 'events', ['ts'], unique=False)

    # Schedules
    op.create_table(
        'schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('start_hhmm', sa.String(length=5), nullable=False),
        sa.Column('end_hhmm', sa.String(length=5), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'day', name='uq_schedule_employee_day')
    )
    op.create_index(op.f('ix_schedules_id'), 'schedules', ['id'], unique=False)
    op.create_index(op.f('ix_schedules_day'), 'schedules', ['day'], unique=False)

    # Users (if exists)
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('password_hash', sa.String(length=128), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_schedules_day'), table_name='schedules')
    op.drop_index(op.f('ix_schedules_id'), table_name='schedules')
    op.drop_table('schedules')
    
    op.drop_index(op.f('ix_events_ts'), table_name='events')
    op.drop_index(op.f('ix_events_direction'), table_name='events')
    op.drop_index(op.f('ix_events_terminal_id'), table_name='events')
    op.drop_index(op.f('ix_events_employee_id'), table_name='events')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')
    
    op.drop_index(op.f('ix_employees_nfc_uid'), table_name='employees')
    op.drop_index(op.f('ix_employees_full_name'), table_name='employees')
    op.drop_index(op.f('ix_employees_id'), table_name='employees')
    op.drop_table('employees')
    
    op.drop_index(op.f('ix_terminals_api_key'), table_name='terminals')
    op.drop_index(op.f('ix_terminals_name'), table_name='terminals')
    op.drop_index(op.f('ix_terminals_id'), table_name='terminals')
    op.drop_table('terminals')
