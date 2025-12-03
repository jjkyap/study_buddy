# rag.py
"""
Lightweight RAG using sentence-transformers + scikit-learn.

- No external DB or chromadb
- Embeds notes with all-MiniLM-L6-v2
- Keeps vectors in memory for this session
- Uses cosine-similarity NearestNeighbors
"""

from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
import numpy as np

_model = SentenceTransformer("all-MiniLM-L6-v2")

_corpus_texts: List[str] = []
_corpus_ids: List[str] = []
_corpus_embeddings: np.ndarray | None = None
_nn: NearestNeighbors | None = None


def _rebuild_index():
    global _corpus_embeddings, _nn
    if not _corpus_texts:
        _corpus_embeddings = None
        _nn = None
        return

    _corpus_embeddings = _model.encode(_corpus_texts, convert_to_numpy=True)
    _nn = NearestNeighbors(
        n_neighbors=min(5, len(_corpus_texts)),
        metric="cosine"
    )
    _nn.fit(_corpus_embeddings)


def init_vector_store():
    """
    Kept for API compatibility with chromadb version.
    Nothing external to init; model loads at import time.
    """
    return None, None


def add_note_to_rag(note_id: str, text: str) -> None:
    global _corpus_texts, _corpus_ids
    _corpus_ids.append(note_id)
    _corpus_texts.append(text)
    _rebuild_index()


def query_context(query: str, k: int = 4) -> List[str]:
    """
    Returns up to k most similar note texts.
    If corpus is empty, returns [].
    """
    if _nn is None or _corpus_embeddings is None or not _corpus_texts:
        return []

    query_emb = _model.encode([query], convert_to_numpy=True)
    n_neighbors = min(k, len(_corpus_texts))
    distances, indices = _nn.kneighbors(query_emb, n_neighbors=n_neighbors)
    idxs = indices[0]
    return [_corpus_texts[i] for i in idxs]
