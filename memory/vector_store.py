"""Lightweight vector store wrapper using local Qdrant."""
import logging
import uuid
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

logger = logging.getLogger(__name__)

COLLECTION = "assistant_memory"


class VectorStore:
    def __init__(self, collection_name: str = "conversations", dim: int = 384):
        self.client = QdrantClient(path="./qdrant_data")
        self.collection_name = collection_name
        # Create collection if it doesn't exist
        collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in collections:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def upsert(self, doc_id: str, vector: List[float], text: str) -> None:
        # Qdrant requires a valid UUID — strip any prefix and regenerate if needed
        try:
            clean_id = doc_id.replace("mem-", "")
            point_id = str(uuid.UUID(clean_id))
        except (ValueError, AttributeError):
            point_id = str(uuid.uuid4())

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={"text": text},
                    )
                ],
            )
        except Exception as exc:  # pylint: disable=broad-except
            import logging
            logging.getLogger(__name__).error("Vector upsert failed: %s", exc)

    def search(self, vector: List[float], top_k: int = 3) -> List[str]:
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=top_k,
            )
            return [hit.payload.get("text", "") for hit in results]
        except Exception:  # pylint: disable=broad-except
            return []
