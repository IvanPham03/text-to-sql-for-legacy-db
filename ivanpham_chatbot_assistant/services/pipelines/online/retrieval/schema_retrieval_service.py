from typing import Any

from langchain_openai import OpenAIEmbeddings
from loguru import logger

from ivanpham_chatbot_assistant.services.vector_store.qdrant_service import (
    QdrantService,
)
from ivanpham_chatbot_assistant.settings import settings


class SchemaRetrievalService:
    """
    Service responsible for retrieving relevant schema elements (tables and columns)
    using semantic vector search. This is Phase 1 of the retrieval system.
    """

    def __init__(self, qdrant_service: QdrantService | None = None):
        self.qdrant_service = qdrant_service or QdrantService()
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key, model="text-embedding-3-small"
        )

    async def execute(self, question: str, limit: int = 15) -> dict[str, Any]:
        """
        Retrieves top K relevant schema components for a given natural language question.

        Logic:
        1. Embed the user question.
        2. Search Qdrant for semantic matches.
        3. Format and return payload metadata for downstream pipeline steps.
        """
        logger.info(
            f"Executing schema retrieval for question: '{question}' (limit={limit})"
        )

        try:
            # 1. Generate embedding for the question
            question_vector = await self.embeddings.aembed_query(question)

            # 2. Perform vector search in Qdrant
            # Each vector represents a column with its associated table context in the payload
            results = await self.qdrant_service.search_vectors(
                query_vector=question_vector, limit=limit
            )

            # 3. Extract and format payload metadata into compact JSON
            db_name = None
            table_groups = {}

            for res in results:
                payload = res.get("payload", {})
                t_name = payload.get("table")

                if not db_name and payload.get("database"):
                    db_name = payload.get("database")

                if t_name not in table_groups:
                    if len(table_groups) >= 5:  # Limit top 5 tables
                        continue
                    table_groups[t_name] = {
                        "schema": payload.get("schema"),
                        "table": t_name,
                        "columns": [],
                    }

                # Limit top 15 columns per table
                if len(table_groups[t_name]["columns"]) >= 15:
                    continue

                col_name = payload.get("column")
                # Avoid duplicate columns
                if any(c["name"] == col_name for c in table_groups[t_name]["columns"]):
                    continue

                col_data = {"name": col_name, "type": payload.get("data_type")}

                if payload.get("is_primary_key"):
                    col_data["pk"] = True
                if payload.get("is_foreign_key"):
                    col_data["fk"] = True

                table_groups[t_name]["columns"].append(col_data)

            retrieved_schema = {
                "database": db_name,
                "tables": list(table_groups.values()),
            }

            logger.info("Retrieved schema context: {}", retrieved_schema)
            logger.info(f"Retrieved {len(table_groups)} tables.")

            return {"status": "success", "retrieved_schema": retrieved_schema}

        except Exception as e:
            logger.error(f"Error during schema retrieval: {e}")
            return {"status": "error", "error": str(e), "retrieved_schema": {}}
