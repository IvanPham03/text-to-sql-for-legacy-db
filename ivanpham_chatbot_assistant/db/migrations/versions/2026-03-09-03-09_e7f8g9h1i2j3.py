"""Replace row_count with column_count in tables table.

Revision ID: e7f8g9h1i2j3
Revises: d4e5f6a1b2c3
Create Date: 2026-03-09 03:09:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = "e7f8g9h1i2j3"
down_revision = "d4e5f6a1b2c3"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Remove the useless row_count (dynamic) and add column_count (static)
    op.drop_column('tables', 'row_count')
    op.add_column('tables', sa.Column('column_count', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('tables', 'column_count')
    op.add_column('tables', sa.Column('row_count', sa.Integer(), nullable=True))
