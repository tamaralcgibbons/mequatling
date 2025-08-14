"""create stock_ledger table

Revision ID: 0006_create_stock_ledger
Revises: 0005_add_group_fk_to_animals
Create Date: 2025-08-13
"""
from alembic import op
import sqlalchemy as sa


revision = '0006_create_stock_ledger'
down_revision = '0005_add_group_fk_to_animals'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'stock_ledger',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('vaccine_id', sa.Integer(), nullable=False, index=True),
        sa.Column('delta', sa.Float(), nullable=False),  # +ve add, -ve consume
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('ref_type', sa.String(length=32), nullable=True),
        sa.Column('ref_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('balance_after', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['vaccine_id'], ['vaccines.id'], ondelete='CASCADE'),
    )


def downgrade():
    op.drop_table('stock_ledger')
