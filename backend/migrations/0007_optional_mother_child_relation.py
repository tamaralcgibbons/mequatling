"""add mother_id FK (self-referential) to animals

Revision ID: 0007_optional_mother_child_relation
Revises: 0006_create_stock_ledger
Create Date: 2025-08-13
"""
from alembic import op
import sqlalchemy as sa


revision = '0007_optional_mother_child_relation'
down_revision = '0006_create_stock_ledger'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('animals', sa.Column('mother_id', sa.Integer(), nullable=True, index=True))
    op.create_foreign_key(
        'fk_animals_mother',
        'animals',
        'animals',
        ['mother_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_animals_mother', 'animals', type_='foreignkey')
    with op.batch_alter_table('animals') as batch:
        batch.drop_column('mother_id')
