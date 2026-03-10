from ivanpham_chatbot_assistant.settings import settings

from .config import MAX_OVERFLOW, POOL_PRE_PING, POOL_RECYCLE, POOL_SIZE

# Database source configurations
DATABASES = {
    "system": {
        "type": "postgres",
        "url": str(settings.db_url),
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "pool_pre_ping": POOL_PRE_PING,
        "pool_recycle": POOL_RECYCLE,
    },
    "sql_source": {
        "type": "sqlserver",
        "host": settings.sql_source_host,
        "port": settings.sql_source_port,
        "user": settings.sql_source_user,
        "password": settings.sql_source_pass,
        "database": settings.sql_source_base,
        "driver": settings.sql_source_driver,
        "encrypt": settings.sql_source_encrypt,
        "trust_cert": settings.sql_source_trust_cert,
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "pool_pre_ping": POOL_PRE_PING,
        "pool_recycle": POOL_RECYCLE,
    },
}
