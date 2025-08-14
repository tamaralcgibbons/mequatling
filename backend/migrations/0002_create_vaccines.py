"""create vaccines table

Revision ID: 0002_create_vaccines
Revises: 0001_create_groups
Create Date: 2025-08-13
"""
from alembic import op
import sqlalchemy as sa


revision = '0002_create_vaccines'
down_revision = '0001_create_groups'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'vaccines',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column('default_dose', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=32), nullable=True),
        sa.Column('methods', sa.JSON(), nullable=False, server_default=sa.text("'[]'") if op.get_bind().dialect.name != 'postgresql' else None),
        sa.Column('current_stock', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
    )


def downgrade():
    op.drop_table('vaccines')
