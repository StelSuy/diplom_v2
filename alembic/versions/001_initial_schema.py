"""Complete initial schema — all tables in final state

Revision ID: 001
Revises:
Create Date: 2026-04-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── terminals ─────────────────────────────────────────────────────────────
    op.create_table(
        'terminals',
        sa.Column('id',           sa.Integer(),      nullable=False),
        sa.Column('name',         sa.String(64),     nullable=False),
        sa.Column('api_key',      sa.String(128),    nullable=False),
        sa.Column('is_active',    sa.Boolean(),      nullable=False, server_default='1'),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_terminals_id',      'terminals', ['id'],      unique=False)
    op.create_index('ix_terminals_name',    'terminals', ['name'],    unique=True)
    op.create_index('ix_terminals_api_key', 'terminals', ['api_key'], unique=True)

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id',            sa.Integer(),   nullable=False),
        sa.Column('username',      sa.String(64),  nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role',          sa.String(20),  nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_id',       'users', ['id'],       unique=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # ── employees ─────────────────────────────────────────────────────────────
    op.create_table(
        'employees',
        sa.Column('id',              sa.Integer(),     nullable=False),
        sa.Column('full_name',       sa.String(128),   nullable=False),
        sa.Column('nfc_uid',         sa.String(64),    nullable=False),
        sa.Column('public_key_b64',  sa.String(2048),  nullable=True),
        sa.Column('is_active',       sa.Boolean(),     nullable=False, server_default='1'),
        sa.Column('position',        sa.String(64),    nullable=True),
        sa.Column('comment',         sa.String(255),   nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_employees_id',        'employees', ['id'],        unique=False)
    op.create_index('ix_employees_full_name', 'employees', ['full_name'], unique=False)
    op.create_index('ix_employees_nfc_uid',   'employees', ['nfc_uid'],   unique=True)

    # ── events ────────────────────────────────────────────────────────────────
    op.create_table(
        'events',
        sa.Column('id',                  sa.Integer(),  nullable=False),
        sa.Column('employee_id',         sa.Integer(),  nullable=False),
        sa.Column('terminal_id',         sa.Integer(),  nullable=True),   # nullable — ручні події
        sa.Column('direction',           sa.String(8),  nullable=False),
        sa.Column('ts',                  sa.DateTime(), nullable=False),
        sa.Column('is_manual',           sa.Boolean(),  nullable=True,  server_default='0'),
        sa.Column('created_by_user_id',  sa.Integer(),  nullable=True),
        sa.Column('comment',             sa.String(500), nullable=True),
        sa.Column('created_at',          sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'],        ['employees.id']),
        sa.ForeignKeyConstraint(['terminal_id'],        ['terminals.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'],
                                name='fk_events_created_by_user'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_events_id',          'events', ['id'],          unique=False)
    op.create_index('ix_events_employee_id', 'events', ['employee_id'], unique=False)
    op.create_index('ix_events_terminal_id', 'events', ['terminal_id'], unique=False)
    op.create_index('ix_events_direction',   'events', ['direction'],   unique=False)
    op.create_index('ix_events_ts',          'events', ['ts'],          unique=False)

    # ── schedules ─────────────────────────────────────────────────────────────
    op.create_table(
        'schedules',
        sa.Column('id',          sa.Integer(),  nullable=False),
        sa.Column('employee_id', sa.Integer(),  nullable=False),
        sa.Column('day',         sa.Date(),     nullable=False),
        sa.Column('start_hhmm',  sa.String(5),  nullable=False),
        sa.Column('end_hhmm',    sa.String(5),  nullable=False),
        sa.Column('code',        sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'day', name='uq_schedule_employee_day'),
    )
    op.create_index('ix_schedules_id',  'schedules', ['id'],  unique=False)
    op.create_index('ix_schedules_day', 'schedules', ['day'], unique=False)

    # ── positions ─────────────────────────────────────────────────────────────
    op.create_table(
        'positions',
        sa.Column('id',        sa.Integer(),   nullable=False),
        sa.Column('name',      sa.String(128), nullable=False),
        sa.Column('is_active', sa.Boolean(),   nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_positions_id',   'positions', ['id'],   unique=False)
    op.create_index('ix_positions_name', 'positions', ['name'], unique=True)

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id',             sa.Integer(),  nullable=False),
        sa.Column('admin_id',       sa.Integer(),  nullable=True),
        sa.Column('admin_username', sa.String(64), nullable=False),
        sa.Column('action',         sa.String(64), nullable=False),
        sa.Column('entity_type',    sa.String(64), nullable=True),
        sa.Column('entity_id',      sa.Integer(),  nullable=True),
        sa.Column('details',        sa.Text(),     nullable=True),
        sa.Column('created_at',     sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_id',             'audit_logs', ['id'],             unique=False)
    op.create_index('ix_audit_logs_admin_id',       'audit_logs', ['admin_id'],       unique=False)
    op.create_index('ix_audit_logs_admin_username', 'audit_logs', ['admin_username'], unique=False)
    op.create_index('ix_audit_logs_action',         'audit_logs', ['action'],         unique=False)
    op.create_index('ix_audit_logs_entity_type',    'audit_logs', ['entity_type'],    unique=False)
    op.create_index('ix_audit_logs_created_at',     'audit_logs', ['created_at'],     unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('positions')
    op.drop_table('schedules')
    op.drop_table('events')
    op.drop_table('employees')
    op.drop_table('users')
    op.drop_table('terminals')
