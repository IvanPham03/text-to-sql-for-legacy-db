from typing import Any

from sqlalchemy.engine import Engine

from ..engines.mysql_engine import MySQLEngine
from ..engines.postgres_engine import PostgresEngine
from ..engines.sqlserver_engine import SQLServerEngine


def create_engine_by_type(db_type: str, config: dict[str, Any]) -> Engine:
    """
    Factory function to create the correct engine based on database type.

    :param db_type: Type of the database (postgres, mysql, sqlserver).
    :param config: Configuration dictionary.
    :return: SQLAlchemy Engine instance.
    """
    db_type = db_type.lower()

    if db_type == "postgres":
        return PostgresEngine().create_engine(config)

    if db_type == "mysql":
        return MySQLEngine().create_engine(config)

    if db_type == "sqlserver":
        return SQLServerEngine().create_engine(config)

    raise ValueError(f"Unsupported database type: {db_type}")
