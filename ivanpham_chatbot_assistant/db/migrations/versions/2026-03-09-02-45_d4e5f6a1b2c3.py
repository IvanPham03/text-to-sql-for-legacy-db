"""Add sampling columns to columns table.

Revision ID: d4e5f6a1b2c3
Revises: c56555f965f4
Create Date: 2026-03-09 02:45:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a1b2c3"
down_revision = "c56555f965f4"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Use JSON for sample_values to store the list/dict
    op.add_column('columns', sa.Column('sample_values', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('columns', sa.Column('distinct_count', sa.Integer(), nullable=True))
    op.add_column('columns', sa.Column('null_count', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('columns', 'null_count')
    op.drop_column('columns', 'distinct_count')
    op.drop_column('columns', 'sample_values')
