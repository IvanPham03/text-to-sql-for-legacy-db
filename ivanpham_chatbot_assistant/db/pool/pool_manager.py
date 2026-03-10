from sqlalchemy.engine import Engine


class PoolManager:
    """
    Manager class that stores and retrieves database engines.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.engines = {}
        return cls._instance

    def register(self, name: str, engine: Engine):
        """
        Register a database engine.

        :param name: Name of the database source.
        :param engine: SQLAlchemy Engine instance.
        """
        self.engines[name] = engine

    def get_engine(self, name: str) -> Engine:
        """
        Retrieve engine by name.

        :param name: Name of the database source.
        :return: SQLAlchemy Engine instance.
        """
        engine = self.engines.get(name)
        if engine is None:
            raise ValueError(f"No database engine registered with name: {name}")
        return engine


pool_manager = PoolManager()
