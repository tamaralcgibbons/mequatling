"""create vaccinations table

Revision ID: 0003_create_vaccinations
Revises: 0002_create_vaccines
Create Date: 2025-08-13
"""
from alembic import op
import sqlalchemy as sa


revision = '0003_create_vaccinations'
down_revision = '0002_create_vaccines'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'vaccinations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('animal_id', sa.Integer(), nullable=False, index=True),
        sa.Column('vaccine_id', sa.Integer(), nullable=False, index=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('dose', sa.Float(), nullable=False),
        sa.Column('method', sa.String(length=64), nullable=True),
        sa.Column('source', sa.String(length=16), nullable=True),  # 'group' | 'manual'
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.ForeignKeyConstraint(['animal_id'], ['animals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vaccine_id'], ['vaccines.id'], ondelete='CASCADE'),
    )


def downgrade():
    op.drop_table('vaccinations')
