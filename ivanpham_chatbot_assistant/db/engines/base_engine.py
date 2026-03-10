from abc import ABC, abstractmethod
from typing import Any, Dict
from sqlalchemy.engine import Engine


class BaseEngine(ABC):
    """
    Base interface for database engine creation.
    """

    @abstractmethod
    def create_engine(self, config: Dict[str, Any]) -> Engine:
        """
        Create SQLAlchemy engine instance.

        :param config: Dictionary containing database configuration.
        :return: SQLAlchemy Engine instance.
        """
        pass
