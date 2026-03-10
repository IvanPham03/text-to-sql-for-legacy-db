"""Add metadata models.

Revision ID: c56555f965f4
Revises: 819cbf6e030b
Create Date: 2026-03-09 00:10:44.943443

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c56555f965f4"
down_revision = "819cbf6e030b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Run the migration."""
    # Enable pgvector extension removed

    op.create_table(
        "databases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("db_type", sa.String(length=50), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_databases_name"), "databases", ["name"], unique=False)

    op.create_table(
        "schemas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("database_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["database_id"], ["databases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_schemas_database_id"), "schemas", ["database_id"], unique=False
    )

    op.create_table(
        "query_examples",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("database_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.String(), nullable=False),
        sa.Column("sql_query", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(["database_id"], ["databases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_query_examples_database_id"),
        "query_examples",
        ["database_id"],
        unique=False,
    )

    op.create_table(
        "tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("schema_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["schema_id"], ["schemas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tables_schema_id"), "tables", ["schema_id"], unique=False)

    op.create_table(
        "columns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("data_type", sa.String(length=255), nullable=False),
        sa.Column("is_nullable", sa.Boolean(), nullable=False),
        sa.Column("is_primary_key", sa.Boolean(), nullable=False),
        sa.Column("is_foreign_key", sa.Boolean(), nullable=False),
        sa.Column("ordinal_position", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["table_id"], ["tables.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_columns_table_id"), "columns", ["table_id"], unique=False)

    op.create_table(
        "foreign_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_column_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_column_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("constraint_name", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_column_id"], ["columns.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["source_table_id"], ["tables.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["target_column_id"], ["columns.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["target_table_id"], ["tables.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_foreign_keys_source_column_id"),
        "foreign_keys",
        ["source_column_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_foreign_keys_source_table_id"),
        "foreign_keys",
        ["source_table_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_foreign_keys_target_column_id"),
        "foreign_keys",
        ["target_column_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_foreign_keys_target_table_id"),
        "foreign_keys",
        ["target_table_id"],
        unique=False,
    )

    op.create_table(
        "table_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("business_description", sa.String(), nullable=True),
        sa.Column("usage_notes", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["table_id"], ["tables.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_table_descriptions_table_id"),
        "table_descriptions",
        ["table_id"],
        unique=True,
    )

    op.create_table(
        "column_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("column_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("examples", sa.String(), nullable=True),
        sa.Column("business_meaning", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["column_id"], ["columns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_column_descriptions_column_id"),
        "column_descriptions",
        ["column_id"],
        unique=True,
    )

def downgrade() -> None:
    """Undo the migration."""
    op.drop_index(
        op.f("ix_column_descriptions_column_id"), table_name="column_descriptions"
    )
    op.drop_table("column_descriptions")
    op.drop_index(
        op.f("ix_table_descriptions_table_id"), table_name="table_descriptions"
    )
    op.drop_table("table_descriptions")
    op.drop_index(op.f("ix_foreign_keys_target_table_id"), table_name="foreign_keys")
    op.drop_index(op.f("ix_foreign_keys_target_column_id"), table_name="foreign_keys")
    op.drop_index(op.f("ix_foreign_keys_source_table_id"), table_name="foreign_keys")
    op.drop_index(op.f("ix_foreign_keys_source_column_id"), table_name="foreign_keys")
    op.drop_table("foreign_keys")
    op.drop_index(op.f("ix_columns_table_id"), table_name="columns")
    op.drop_table("columns")
    op.drop_index(op.f("ix_tables_schema_id"), table_name="tables")
    op.drop_table("tables")
    op.drop_index(op.f("ix_query_examples_database_id"), table_name="query_examples")
    op.drop_table("query_examples")
    op.drop_index(op.f("ix_schemas_database_id"), table_name="schemas")
    op.drop_table("schemas")
    op.drop_index(op.f("ix_databases_name"), table_name="databases")
    op.drop_table("databases")
