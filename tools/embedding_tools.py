"""
Embedding tools — uses all-MiniLM-L6-v2 for lightweight CPU-based embeddings.
Integrates with ChromaDB for persistent vector storage.
"""
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Use the project-local Hugging Face cache instead of the system-wide Windows cache,
# which often causes permission issues in shared/dev environments.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HF_HOME = PROJECT_ROOT / "data" / "hf_cache"
HF_HOME.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(HF_HOME))
os.environ.setdefault("HF_HUB_CACHE", str(HF_HOME / "hub"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(HF_HOME / "transformers"))

# Global model singleton (loaded once, ~80MB)
_model = None


def _get_model():
    """Lazy-load the sentence-transformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading all-MiniLM-L6-v2 embedding model (~80MB)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embedding model loaded.")
    return _model


def embed_text(text: str) -> list[float]:
    """Generate a 384-dimensional embedding for a single text."""
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Batch-embed multiple texts for efficiency."""
    model = _get_model()
    embeddings = model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
    return embeddings.tolist()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two normalized vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b))


def cosine_similarity_batch(vec_a: list[float], vecs_b: list[list[float]]) -> list[float]:
    """Compute cosine similarity between one vector and a batch of vectors."""
    a = np.array(vec_a)
    b = np.array(vecs_b)
    return (b @ a).tolist()


# ── ChromaDB Integration ──

_chroma_client = None
_chroma_collection = None


def _get_chroma_collection(persist_dir: str = "data/chroma_db"):
    """Get or create the ChromaDB collection."""
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        import chromadb
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
        _chroma_collection = _chroma_client.get_or_create_collection(
            name="resume_embeddings",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB collection ready at {persist_dir}")
    return _chroma_collection


def store_embedding(
    doc_id: str,
    text: str,
    embedding: list[float],
    metadata: Optional[dict] = None,
    persist_dir: str = "data/chroma_db",
):
    """Store an embedding in ChromaDB."""
    collection = _get_chroma_collection(persist_dir)
    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata or {}],
    )


def query_similar(
    query_embedding: list[float],
    n_results: int = 10,
    persist_dir: str = "data/chroma_db",
) -> list[dict]:
    """Query ChromaDB for similar documents."""
    collection = _get_chroma_collection(persist_dir)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    return [
        {
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "distance": results["distances"][0][i] if results["distances"] else None,
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
        }
        for i in range(len(results["ids"][0]))
    ]
