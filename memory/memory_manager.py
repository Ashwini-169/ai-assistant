"""Manages long-term memory storage and retrieval."""
import logging
import time
import uuid
from typing import List

from memory.embedding_model import embed
from memory.vector_store import VectorStore

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self) -> None:
        sample_vector = embed("warmup")
        self.store = VectorStore(dim=len(sample_vector))

    def _summarize(self, user_text: str, assistant_text: str) -> str:
        snippet_user = user_text[:200]
        snippet_assistant = assistant_text[:200]
        return f"User: {snippet_user}\nAssistant: {snippet_assistant}"

    def add_interaction(self, user_text: str, assistant_text: str) -> None:
        summary = self._summarize(user_text, assistant_text)
        vector = embed(summary)
        doc_id = str(uuid.uuid4())
        self.store.upsert(doc_id, vector, summary)
        logger.info("Stored memory %s", doc_id)

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        query_vec = embed(query)
        return self.store.search(query_vec, top_k=top_k)

    def format_memories(self, memories: List[str]) -> str:
        if not memories:
            return "(no long-term memories)"
        lines = [f"Memory {idx+1}: {mem}" for idx, mem in enumerate(memories)]
        return "\n".join(lines)
