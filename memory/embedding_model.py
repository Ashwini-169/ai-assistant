"""CPU-only embedding model loader using sentence-transformers."""
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    # Force CPU to avoid competing with GPU workloads
    return SentenceTransformer(MODEL_NAME, device="cpu")


def embed(text: str) -> List[float]:
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()
