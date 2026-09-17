import hashlib
import os
import json
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from src.gemini_client import EMBEDDING_DIMENSION, embed_texts

# Try to import FAISS, but fall back to simple implementation if not available
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


def _simple_local_embeddings(texts: List[str], dim: int = EMBEDDING_DIMENSION) -> List[List[float]]:
    """Generate deterministic local embeddings without external ML libraries."""
    embeddings = np.zeros((len(texts), dim), dtype=np.float32)
    for i, text in enumerate(texts):
        normalized_text = text.lower()
        for n in (3, 4, 5):
            for j in range(len(normalized_text) - n + 1):
                gram = normalized_text[j:j + n]
                idx = int(hashlib.sha256(gram.encode("utf-8")).hexdigest(), 16) % dim
                embeddings[i, idx] += 1.0
        norm = np.linalg.norm(embeddings[i])
        if norm > 0:
            embeddings[i] /= norm
    return [emb.tolist() for emb in embeddings]


def get_embeddings(texts: List[str], embedding_model: str = "gemini-embedding-2", local_model: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    """Return Gemini embeddings, falling back to deterministic local embeddings."""
    try:
        return embed_texts(texts, model=embedding_model)
    except Exception:
        return _simple_local_embeddings(texts)

    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(local_model)
        embs = model.encode(texts, convert_to_numpy=True)
        return [emb.astype("float32").tolist() for emb in embs]
    except Exception:
        return _simple_local_embeddings(texts)


class SimpleIndex:
    """Simple in-memory vector search index (fallback when FAISS not available)"""
    def __init__(self, embeddings: List[List[float]]):
        self.embeddings = np.array(embeddings, dtype=np.float32)
        self.dim = self.embeddings.shape[1] if len(self.embeddings) > 0 else EMBEDDING_DIMENSION
    
    def search(self, query: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Search for k nearest neighbors using cosine similarity"""
        if len(self.embeddings) == 0:
            return np.array([[]], dtype=np.int64), np.array([[]], dtype=np.float32)
        
        k = min(k, len(self.embeddings))
        
        # Compute cosine similarity
        query_norm = query / (np.linalg.norm(query, axis=1, keepdims=True) + 1e-8)
        embeddings_norm = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-8)
        similarities = np.dot(query_norm, embeddings_norm.T)[0]
        
        # Return top k (as distances: 1 - similarity)
        indices = np.argsort(-similarities)[:k]
        distances = (1 - similarities[indices]).astype(np.float32)
        return indices.reshape(1, -1).astype(np.int64), distances.reshape(1, -1)


def build_faiss_index(embeddings: List[List[float]]) -> Tuple[Any, int]:
    """Build a FAISS index or fallback to simple index"""
    arr = np.array(embeddings).astype("float32")
    dim = arr.shape[1]
    
    if FAISS_AVAILABLE:
        try:
            index = faiss.IndexFlatL2(dim)
            index.add(arr)
            return index, dim
        except Exception:
            # Fallback to simple index
            return SimpleIndex(embeddings), dim
    else:
        # Use simple index when FAISS not available
        return SimpleIndex(embeddings), dim


def save_index(index: Any, docs: List[Dict[str, Any]], path: str = "faiss_index.bin", docs_path: str = "docs.json") -> None:
    """Save index and documents"""
    try:
        if FAISS_AVAILABLE and hasattr(index, 'add'):  # It's a FAISS index
            import faiss
            faiss.write_index(index, path)
        else:
            # Save simple index as pickle
            import pickle
            with open(path, "wb") as f:
                pickle.dump(index, f)
    except Exception:
        pass  # Ignore save errors
    
    with open(docs_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False)


def load_index(path: str = "faiss_index.bin", docs_path: str = "docs.json") -> Tuple[Optional[Any], List[Dict[str, Any]]]:
    """Load index and documents"""
    if not os.path.exists(path) or not os.path.exists(docs_path):
        return None, []
    
    index = None
    try:
        if FAISS_AVAILABLE:
            try:
                import faiss
                index = faiss.read_index(path)
            except Exception:
                # Try loading as pickle (simple index)
                import pickle
                with open(path, "rb") as f:
                    index = pickle.load(f)
        else:
            # Load as pickle
            import pickle
            with open(path, "rb") as f:
                index = pickle.load(f)
    except Exception:
        index = None

    if index is not None:
        index_dimension = getattr(index, "d", getattr(index, "dim", None))
        if index_dimension != EMBEDDING_DIMENSION:
            index = None
    
    docs = []
    try:
        with open(docs_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
    except Exception:
        pass
    
    return index, docs


def search_index(index: Any, query_embedding: List[float], k: int = 4) -> Tuple[List[int], List[float]]:
    """Search index for k nearest neighbors"""
    if index is None:
        return [], []
    
    q = np.array([query_embedding]).astype("float32")
    
    if isinstance(index, SimpleIndex):
        # Use our simple index
        indices, distances = index.search(q, k)
        return indices[0].tolist(), distances[0].tolist()
    elif FAISS_AVAILABLE:
        # Use FAISS index
        try:
            distances, indices = index.search(q, k)
            return indices[0].tolist(), distances[0].tolist()
        except Exception:
            return [], []
    else:
        return [], []
