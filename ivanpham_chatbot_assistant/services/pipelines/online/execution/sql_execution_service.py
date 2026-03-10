import decimal
from datetime import date, datetime, time
from typing import Any, Dict, List, Union

from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Engine

from ivanpham_chatbot_assistant.db.factory.engine_factory import create_engine_by_type


class SqlExecutionService:
    """
    Service responsible for executing validated SQL queries against the source database.
    Implements production guardrails like row limits and query timeouts.
    """

    DEFAULT_ROW_LIMIT = 100
    DEFAULT_TIMEOUT_SECONDS = 5

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize with source database configuration.
        """
        self.db_type = db_config.get("db_type", "postgres").lower()
        
        # Build URL if missing, similar to SchemaCrawlerService logic
        if "url" not in db_config:
            host = db_config.get("host", "localhost")
            port = db_config.get("port")
            user = db_config.get("user", "")
            password = db_config.get("password", "")
            database = db_config.get("database", "")
            
            if self.db_type in ["postgres", "postgresql"]:
                port_str = f":{port}" if port else ":5432"
                db_config["url"] = f"postgresql://{user}:{password}@{host}{port_str}/{database}"
            elif self.db_type == "mysql":
                port_str = f":{port}" if port else ":3306"
                db_config["url"] = f"mysql+pymysql://{user}:{password}@{host}{port_str}/{database}"
            elif self.db_type == "sqlserver":
                # SQL Server often uses a connection string or specific parameters in config
                # The SQLServerEngine usually handles its own URL if not provided, 
                # but we'll let the factory/engine handle it or expect it in config.
                pass

        self.engine = create_engine_by_type(self.db_type, db_config)
        logger.info(f"Initialized SqlExecutionService for {self.db_type} source database.")

    async def execute(
        self, 
        sql: str, 
        limit: int | None = DEFAULT_ROW_LIMIT, 
        timeout: int = DEFAULT_TIMEOUT_SECONDS
    ) -> Dict[str, Any]:
        """
        Executes a validated SQL query against the source database.
        
        :param sql: The SQL query string (already validated).
        :param limit: Maximum number of rows to return.
        :param timeout: Maximum execution time in seconds.
        :return: A dictionary containing status and result data.
        """
        logger.info(f"Executing SQL query on {self.db_type}")

        try:
            # 1. Apply safety guardrails (Row Limit)
            guarded_sql = self._apply_row_limit(sql, limit)

            # 2. Execute with timeout
            # Note: SQLAlchemy Engine is synchronous by default in our current setup.
            # Using connect() as a context manager ensures cleanup.
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(guarded_sql).execution_options(timeout=timeout)
                )
                
                # 3. Fetch and normalize results
                rows = [dict(row._mapping) for row in result]
                normalized_data = self._normalize_results(rows)

                logger.info(f"Query executed successfully, returned {len(normalized_data)} rows.")
                return {
                    "status": "success",
                    "data": normalized_data,
                    "row_count": len(normalized_data)
                }

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {
                "status": "error",
                "message": f"Query execution failed: {str(e)}",
                "data": None
            }

    def _apply_row_limit(self, sql: str, limit: int | None) -> str:
        """Appends a LIMIT/TOP clause to the SQL if not already present."""
        if limit is None:
            return sql

        upper_sql = sql.upper().strip().rstrip(";")
        
        # Basic check to avoid double limits
        if " LIMIT " in upper_sql or " TOP " in upper_sql:
            return sql + ";"

        if self.db_type == "sqlserver":
            # Simple injection for TOP if it starts with SELECT
            if upper_sql.startswith("SELECT DISTINCT"):
                 return f"SELECT DISTINCT TOP {limit}" + sql[15:] + ";"
            if upper_sql.startswith("SELECT"):
                 return f"SELECT TOP {limit}" + sql[6:] + ";"
        else:
            # Postgres/MySQL/SQLite use LIMIT at the end
            return f"{sql.strip().rstrip(';')} LIMIT {limit};"
            
        return sql + ";"

    def _normalize_results(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts database-specific types (Decimal, datetime) to JSON-safe formats."""
        normalized = []
        for row in rows:
            clean_row = {}
            for key, val in row.items():
                if isinstance(val, (datetime, date, time)):
                    clean_row[key] = val.isoformat()
                elif isinstance(val, decimal.Decimal):
                    clean_row[key] = float(val)
                elif isinstance(val, (bytes, bytearray)):
                    clean_row[key] = "<binary data>"
                else:
                    clean_row[key] = val
            normalized.append(clean_row)
        return normalized
