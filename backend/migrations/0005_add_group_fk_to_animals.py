"""add group_id FK to animals

Revision ID: 0005_add_group_fk_to_animals
Revises: 0004_alter_animals_add_parity_and_deceased_fields
Create Date: 2025-08-13
"""
from alembic import op
import sqlalchemy as sa


revision = '0005_add_group_fk_to_animals'
down_revision = '0004_alter_animals_add_parity_and_deceased_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('animals', sa.Column('group_id', sa.Integer(), nullable=True, index=True))
    # if groups table exists (from 0001), add FK constraint
    op.create_foreign_key('fk_animals_group', 'animals', 'groups', ['group_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint('fk_animals_group', 'animals', type_='foreignkey')
    with op.batch_alter_table('animals') as batch:
        batch.drop_column('group_id')
