from alembic import op
import sqlalchemy as sa

revision = '0014_create_fuel_stocktake_events'
down_revision = '0013_create_fertiliser_stocktake_events'  # Update if needed
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'fuel_stocktake_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('fuel_id', sa.Integer(), sa.ForeignKey('fuels.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('recorded_stock', sa.Float(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('notes', sa.Text(), nullable=True),
            )

def downgrade():
    op.drop_table('fuel_stocktake_events')