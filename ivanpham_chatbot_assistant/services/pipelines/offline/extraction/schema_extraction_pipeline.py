from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ivanpham_chatbot_assistant.db.models.column import Column
from ivanpham_chatbot_assistant.db.models.database import Database
from ivanpham_chatbot_assistant.db.models.foreign_key import ForeignKey
from ivanpham_chatbot_assistant.db.models.schema import Schema
from ivanpham_chatbot_assistant.db.models.table import Table
from ivanpham_chatbot_assistant.services.source_sql.schema_crawler_service import (
    SchemaCrawlerService,
)
import time

from ivanpham_chatbot_assistant.settings import settings
from ivanpham_chatbot_assistant.web.schemas.schema_index_request import SchemaIndexRequest


class SchemaExtractionPipeline:
    """Offline pipeline to index a target database's schemas, tables, and columns."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def run(self, request: SchemaIndexRequest) -> str:
        """Runs the schema extraction and persists to internal database."""

        start_time = time.time()

        db_config = {
            "type": "sqlserver",
            "db_type": "sqlserver",
            "host": settings.sql_source_host,
            "port": settings.sql_source_port,
            "database": settings.sql_source_base,
            "user": settings.sql_source_user,
            "password": settings.sql_source_pass,
            "driver": settings.sql_source_driver,
            "encrypt": settings.sql_source_encrypt,
            "trust_cert": settings.sql_source_trust_cert,
        }

        # Setup python-to-SQL layer extraction
        logger.info(f"database indexing started for {settings.sql_source_base} on {settings.sql_source_host}")
        crawler = SchemaCrawlerService(db_config)

        try:
            # 1. Fetch metadata
            schemas = crawler.fetch_schemas()
            tables = crawler.fetch_tables()
            columns = crawler.fetch_columns()
            fks = crawler.fetch_foreign_keys()

            # 2. Extract Sample Values (Reduced to 1 query per table)
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            table_keys_to_index = {f"{t['schema_name']}.{t['table_name']}" for t in tables}
            tables_with_samples = set()
            table_samples_map = {}
            
            # 2.1 Sample tables in parallel (Adaptive Sampling)
            logger.info("Adaptive Sampling {count} tables in parallel (ASC + DESC)...", count=len(tables))
            
            def table_sample_worker(t):
                table_key = f"{t['schema_name']}.{t['table_name']}"
                try:
                    # Stage 1: Fast Sampling (100 ASC + 100 DESC = 200 rows)
                    rows = crawler.sample_table_rows(t["schema_name"], t["table_name"], limit=100)
                    
                    if not rows:
                        return table_key, rows

                    # Check if at least one column has a sample from these 200 rows
                    table_cols = [c["column_name"] for c in columns if c["table_name"] == t["table_name"]]
                    any_samples_found = False
                    for c_name in table_cols:
                        if crawler.build_column_samples_from_rows(rows, c_name):
                            any_samples_found = True
                            break
                    
                    # Stage 2: FULL TABLE SCAN (No limit)
                    # ONLY if the first stage failed to find any meaningful data for the whole table
                    if not any_samples_found:
                        logger.info(f"Table {table_key} looks sparse (no samples in first 200 rows). Falling back to FULL TABLE SCAN (Unlimited rows)...")
                        rows = crawler.sample_table_rows(t["schema_name"], t["table_name"], limit=None)

                    return table_key, rows
                except Exception as e:
                    logger.warning(f"Failed to sample table {table_key}: {e}")
                    return table_key, []

            with ThreadPoolExecutor(max_workers=24) as executor:
                futures = {executor.submit(table_sample_worker, t): t for t in tables}
                for future in as_completed(futures):
                    table_key, rows = future.result()
                    if rows:
                        table_samples_map[table_key] = rows
                        # Reduced logging: only log to debug for individual table success
                        logger.debug(f"Table {table_key}: {len(rows)} sample rows fetched")

            # 2.2 Populate column metadata from sampled rows in memory
            logger.info("Processing column samples for {count} columns...", count=len(columns))
            for col in columns:
                table_key = f"{col['schema_name']}.{col['table_name']}"
                if table_key not in table_samples_map:
                    continue
                
                rows = table_samples_map[table_key]
                samples = crawler.build_column_samples_from_rows(rows, col["column_name"])
                
                col["sample_values"] = samples
                col["distinct_count"] = len(samples)
                col["null_count"] = 0
                
                if samples:
                    tables_with_samples.add(table_key)

            # 2.3 Filter outcomes
            initial_table_count = len(tables)
            tables = [t for t in tables if f"{t['schema_name']}.{t['table_name']}" in tables_with_samples]
            columns = [c for c in columns if f"{c['schema_name']}.{c['table_name']}" in tables_with_samples]
            
            # Populate column_count for each table
            for t in tables:
                table_key = f"{t['schema_name']}.{t['table_name']}"
                t_cols = [c for c in columns if f"{c['schema_name']}.{c['table_name']}" == table_key]
                t["column_count"] = len(t_cols)
            
            # Filter foreign keys
            fks = [
                fk for fk in fks 
                if f"{fk['schema_name']}.{fk['table_name']}" in tables_with_samples 
                and f"{fk['referenced_schema_name']}.{fk['referenced_table_name']}" in tables_with_samples
            ]
            
            skipped_count = initial_table_count - len(tables)
            if skipped_count > 0:
                logger.info("Finished sampling. Kept {active} tables, skipped {skipped} tables (broken/empty/system).", 
                            active=len(tables), skipped=skipped_count)
            
            # Filter foreign keys
            fks = [
                fk for fk in fks 
                if f"{fk['schema_name']}.{fk['table_name']}" in tables_with_samples 
                and f"{fk['referenced_schema_name']}.{fk['referenced_table_name']}" in tables_with_samples
            ]
            
            skipped_count = initial_table_count - len(tables)
            if skipped_count > 0:
                logger.info("Finished sampling. Kept {active} tables, skipped {skipped} tables (broken/empty/system).", 
                            active=len(tables), skipped=skipped_count)

            logger.info("Metadata extraction completed. Saving to database...")
            
            # Step 3...

            # 3. Save to internal database
            async with self.session_factory() as session:
                async with session.begin():
                    # 3.1 Upsert Database
                    db_instance = await self._upsert_database(session, request)

                    # 3.2 Upsert Schemas
                    schema_id_map = {}
                    for schema_name in schemas:
                        schema_obj = await self._upsert_schema(session, db_instance.id, schema_name)
                        schema_id_map[schema_name] = schema_obj.id

                    # 3.3 Upsert Tables
                    table_id_map = {}
                    for table in tables:
                        s_name = table["schema_name"]
                        t_name = table["table_name"]
                        if s_name not in schema_id_map:
                            continue

                        table_obj = await self._upsert_table(session, schema_id_map[s_name], table)
                        table_id_map[f"{s_name}.{t_name}"] = table_obj.id

                    # 3.4 Upsert Columns
                    col_id_map = {}
                    for col in columns:
                        s_name = col["schema_name"]
                        t_name = col["table_name"]
                        c_name = col["column_name"]
                        table_key = f"{s_name}.{t_name}"

                        if table_key not in table_id_map:
                            continue

                        col_obj = await self._upsert_column(session, table_id_map[table_key], col)
                        col_id_map[f"{s_name}.{t_name}.{c_name}"] = col_obj.id

                    # 3.5 Upsert Foreign Keys
                    for fk in fks:
                        await self._upsert_foreign_key(session, col_id_map, fk)

                    # 3.6 Virtual Foreign Key Discovery (For legacy DBs without hard constraints)
                    virtual_fks = self._discover_virtual_fks(columns)
                    logger.info("Discovered {count} virtual foreign keys based on heuristics", count=len(virtual_fks))
                    for vfk in virtual_fks:
                        await self._upsert_foreign_key(session, col_id_map, vfk)

            duration = time.time() - start_time
            logger.info("Schema indexing completed\n"
                        f"schemas={len(schemas)}\n"
                        f"tables={len(tables)}\n"
                        f"columns={len(columns)}\n"
                        f"duration={duration:.1f}s")
            return "success"

        except Exception as e:
            logger.error(f"Schema extraction failed for {settings.sql_source_base}: {e}")
            raise e

    async def _upsert_database(self, session: AsyncSession, req: SchemaIndexRequest) -> Database:
        result = await session.execute(
            select(Database).where(Database.name == settings.sql_source_base, Database.host == settings.sql_source_host)
        )
        db_obj = result.scalars().first()
        
        if db_obj and req.force_refresh:
            await session.delete(db_obj)
            await session.flush()
            db_obj = None

        if not db_obj:
            db_obj = Database(
                name=settings.sql_source_base,
                db_type="sqlserver",
                host=settings.sql_source_host,
                port=settings.sql_source_port,
            )
            session.add(db_obj)
            await session.flush()
        return db_obj

    async def _upsert_schema(self, session: AsyncSession, db_id, schema_name: str) -> Schema:
        result = await session.execute(
            select(Schema).where(Schema.database_id == db_id, Schema.name == schema_name)
        )
        schema_obj = result.scalars().first()
        if not schema_obj:
            schema_obj = Schema(database_id=db_id, name=schema_name)
            session.add(schema_obj)
            await session.flush()
        return schema_obj

    async def _upsert_table(self, session: AsyncSession, schema_id, table: dict[str, Any]) -> Table:
        table_name = table["table_name"]
        result = await session.execute(
            select(Table).where(Table.schema_id == schema_id, Table.name == table_name)
        )
        table_obj = result.scalars().first()
        if not table_obj:
            table_obj = Table(
                schema_id=schema_id, 
                name=table_name,
                column_count=table.get("column_count")
            )
            session.add(table_obj)
        else:
            table_obj.column_count = table.get("column_count")
            
        await session.flush()
        return table_obj

    async def _upsert_column(self, session: AsyncSession, table_id, col: dict[str, Any]) -> Column:
        result = await session.execute(
            select(Column).where(Column.table_id == table_id, Column.name == col["column_name"])
        )
        col_obj = result.scalars().first()
        if not col_obj:
            col_obj = Column(
                table_id=table_id,
                name=col["column_name"],
                data_type=col["data_type"],
                is_nullable=col["is_nullable"],
                ordinal_position=col["ordinal_position"],
            )
            session.add(col_obj)
        else:
            col_obj.data_type = col["data_type"]
            col_obj.is_nullable = col["is_nullable"]
            col_obj.ordinal_position = col["ordinal_position"]

        col_obj.sample_values = col.get("sample_values")
        col_obj.distinct_count = col.get("distinct_count")
        col_obj.null_count = col.get("null_count")

        await session.flush()
        return col_obj

    def _discover_virtual_fks(self, columns: list[dict[str, Any]]) -> list[dict[str, str]]:
        """
        Discovers potential foreign key relationships based on column naming heuristics.
        Useful for legacy databases lacking formal FK constraints.
        """
        virtual_fks = []
        
        # 1. Identify potential PK-like columns (id, code, pk)
        pk_candidates = {} # name_lower -> list of columns
        for col in columns:
            name_lower = col["column_name"].lower()
            if name_lower in ["id", "code", "pk"] or name_lower.endswith("_id") or name_lower.endswith("_code"):
                if name_lower not in pk_candidates:
                    pk_candidates[name_lower] = []
                pk_candidates[name_lower].append(col)
        
        # 2. Match potential FKs to PKs
        # Heuristic: If Table A has 'partner_id' and Table B has 'id' and is named 'Partner'
        for col in columns:
            name_lower = col["column_name"].lower()
            
            # Skip if it looks like a generic PK
            if name_lower in ["id", "pk"]:
                continue
                
            # Pattern 1: column 'user_id' matches table 'users' with column 'id'
            if name_lower.endswith("_id"):
                base_name = name_lower[:-3] # 'user'
                for target_col in pk_candidates.get("id", []):
                    target_table_lower = target_col["table_name"].lower()
                    # Check if table name matches (starts with or plural/singular)
                    if target_table_lower == base_name or target_table_lower == base_name + "s" or target_table_lower == base_name + "es":
                        # Avoid self-reference
                        if col["table_name"] == target_col["table_name"]:
                            continue
                            
                        virtual_fks.append({
                            "schema_name": col["schema_name"],
                            "table_name": col["table_name"],
                            "column_name": col["column_name"],
                            "referenced_schema_name": target_col["schema_name"],
                            "referenced_table_name": target_col["table_name"],
                            "referenced_column_name": target_col["column_name"]
                        })

        return virtual_fks

    async def _upsert_foreign_key(self, session: AsyncSession, col_id_map: dict[str, Any], fk: dict[str, str]):
        col_key = f"{fk['schema_name']}.{fk['table_name']}.{fk['column_name']}"
        ref_col_key = f"{fk['referenced_schema_name']}.{fk['referenced_table_name']}.{fk['referenced_column_name']}"

        col_id = col_id_map.get(col_key)
        ref_col_id = col_id_map.get(ref_col_key)

        if col_id and ref_col_id:
            result = await session.execute(
                select(ForeignKey).where(
                    ForeignKey.column_id == col_id,
                    ForeignKey.referenced_column_id == ref_col_id
                )
            )
            fk_obj = result.scalars().first()
            if not fk_obj:
                fk_obj = ForeignKey(column_id=col_id, referenced_column_id=ref_col_id)
                session.add(fk_obj)
                await session.flush()
