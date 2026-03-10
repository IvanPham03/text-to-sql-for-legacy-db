# Database Infrastructure Module

The `db` module provides centralized management for all database connections in the Text-to-SQL system. It supports multiple database engines (Postgres, MySQL, SQL Server) and handles connection pools automatically. It also stores **metadata** about indexed databases — schemas, tables, columns, semantic descriptions, and vector embeddings — enabling the RAG retrieval pipeline.

## Architecture

```
db/
├── base.py               # SQLAlchemy declarative Base
├── meta.py               # MetaData instance shared by models & Alembic
├── config.py             # Default pool/engine settings
├── dependencies.py       # FastAPI-style dependency helpers (get_engine)
├── registry.py           # Registry of external database source configs
├── engines/              # Engine implementations per dialect
│   ├── postgres_engine.py
│   ├── mysql_engine.py
│   └── sqlserver_engine.py
├── factory/
│   └── engine_factory.py # Selects the right engine class by type
├── pool/
│   └── pool_manager.py   # Singleton PoolManager caching connection pools
├── models/               # SQLAlchemy 2.0 ORM metadata models (see below)
│   ├── database.py
│   ├── schema.py
│   ├── table.py
│   ├── column.py
│   ├── foreign_key.py
│   ├── table_description.py
│   ├── column_description.py
│   ├── query_example.py
│   └── embedding.py
└── migrations/           # Alembic migration scripts
    ├── env.py
    └── versions/
        └── 2026-03-09-00-10_c56555f965f4.py  # Metadata tables
```

## Metadata Models

These SQLAlchemy 2.0 models capture structured information about indexed SQL databases. All models use UUID primary keys and include `created_at` / `updated_at` timestamps.

| Model | Table | Description |
|-------|-------|-------------|
| `Database` | `databases` | A registered database instance (host, type, port) |
| `Schema` | `schemas` | A schema belonging to a Database |
| `Table` | `tables` | A table within a Schema |
| `Column` | `columns` | Columns with their data types and key flags |
| `ForeignKey` | `foreign_keys` | Foreign key constraints between tables/columns |
| `TableDescription` | `table_descriptions` | Semantic summary & usage notes per table |
| `ColumnDescription` | `column_descriptions` | Business meaning per column |
| `QueryExample` | `query_examples` | Natural language → SQL query pairs for RAG training |
| `Embedding` | `embeddings` | 1536-dim vector embeddings (pgvector) for retrieval |

### Entity Relationship Overview

```
Database ──< Schema ──< Table ──< Column
                          │           └──< ColumnDescription
                          ├──< ForeignKey
                          └──< TableDescription
Database ──< QueryExample
Table/Column/QueryExample ──< Embedding (via entity_type + entity_id)
```

## Supported External Databases

- **PostgreSQL**: Core metadata store. Uses `asyncpg` for async connections.
- **MySQL**: Supported for external source databases.
- **SQL Server**: Supported for enterprise ERP/CRM sources (ODBC Driver 18).

## Configuration and Usage

### 1. Adding a new external database source

1. Add credentials to `.env` and `ivanpham_chatbot_assistant/settings.py`.
2. Register it in `ivanpham_chatbot_assistant/db/registry.py`:

```python
DATABASES = {
    "sales_db": {
        "type": "mysql",
        "url": settings.sales_db_url,
        "pool_size": 10,
        "max_overflow": 20,
    }
}
```

### 2. Using the DB engine in services/pipelines

```python
from sqlalchemy import text
from ivanpham_chatbot_assistant.db.dependencies import get_engine

source_engine = get_engine("sql_source")

def fetch_schema():
    with source_engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM INFORMATION_SCHEMA.TABLES;"))
        return result.fetchall()
```

### 3. Applying Migrations

All metadata tables are managed by Alembic. Run migrations inside Docker:

```bash
# Apply all pending migrations
docker compose run --rm api uv run alembic upgrade head

# Revert all migrations
docker compose run --rm api uv run alembic downgrade base

# Generate a new migration (requires running DB)
docker compose run --rm api uv run alembic revision --autogenerate -m "describe change"
```

### Connection Pooling

Default engine settings in `ivanpham_chatbot_assistant/db/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `pool_size` | 10 | Max persistent connections |
| `max_overflow` | 20 | Extra connections above pool_size |
| `pool_pre_ping` | `True` | Detects stale connections before use |
| `pool_recycle` | 1800 | Recycles connections older than 30 min |
