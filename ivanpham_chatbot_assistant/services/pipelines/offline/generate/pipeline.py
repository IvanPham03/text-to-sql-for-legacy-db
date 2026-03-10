import os
import random

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ivanpham_chatbot_assistant.db.models.column import Column
from ivanpham_chatbot_assistant.db.models.column_description import ColumnDescription
from ivanpham_chatbot_assistant.db.models.database import Database
from ivanpham_chatbot_assistant.db.models.schema import Schema
from ivanpham_chatbot_assistant.db.models.table import Table
from ivanpham_chatbot_assistant.db.models.table_description import TableDescription
from ivanpham_chatbot_assistant.log import logger
from ivanpham_chatbot_assistant.services.llm.llm_service import LLMService
from ivanpham_chatbot_assistant.services.pipelines.offline.generate.generator import (
    DescriptionGenerator,
)
from ivanpham_chatbot_assistant.settings import settings


class DescriptionGenerationPipeline:
    """
    Pipeline to batch generate semantic descriptions for all tables and columns
    in a given database index using an LLM.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory

        # Initialize LLM Service with default config from settings
        # This uses the existing LLMService infrastructure with fallbacks and metrics
        llm_config = {
            "providers": [
                {
                    "name": "openai",
                    "config": {
                        "api_key": settings.openai_api_key,
                        "model": "gpt-4o-mini",  # Lightweight yet capable for descriptions
                    },
                }
            ]
        }
        self.llm_service = LLMService(llm_config)

        # Templates are located in the local 'prompts/' directory
        templates_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self.generator = DescriptionGenerator(
            self.llm_service,
            templates_dir,
            max_concurrency=10,  # Reasonable concurrency for rate limits
        )

    async def run(self, table_names: list[str] | None = None, limit: int | None = None):
        """
        Runs the semantic description generation for the indexed database.
        Supports filtering by table names or limiting to a random subset of tables.
        """
        logger.info("Starting semantic description generation for the indexed database")

        async with self.session_factory() as session:
            # 1. Fetch the first available Database instance (since only one exists)
            stmt = select(Database).limit(1)
            result = await session.execute(stmt)
            db_instance = result.scalars().first()

            if not db_instance:
                logger.error("No database found in index. Run extraction first.")
                return "database_not_found"

            # 2. Fetch tables and columns for this database
            stmt = (
                select(Table)
                .join(Schema)
                .where(Schema.database_id == db_instance.id)
                .options(
                    selectinload(Table.columns).selectinload(Column.column_description),
                    selectinload(Table.table_description),
                )
            )

            # Apply name filter if provided
            if table_names:
                stmt = stmt.where(Table.name.in_(table_names))

            result = await session.execute(stmt)
            tables = result.scalars().all()

            # Apply limit/randomization only if table_names is NOT provided (as per user request)
            # "if giving a number (limit) without a specific table (table_names) then random"
            if limit and not table_names:
                random.shuffle(tables)
                tables = tables[:limit]
            elif limit and table_names:
                # If both are provided, we just take the first N of the requested tables
                tables = tables[:limit]

            logger.info(f"Targeting {len(tables)} tables for semantic analysis.")

            for table in tables:
                try:
                    # 2.1 Prepare column context for LLM
                    cols_data = [
                        {
                            "name": col.name,
                            "data_type": col.data_type,
                            "sample_values": col.sample_values,
                        }
                        for col in table.columns
                    ]

                    # 2.2 Inference Stage 1: Table Description
                    # Understanding the aggregate purpose of the table first
                    generated_table_desc = (
                        await self.generator.generate_table_description(
                            table.name, cols_data
                        )
                    )

                    # 2.3 Inference Stage 2: Column Descriptions
                    # Understanding each column using its data + table purpose
                    col_desc_map = await self.generator.generate_column_descriptions(
                        table.name, generated_table_desc, cols_data
                    )

                    # 2.4 Update semantic description models
                    if not table.table_description:
                        table.table_description = TableDescription(table_id=table.id)
                    table.table_description.summary = generated_table_desc

                    for col in table.columns:
                        desc = col_desc_map.get(col.name)
                        if not col.column_description:
                            col.column_description = ColumnDescription(column_id=col.id)
                        col.column_description.summary = desc

                    await session.commit()  # Commit per table for robustness
                    logger.info(
                        f"Semantic descriptions persisted for table: {table.name}"
                    )
                except Exception as e:
                    await session.rollback()
                    logger.error(
                        f"Failed to generate/persist descriptions for table {table.name}: {e}"
                    )

            logger.info("Semantic description augmentation completed.")
            return "success"
