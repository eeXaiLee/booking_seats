"""add processed event

Revision ID: 8a34e5a8f3c1
Revises: 6e3a9d4f2a21
Create Date: 2026-03-26 06:35:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a34e5a8f3c1'
down_revision: Union[str, None] = '6e3a9d4f2a21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'processed_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column(
            'processed_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_processed_event')),
        sa.UniqueConstraint(
            'event_id',
            name=op.f('uq_processed_event_event_id'),
        ),
    )
    op.create_index(
        op.f('ix_processed_event_event_type'),
        'processed_event',
        ['event_type'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_processed_event_event_type'), table_name='processed_event')
    op.drop_table('processed_event')