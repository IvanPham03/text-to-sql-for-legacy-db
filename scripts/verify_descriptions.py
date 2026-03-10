import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ivanpham_chatbot_assistant.services.pipelines.offline.generate.pipeline import (
    DescriptionGenerationPipeline,
)
from ivanpham_chatbot_assistant.settings import settings


async def main():
    # Setup database connection manually for the script
    engine = create_async_engine(str(settings.db_url), echo=settings.db_echo)
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    # Usage: python verify_descriptions.py <db_name> <host>
    db_name = settings.sql_source_base
    host = settings.sql_source_host

    pipeline = DescriptionGenerationPipeline(session_factory)

    print(f"Running description generation for {db_name} at {host}...")
    result = await pipeline.run(db_name, host)

    if result == "success":
        print("✅ Semantic descriptions generated successfully.")
    else:
        print(f"❌ Generation failed: {result}")


if __name__ == "__main__":
    asyncio.run(main())
