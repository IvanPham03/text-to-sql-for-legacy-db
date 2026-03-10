import hashlib
import time
import uuid
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from ivanpham_chatbot_assistant.db.models.column import Column
from ivanpham_chatbot_assistant.db.models.schema import Schema
from ivanpham_chatbot_assistant.db.models.table import Table
from ivanpham_chatbot_assistant.services.pipelines.offline.embedding.schema_embedding_service import (
    SchemaEmbeddingService,
)
from ivanpham_chatbot_assistant.services.vector_store.qdrant_service import (
    QdrantService,
)
from ivanpham_chatbot_assistant.web.metrics.schema_sync_metrics import (
    schema_sync_duration_seconds,
    schema_vectors_total,
)


class SchemaSyncService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.embedding_service = SchemaEmbeddingService()
        self.qdrant_service = QdrantService()

    def _generate_checksum(self, content: str) -> str:
        """Generates a MD5 checksum for the given content."""
        return hashlib.md5(content.encode()).hexdigest()

    def _generate_vector_id(self, db: str, schema: str, table: str, col: str) -> str:
        """Generates a deterministic vector ID for Qdrant (UUID format)."""
        seed = f"{db}.{schema}.{table}.{col}"
        # Qdrant accepts UUIDs, we can generate a stable UUID from a hash
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))

    def _compute_column_checksum(self, column: Column) -> str:
        """
        Computes a checksum based on:
        name + data_type + sample_values + summary + business_meaning
        """
        col_desc = column.column_description
        components = [
            column.name,
            column.data_type,
            str(column.sample_values or []),
            col_desc.summary if col_desc else "",
            col_desc.business_meaning if col_desc else "",
        ]
        content = "|".join(filter(None, components))
        return self._generate_checksum(content)

    async def full_sync(self) -> dict[str, Any]:
        """
        Performs a full sync. Driven by existence of TableDescription/ColumnDescription.
        """
        start_time = time.perf_counter()
        stats = {"tables_processed": 0, "columns_processed": 0, "vectors_upserted": 0}

        async with self.session_factory() as session:
            # Hierarchical fetch
            stmt = select(Table).options(
                joinedload(Table.schema).joinedload(Schema.database),
                joinedload(Table.table_description),
                joinedload(Table.columns).joinedload(Column.column_description),
            )
            result = await session.execute(stmt)
            tables = result.unique().scalars().all()

            schema_data = {"tables": []}

            for table in tables:
                db_name = table.schema.database.name
                schema_name = table.schema.name

                table_desc_row = table.table_description
                has_table_description = table_desc_row is not None

                # Only sync columns that HAVE descriptions
                valid_columns = [
                    c for c in table.columns if c.column_description is not None
                ]

                if not has_table_description and not valid_columns:
                    continue

                stats["tables_processed"] += 1
                table_entry = {
                    "id": table.id,
                    "name": table.name,
                    "database_name": db_name,
                    "schema_name": schema_name,
                    "description": table_desc_row.summary
                    if has_table_description
                    else None,
                    "columns": [],
                }

                for col in valid_columns:
                    stats["columns_processed"] += 1
                    col_desc_row = col.column_description

                    # Update checksum in DB
                    col.sync_checksum = self._compute_column_checksum(col)

                    table_entry["columns"].append(
                        {
                            "id": col.id,
                            "name": col.name,
                            "description": col_desc_row.summary,
                            "business_meaning": col_desc_row.business_meaning,
                            "data_type": col.data_type,
                            "is_nullable": col.is_nullable,
                            "is_primary_key": col.is_primary_key,
                            "is_foreign_key": col.is_foreign_key,
                            "sample_values": col.sample_values,
                            "distinct_count": col.distinct_count,
                            "vector_id": self._generate_vector_id(
                                db_name, schema_name, table.name, col.name
                            ),
                        }
                    )

                if table_entry["columns"]:
                    schema_data["tables"].append(table_entry)

            if schema_data["tables"]:
                result = await self.embedding_service.execute(schema_data)
                stats["vectors_upserted"] = result["embeddings_stored"]
                await session.commit()
                logger.info(f"Full sync: Upserted {stats['vectors_upserted']} vectors.")
            else:
                logger.info("Full sync: No items with descriptions found to sync.")

        duration = time.perf_counter() - start_time
        schema_sync_duration_seconds.labels(sync_type="full").observe(duration)
        schema_vectors_total.labels(type="column").set(stats["columns_processed"])

        return stats

    async def incremental_sync(self) -> dict[str, Any]:
        """
        Syncs only changed elements that have descriptions.
        """
        start_time = time.perf_counter()
        stats = {"columns_processed": 0, "vectors_upserted": 0}

        async with self.session_factory() as session:
            stmt = select(Table).options(
                joinedload(Table.schema).joinedload(Schema.database),
                joinedload(Table.table_description),
                joinedload(Table.columns).joinedload(Column.column_description),
            )
            result = await session.execute(stmt)
            tables = result.unique().scalars().all()

            changed_schema_data = {"tables": []}

            for table in tables:
                db_name = table.schema.database.name
                schema_name = table.schema.name

                valid_columns = [
                    c for c in table.columns if c.column_description is not None
                ]
                changed_columns = []

                for col in valid_columns:
                    new_checksum = self._compute_column_checksum(col)
                    if col.sync_checksum != new_checksum:
                        col_desc_row = col.column_description
                        changed_columns.append(
                            {
                                "id": col.id,
                                "name": col.name,
                                "description": col_desc_row.summary,
                                "business_meaning": col_desc_row.business_meaning,
                                "data_type": col.data_type,
                                "is_nullable": col.is_nullable,
                                "is_primary_key": col.is_primary_key,
                                "is_foreign_key": col.is_foreign_key,
                                "sample_values": col.sample_values,
                                "distinct_count": col.distinct_count,
                                "vector_id": self._generate_vector_id(
                                    db_name, schema_name, table.name, col.name
                                ),
                            }
                        )
                        col.sync_checksum = new_checksum
                        stats["columns_processed"] += 1

                if changed_columns:
                    changed_schema_data["tables"].append(
                        {
                            "id": table.id,
                            "name": table.name,
                            "database_name": db_name,
                            "schema_name": schema_name,
                            "description": table.table_description.summary
                            if table.table_description
                            else None,
                            "columns": changed_columns,
                        }
                    )

            if changed_schema_data["tables"]:
                result = await self.embedding_service.execute(changed_schema_data)
                stats["vectors_upserted"] = result["embeddings_stored"]
                await session.commit()
                logger.info(
                    f"Incremental sync: Upserted {stats['vectors_upserted']} vectors."
                )
            else:
                logger.info("Incremental sync: No description changes detected.")

        duration = time.perf_counter() - start_time
        schema_sync_duration_seconds.labels(sync_type="incremental").observe(duration)
        return stats

    async def cleanup_sync(self) -> dict[str, Any]:
        """
        Deletes vectors for columns no longer present in the internal DB.
        """
        start_time = time.perf_counter()
        stats = {"vectors_deleted": 0}

        async with self.session_factory() as session:
            # 1. Get all deterministic IDs that SHOULD exist in Qdrant
            # We only generate IDs for columns that have descriptions
            stmt = (
                select(Column)
                .options(
                    joinedload(Column.table)
                    .joinedload(Table.schema)
                    .joinedload(Schema.database),
                    joinedload(Column.column_description),
                )
                .where(Column.column_description is not None)
            )

            result = await session.execute(stmt)
            columns = result.scalars().all()

            valid_vector_ids = set()
            for col in columns:
                vid = self._generate_vector_id(
                    col.table.schema.database.name,
                    col.table.schema.name,
                    col.table.name,
                    col.name,
                )
                valid_vector_ids.add(vid)

            # 2. Cleanup orphaned vectors in Qdrant
            # Since Qdrant doesn't support "not in" easily for all points,
            # we scroll through all points and check
            if self.qdrant_service.client:
                logger.info("Starting deletion sync (cleanup)...")

                # In a real production system, you'd use a scroll API or specialized indexing.
                # For simplicity, we fetch all points (assuming small enough collection for Text-to-SQL schemas)
                # or use payload discovery.

                # Simple implementation: fetch all points and check
                # This is okay for schema sync which has limited number of items (<100k)
                offset = None
                while True:
                    scroll_result = await self.qdrant_service.client.scroll(
                        collection_name=self.qdrant_service.collection_name,
                        limit=100,
                        offset=offset,
                        with_payload=True,
                    )
                    points, offset = scroll_result

                    orphans = [
                        p.id for p in points if str(p.id) not in valid_vector_ids
                    ]
                    if orphans:
                        await self.qdrant_service.delete_vectors(orphans)
                        stats["vectors_deleted"] += len(orphans)
                        logger.info(
                            f"Deleted {len(orphans)} orphaned vectors from Qdrant."
                        )

                    if offset is None:
                        break

        duration = time.perf_counter() - start_time
        schema_sync_duration_seconds.labels(sync_type="cleanup").observe(duration)
        return stats
