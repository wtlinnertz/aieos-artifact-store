"""AIEOS Artifact Store — Embedding model wrapper.

Wraps sentence-transformers for vector generation. Swappable by changing
config.EMBEDDING_MODEL and running reindex.
"""

from functools import lru_cache
from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load the embedding model (cached after first call)."""
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (list of floats).
    """
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Generate embedding for a single query string.

    Args:
        query: Query text to embed.

    Returns:
        Single embedding vector.
    """
    model = get_model()
    embedding = model.encode(query, show_progress_bar=False)
    return embedding.tolist()
