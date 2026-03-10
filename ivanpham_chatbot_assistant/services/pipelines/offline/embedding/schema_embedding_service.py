import time
import uuid

from langchain_openai import OpenAIEmbeddings
from loguru import logger

from ivanpham_chatbot_assistant.services.vector_store.qdrant_service import QdrantService
from ivanpham_chatbot_assistant.settings import settings
from ivanpham_chatbot_assistant.web.metrics.schema_sync_metrics import schema_embedding_latency


class SchemaEmbeddingService:
    """
    Service responsible for converting extracted schema metadata into
    vector embeddings for semantic retrieval.
    """

    def __init__(self):
        self.qdrant_service = QdrantService()
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model="text-embedding-3-small"
        )

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a batch of strings."""
        if not texts:
            return []

        start_time = time.perf_counter()
        try:
            vectors = await self.embeddings.aembed_documents(texts)
            latency = time.perf_counter() - start_time
            schema_embedding_latency.observe(latency)
            return vectors
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def execute(self, schema_data: dict) -> dict:
        """
        Processes schema data and generates column-centric embeddings.
        Each vector represents ONE column.
        """
        all_columns_to_sync = []

        # Flatten hierarchy into a list of column-centric sync items
        for table in schema_data.get("tables", []):
            table_info = {
                "id": table.get("id"),
                "name": table.get("name"),
                "summary": table.get("description"),
                "database": table.get("database_name"),
                "schema": table.get("schema_name"),
            }
            
            for col in table.get("columns", []):
                all_columns_to_sync.append({
                    "table": table_info,
                    "column": col
                })

        if not all_columns_to_sync:
            return {"status": "success", "embeddings_stored": 0}

        points_to_upsert = []
        batch_size = 20 # OpenAI optimal batch size for small texts
        upsert_threshold = 100 # Flush to Qdrant when we reach this many points
        total_upserted = 0
        
        for i in range(0, len(all_columns_to_sync), batch_size):
            batch = all_columns_to_sync[i : i + batch_size]
            
            texts_to_embed = [
                self._build_document(item["table"], item["column"])
                for item in batch
            ]
            
            vectors = await self.embed_batch(texts_to_embed)
            
            for j, vector in enumerate(vectors):
                item = batch[j]
                payload = self._build_payload(item["table"], item["column"])
                
                # Deterministic ID based on schema hierarchy
                vector_id = item["column"].get("vector_id") or str(uuid.uuid4())
                
                points_to_upsert.append({
                    "id": vector_id,
                    "vector": vector,
                    "payload": payload
                })
                
            # Flush points to Qdrant if threshold is reached
            if len(points_to_upsert) >= upsert_threshold:
                logger.info(f"Flushing {len(points_to_upsert)} column vectors to Qdrant (saving memory)...")
                await self.qdrant_service.upsert_vectors(points_to_upsert, batch_size=upsert_threshold)
                total_upserted += len(points_to_upsert)
                points_to_upsert = []

        # Flush any remaining points
        if points_to_upsert:
            logger.info(f"Flushing final {len(points_to_upsert)} column vectors to Qdrant...")
            await self.qdrant_service.upsert_vectors(points_to_upsert, batch_size=upsert_threshold)
            total_upserted += len(points_to_upsert)

        return {"status": "success", "embeddings_stored": total_upserted}

    def _build_document(self, table: dict, column: dict) -> str:
        """Builds a structured semantic document for a single column."""
        table_summary = table.get("summary") or "No summary available."
        col_summary = column.get("description") or "No summary available."
        
        sample_values = column.get("sample_values") or []
        samples_str = "\n".join([f"* {v}" for v in sample_values[:3]]) if sample_values else "No sample values."
        
        document = f"""DATABASE: {table.get('database')}
SCHEMA: {table.get('schema')}

TABLE: {table.get('name')}
TABLE_SUMMARY: {table_summary}

COLUMN: {column.get('name')}
TYPE: {column.get('data_type')}
NULLABLE: {column.get('is_nullable', True)}

COLUMN_SUMMARY: {col_summary}
BUSINESS_MEANING: {column.get('business_meaning') or col_summary}

SAMPLE_VALUES:
{samples_str}

DISTINCT_COUNT: {column.get('distinct_count') or 'N/A'}
"""
        return document.strip()

    def _build_payload(self, table: dict, column: dict) -> dict:
        """Builds the structured payload for Qdrant filtering and ranking."""
        return {
            "database": table.get("database"),
            "schema": table.get("schema"),
            "table": table.get("name"),
            "column": column.get("name"),
            "data_type": column.get("data_type"),
            "table_summary": table.get("summary"),
            "column_summary": column.get("description"),
            "business_meaning": column.get("business_meaning") or column.get("description"),
            "is_primary_key": column.get("is_primary_key", False),
            "is_foreign_key": column.get("is_foreign_key", False),
            "source_id": str(column.get("id", ""))
        }
