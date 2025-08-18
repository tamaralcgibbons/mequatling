"""create groups table

Revision ID: 0001_create_groups
Revises: 
Create Date: 2025-08-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_create_groups'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('camp_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
    )
    # Optional FK to camps if that table exists already; safe to leave as commented if not yet present:
    # op.create_foreign_key('fk_groups_camp', 'groups', 'camps', ['camp_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_table('groups')
