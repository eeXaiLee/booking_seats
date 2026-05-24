"""add outbox event

Revision ID: 6e3a9d4f2a21
Revises: 0eaffc6617c8
Create Date: 2026-03-26 06:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e3a9d4f2a21'
down_revision: Union[str, None] = '0eaffc6617c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'outbox_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('event_version', sa.Integer(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('aggregate_type', sa.String(length=64), nullable=False),
        sa.Column('aggregate_id', sa.Integer(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column(
            'status',
            sa.String(length=32),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_outbox_event')),
        sa.UniqueConstraint('event_id', name=op.f('uq_outbox_event_event_id')),
    )
    op.create_index(
        op.f('ix_outbox_event_status'),
        'outbox_event',
        ['status'],
        unique=False,
    )
    op.create_index(
        op.f('ix_outbox_event_aggregate_type'),
        'outbox_event',
        ['aggregate_type'],
        unique=False,
    )
    op.create_index(
        op.f('ix_outbox_event_aggregate_id'),
        'outbox_event',
        ['aggregate_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_outbox_event_aggregate_id'), table_name='outbox_event')
    op.drop_index(op.f('ix_outbox_event_aggregate_type'), table_name='outbox_event')
    op.drop_index(op.f('ix_outbox_event_status'), table_name='outbox_event')
    op.drop_table('outbox_event')