from sqlalchemy.engine import Engine
from .pool.pool_manager import pool_manager
from .registry import DATABASES
from .factory.engine_factory import create_engine_by_type


def init_db_engines():
    """
    Initialize and register all database engines defined in registry.
    """
    for name, config in DATABASES.items():
        db_type = config.get("type")
        engine = create_engine_by_type(db_type, config)
        pool_manager.register(name, engine)


def get_engine(name: str) -> Engine:
    """
    Retrieve a database engine by name from the pool manager.

    :param name: Name of the database source.
    :return: SQLAlchemy Engine instance.
    """
    return pool_manager.get_engine(name)
