from typing import List, Dict, Any, Optional
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter
from tenacity import retry, stop_after_attempt, wait_fixed, before_sleep_log
import logging

from ivanpham_chatbot_assistant.settings import settings
from ivanpham_chatbot_assistant.utils.batching import batched


class QdrantService:
    """Service to interact with Qdrant vector database."""

    def __init__(self):
        try:
            self.client = AsyncQdrantClient(
                host=settings.qdrant_host, 
                port=settings.qdrant_port,
                timeout=settings.qdrant_timeout
            )
            self.collection_name = settings.qdrant_collection
            # We don't call _ensure_collection_exists here as it is async now
        except Exception as e:
            logger.error(f"Failed to initialize QdrantClient: {e}")
            self.client = None

    async def _ensure_collection_exists(self, vector_size: int = 1536):
        """Creates the collection if it does not exist already."""
        if not self.client:
            return
        
        try:
            collections_response = await self.client.get_collections()
            collections = collections_response.collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection exists: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def _upsert_batch(self, points: List[PointStruct]) -> None:
        """Upserts a single batch of points with retry logic."""
        if not self.client:
            raise ValueError("QdrantClient is not initialized")
            
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    async def upsert_vectors(self, points: List[Dict[str, Any]], batch_size: int = 100):
        """
        Upserts vectors into Qdrant in batches.
        Expected format of points: [{"id": str, "vector": List[float], "payload": dict}]
        """
        if not self.client:
            logger.error("QdrantClient is not initialized")
            return

        try:
            await self._ensure_collection_exists() # Ensure collection exists before upsert
            
            qdrant_points = [
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
                for point in points
            ]
            
            total_points = len(qdrant_points)
            batches = list(batched(qdrant_points, batch_size))
            total_batches = len(batches)
            
            logger.info(f"Starting batched upsert of {total_points} points in {total_batches} batches...")
            
            for idx, batch in enumerate(batches, 1):
                logger.info(f"Upserting batch {idx}/{total_batches} ({len(batch)} vectors)")
                await self._upsert_batch(list(batch))
                
            logger.info(f"Successfully upserted {total_points} vectors to {self.collection_name}")
        except Exception as e:
            logger.error(f"Error upserting vectors to Qdrant: {e}")
            raise

    async def search_vectors(
        self, 
        query_vector: List[float], 
        limit: int = 5, 
        query_filter: Optional[Filter] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches for the nearest vectors in Qdrant.
        """
        if not self.client:
             logger.error("QdrantClient is not initialized")
             return []

        try:
            search_result = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                query_filter=query_filter
            )
            
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in search_result.points
            ]
        except Exception as e:
            logger.error(f"Error searching vectors in Qdrant: {e}")
            return []

    async def delete_vectors(self, point_ids: List[str]):
        """
        Deletes vectors by IDs from Qdrant.
        """
        if not self.client:
             return
             
        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids
            )
            logger.info(f"Deleted {len(point_ids)} vectors from {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting vectors from Qdrant: {e}")
            raise
