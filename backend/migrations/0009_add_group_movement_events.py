from alembic import op
import sqlalchemy as sa

revision = '0009_add_group_movement_events'
down_revision = '0008_create_camps'  # Replace with your previous revision ID
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'group_movement_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('from_camp_id', sa.Integer(), sa.ForeignKey('camps.id'), nullable=True),
        sa.Column('to_camp_id', sa.Integer(), sa.ForeignKey('camps.id'), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
    )

def downgrade():
    op.drop_table('group_movement_events')