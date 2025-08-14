"""create camps table

Revision ID: 0008_create_camps
Revises: 0007_optional_mother_child_relation
Create Date: 2025-08-13
"""
from alembic import op
import sqlalchemy as sa

revision = '0008_create_camps'
down_revision = '0007_optional_mother_child_relation'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'camps',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
    )
    # If you want a real FK from groups.camp_id -> camps.id (your model has an FK):
    try:
        op.create_foreign_key('fk_groups_camp', 'groups', 'camps', ['camp_id'], ['id'], ondelete='SET NULL')
    except Exception:
        # If groups.camp_id doesn’t exist yet or FK already present, ignore
        pass

def downgrade():
    # Drop FK first if it exists
    try:
        op.drop_constraint('fk_groups_camp', 'groups', type_='foreignkey')
    except Exception:
        pass
    op.drop_table('camps')
