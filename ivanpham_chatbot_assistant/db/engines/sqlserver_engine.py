from typing import Any, Dict
import urllib
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from .base_engine import BaseEngine


class SQLServerEngine(BaseEngine):
    """
    Implementation for SQL Server engine creation.
    """

    def create_engine(self, config: Dict[str, Any]) -> Engine:
        """
        Create SQLAlchemy engine instance for SQL Server.

        :param config: Dictionary containing database configuration.
        :return: SQLAlchemy Engine instance.
        """
        url = config.get("url")
        if not url:
            # Construct URL from components if not provided directly
            host = config.get("host")
            port = config.get("port", 1433)
            user = config.get("user")
            password = config.get("password")
            database = config.get("database")
            driver = config.get("driver", "ODBC Driver 18 for SQL Server")
            encrypt = config.get("encrypt", "no")
            trust_cert = config.get("trust_cert", "yes")

            params = urllib.parse.quote_plus(
                f"DRIVER={{{driver}}};SERVER={host},{port};DATABASE={database};UID={user};PWD={password};Encrypt={encrypt};TrustServerCertificate={trust_cert}"
            )
            url = f"mssql+pyodbc:///?odbc_connect={params}"

        return create_engine(
            url,
            pool_size=config.get("pool_size", 10),
            max_overflow=config.get("max_overflow", 20),
            pool_pre_ping=config.get("pool_pre_ping", True),
            pool_recycle=config.get("pool_recycle", 1800),
        )
