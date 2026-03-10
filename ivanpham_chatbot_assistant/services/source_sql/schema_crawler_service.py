import json
from typing import Any

from loguru import logger
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_exponential

from ivanpham_chatbot_assistant.db.factory.engine_factory import create_engine_by_type


class SchemaCrawlerService:
    """Service to crawl target databases and extract schema metadata and sample values."""

    def __init__(self, db_config: dict[str, Any]):
        """Initialize the crawler with a source database connection."""
        self.db_type = db_config.get("db_type", "postgres").lower()

        # Build URL for engines that require it
        if "url" not in db_config:
            host = db_config.get("host", "localhost")
            port = db_config.get("port")
            user = db_config.get("user", "")
            password = db_config.get("password", "")
            database = db_config.get("database", "")

            if self.db_type == "postgres" or self.db_type == "postgresql":
                port_str = f":{port}" if port else ":5432"
                db_config["url"] = (
                    f"postgresql://{user}:{password}@{host}{port_str}/{database}"
                )
            elif self.db_type == "mysql":
                port_str = f":{port}" if port else ":3306"
                db_config["url"] = (
                    f"mysql+pymysql://{user}:{password}@{host}{port_str}/{database}"
                )

        self.engine = create_engine_by_type(self.db_type, db_config)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_schemas(self) -> list[str]:
        """Extract schemas from the source database, excluding system schemas."""
        excluded_schemas = (
            "information_schema",
            "sys",
            "guest",
            "db_owner",
            "db_accessadmin",
            "db_securityadmin",
            "db_ddladmin",
            "db_backupoperator",
            "db_datareader",
            "db_datawriter",
            "db_denydatareader",
            "db_denydatawriter",
        )

        query = text("SELECT schema_name FROM information_schema.schemata")
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                schemas = [
                    row[0] for row in result if row[0].lower() not in excluded_schemas
                ]
                logger.info(
                    "Extracted {count} schemas after filtering", count=len(schemas)
                )
                return schemas
        except Exception as e:
            logger.error("Failed to extract schemas: {error}", error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_tables(self) -> list[dict[str, str]]:
        """Extract all base tables and views from the source database, excluding system schemas."""
        excluded_schemas = (
            "information_schema",
            "sys",
            "guest",
            "db_owner",
            "db_accessadmin",
            "db_securityadmin",
            "db_ddladmin",
            "db_backupoperator",
            "db_datareader",
            "db_datawriter",
            "db_denydatareader",
            "db_denydatawriter",
        )

        query = text("""
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables 
            WHERE table_type IN ('BASE TABLE', 'VIEW')
        """)
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                tables = []
                for row in result:
                    if row[0].lower() not in excluded_schemas:
                        tables.append(
                            {
                                "schema_name": row[0],
                                "table_name": row[1],
                                "table_type": row[2],
                            }
                        )
                logger.info("Extracted {count} tables/views", count=len(tables))
                return tables
        except Exception as e:
            logger.error("Failed to extract tables: {error}", error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_columns(self) -> list[dict[str, Any]]:
        """Extract all columns from the source database, excluding system schemas."""
        excluded_schemas = (
            "information_schema",
            "sys",
            "guest",
            "db_owner",
            "db_accessadmin",
            "db_securityadmin",
            "db_ddladmin",
            "db_backupoperator",
            "db_datareader",
            "db_datawriter",
            "db_denydatareader",
            "db_denydatawriter",
        )

        query = text("""
            SELECT table_schema, table_name, column_name, data_type, is_nullable, ordinal_position 
            FROM information_schema.columns
        """)
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                columns = []
                for row in result:
                    if row[0].lower() in excluded_schemas:
                        continue

                    is_nullable = False
                    if isinstance(row[4], str):
                        is_nullable = row[4].upper() in ["YES", "TRUE", "1"]
                    else:
                        is_nullable = bool(row[4])

                    columns.append(
                        {
                            "schema_name": row[0],
                            "table_name": row[1],
                            "column_name": row[2],
                            "data_type": row[3],
                            "is_nullable": is_nullable,
                            "ordinal_position": row[5],
                        }
                    )
                logger.info(
                    "Extracted {count} columns after filtering", count=len(columns)
                )
                return columns
        except Exception as e:
            logger.error("Failed to extract columns: {error}", error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_foreign_keys(self) -> list[dict[str, str]]:
        """Extract foreign keys from the source database."""
        query = text("""
            SELECT 
                kcu.table_schema as schema_name,
                kcu.table_name as table_name,
                kcu.column_name as column_name,
                ccu.table_schema as referenced_schema_name,
                ccu.table_name as referenced_table_name,
                ccu.column_name as referenced_column_name
            FROM 
                information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu 
                ON tc.constraint_name = kcu.constraint_name 
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu 
                ON ccu.constraint_name = tc.constraint_name 
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
        """)
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                fks = [
                    {
                        "schema_name": row[0],
                        "table_name": row[1],
                        "column_name": row[2],
                        "referenced_schema_name": row[3],
                        "referenced_table_name": row[4],
                        "referenced_column_name": row[5],
                    }
                    for row in result
                ]
                logger.info("Extracted {count} foreign keys", count=len(fks))
                return fks
        except Exception as e:
            logger.error("Failed to extract foreign keys: {error}", error=str(e))
            return []

    def sample_table_rows(
        self, schema: str, table: str, limit: int | None = 100
    ) -> list[dict[str, Any]]:
        """
        Fetches sample rows from both the beginning and the end of the table.
        Default limit is 100 per side (200 rows total).
        If limit is None, performs a FULL TABLE SCAN (unlimited).
        """
        schema_q = self._quote_ident(schema)
        table_q = self._quote_ident(table)
        table_ref = f"{schema_q}.{table_q}"

        if limit is None:
            # Stage 2: Full Scan as requested
            query_str = f"SELECT * FROM {table_ref}"
        elif self.db_type == "sqlserver":
            query_str = f"""
                SELECT * FROM (
                    SELECT TOP {limit} * FROM {table_ref} ORDER BY 1 ASC
                ) a
                UNION
                SELECT * FROM (
                    SELECT TOP {limit} * FROM {table_ref} ORDER BY 1 DESC
                ) b
            """
        else:
            query_str = f"""
                (SELECT * FROM {table_ref} ORDER BY 1 ASC LIMIT {limit})
                UNION
                (SELECT * FROM {table_ref} ORDER BY 1 DESC LIMIT {limit})
            """

        try:
            with self.engine.connect() as conn:
                # 30s timeout is safe for 2000 rows on most systems
                result = conn.execute(text(query_str).execution_options(timeout=30))
                rows = [dict(row._mapping) for row in result]

                if not rows:
                    fallback_limit = limit * 2
                    fallback = (
                        f"SELECT TOP {fallback_limit} * FROM {table_ref}"
                        if self.db_type == "sqlserver"
                        else f"SELECT * FROM {table_ref} LIMIT {fallback_limit}"
                    )
                    result = conn.execute(text(fallback).execution_options(timeout=20))
                    rows = [dict(row._mapping) for row in result]

                return rows
        except Exception as e:
            logger.warning(
                "Skipping unreadable table {schema}.{table} during sampling: {error}",
                schema=schema,
                table=table,
                error=str(e),
            )
            return []

    def _get_random_function(self) -> str:
        """Returns the appropriate random ordering function for the dialect."""
        if self.db_type == "mysql":
            return "RAND()"
        if self.db_type == "sqlserver":
            return "NEWID()"
        return "RANDOM()"

    def _is_meaningful_sample(self, val: Any) -> bool:
        """Determines if a sample value is meaningful enough to be included."""
        if val is None:
            return False
        return not (isinstance(val, str) and not val.strip())

    def _deduplicate_samples(self, values: list[Any]) -> list[Any]:
        """Filters empty values and deduplicates to avoid [0,0,0] and identicals."""
        filtered = [v for v in values if self._is_meaningful_sample(v)]

        distinct_vals = []
        for v in filtered:
            if v not in distinct_vals:
                distinct_vals.append(v)

        return distinct_vals[:3]

    def _quote_ident(self, ident: str) -> str:
        """Quote identifiers based on dialect."""
        if self.db_type == "mysql":
            return f"`{ident}`"
        if self.db_type == "sqlserver":
            return f"[{ident}]"
        return f'"{ident}"'

    def build_column_samples_from_rows(
        self, rows: list[dict[str, Any]], column_name: str
    ) -> list[Any]:
        """
        Extracts up to 3 distinct meaningful sample values for a column from a list of rows.
        Performed in memory to avoid extra SQL queries.
        """
        raw_values = []
        for row in rows:
            if column_name in row:
                raw_values.append(row[column_name])

        # Use existing deduplication and meaningful check logic
        samples = self._deduplicate_samples(raw_values)

        serializable_samples = []
        for val in samples:
            try:
                # Ensure it's JSON serializable
                json.dumps(val)
                serializable_samples.append(val)
            except (TypeError, ValueError):
                serializable_samples.append(str(val))

        return serializable_samples
