from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ivanpham_chatbot_assistant.settings import settings

# Create engine and session factory for metadata DB
engine = create_async_engine(str(settings.db_url), echo=settings.db_echo)

session_factory = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db_session():
    """Dependency for getting an async database session."""
    async with session_factory() as session:
        yield session
