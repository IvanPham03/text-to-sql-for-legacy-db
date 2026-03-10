import enum
from pathlib import Path
from tempfile import gettempdir

from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL

TEMP_DIR = Path(gettempdir())


class LogLevel(enum.StrEnum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False

    # Current environment
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO
    # Variables for the database
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "ivanpham_chatbot_assistant"
    db_pass: str = "ivanpham_chatbot_assistant"
    db_base: str = "admin"
    db_echo: bool = False

    # OpenAI Configuration
    openai_api_key: str | None = None

    # Variables for the source SQL Database (e.g. SQL Server)
    sql_source_host: str = "localhost"
    sql_source_port: int = 1433
    sql_source_user: str = "sa"
    sql_source_pass: str = "password"
    sql_source_base: str = "master"
    sql_source_driver: str = "ODBC Driver 18 for SQL Server"
    sql_source_encrypt: str = "no"
    sql_source_trust_cert: str = "yes"

    # Qdrant Configuration
    qdrant_host: str = "ivanpham_chatbot_assistant-qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "schema_embeddings"
    qdrant_timeout: int = 60

    # Variables for Redis
    redis_host: str = "ivanpham_chatbot_assistant-redis"
    redis_port: int = 6379
    redis_user: str | None = None
    redis_pass: str | None = None
    redis_base: int | None = None

    # This variable is used to define
    # multiproc_dir. It's required for [uvi|guni]corn projects.
    prometheus_dir: Path = TEMP_DIR / "prom"

    # Sentry's configuration.
    sentry_dsn: str | None = None
    sentry_sample_rate: float = 1.0

    # Grpc endpoint for opentelemetry.
    # E.G. http://localhost:4317
    opentelemetry_endpoint: str | None = None

    @property
    def db_url(self) -> URL:
        """
        Assemble database URL from settings.

        :return: database URL.
        """
        return URL.build(
            scheme="postgresql+asyncpg",
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_pass,
            path=f"/{self.db_base}",
        )

    @property
    def redis_url(self) -> URL:
        """
        Assemble REDIS URL from settings.

        :return: redis URL.
        """
        path = ""
        if self.redis_base is not None:
            path = f"/{self.redis_base}"
        return URL.build(
            scheme="redis",
            host=self.redis_host,
            port=self.redis_port,
            user=self.redis_user,
            password=self.redis_pass,
            path=path,
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="IVANPHAM_CHATBOT_ASSISTANT_",
        env_file_encoding="utf-8",
    )


settings = Settings()
