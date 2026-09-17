"""Run a small smoke test of ingestion -> chunking -> embeddings -> FAISS search.

This script intentionally uses local fallback embeddings when OpenAI key isn't set.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest import chunk_pages
from src.vectorstore import get_embeddings, build_faiss_index, search_index


def main():
    # Create synthetic page
    page = {
        "text": (
            "Machine learning models can overfit when they memorize training examples instead of learning general patterns. "
            "Supervised learning uses labeled data for training."
        ),
        "page": 1,
        "source": "test_doc.pdf",
    }

    chunks = chunk_pages([page], chunk_size=120, overlap=30)
    texts = [c["text"] for c in chunks]
    embeddings = get_embeddings(texts)
    index, dim = build_faiss_index(embeddings)
    q_emb = get_embeddings(["What is supervised learning?"])[0]
    ids, distances = search_index(index, q_emb, k=2)
    print("Chunk count:", len(chunks))
    print("Top ids:", ids)


if __name__ == "__main__":
    main()
