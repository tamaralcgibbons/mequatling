"""alter animals: add parity + deceased fields

Revision ID: 0004_alter_animals_add_parity_and_deceased_fields
Revises: 0003_create_vaccinations
Create Date: 2025-08-13
"""
from alembic import op
import sqlalchemy as sa


revision = '0004_alter_animals_add_parity_and_deceased_fields'
down_revision = '0003_create_vaccinations'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.add_column('animals', sa.Column('deceased', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('animals', sa.Column('killed', sa.Boolean(), nullable=True))
    op.add_column('animals', sa.Column('death_reason', sa.Text(), nullable=True))

    op.add_column('animals', sa.Column('has_calved', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('animals', sa.Column('calves_count', sa.Integer(), nullable=False, server_default='0'))
    # JSON calves_tags
    op.add_column('animals', sa.Column('calves_tags', sa.JSON(), nullable=False, server_default=sa.text("'[]'") if dialect != 'postgresql' else None))

    # ensure server_default cleared (optional) after initial migration
    with op.batch_alter_table('animals') as batch:
        batch.alter_column('deceased', server_default=None)
        batch.alter_column('has_calved', server_default=None)
        batch.alter_column('calves_count', server_default=None)


def downgrade():
    with op.batch_alter_table('animals') as batch:
        batch.drop_column('calves_tags')
        batch.drop_column('calves_count')
        batch.drop_column('has_calved')
        batch.drop_column('death_reason')
        batch.drop_column('killed')
        batch.drop_column('deceased')
