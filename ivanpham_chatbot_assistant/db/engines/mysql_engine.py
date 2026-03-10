from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .base_engine import BaseEngine


class MySQLEngine(BaseEngine):
    """
    Implementation for MySQL engine creation.
    """

    def create_engine(self, config: dict[str, Any]) -> Engine:
        """
        Create SQLAlchemy engine instance for MySQL.

        :param config: Dictionary containing database configuration.
        :return: SQLAlchemy Engine instance.
        """
        url = config.get("url")
        if not url:
            raise ValueError("MySQL connection URL is required")

        return create_engine(
            url,
            pool_size=config.get("pool_size", 10),
            max_overflow=config.get("max_overflow", 20),
            pool_pre_ping=config.get("pool_pre_ping", True),
            pool_recycle=config.get("pool_recycle", 1800),
        )
