from alembic import op
import sqlalchemy as sa

revision = '0011_create_vaccine_stocktake_events'
down_revision = '0010_add_vaccinations_table'  # Update if needed
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'vaccine_stocktake_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('vaccine_id', sa.Integer(), sa.ForeignKey('vaccines.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('recorded_stock', sa.Float(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('notes', sa.Text(), nullable=True),
    )

def