from src.vectorstore import get_embeddings, build_faiss_index, search_index


def test_embeddings_and_faiss_local():
    texts = ["Machine learning is the study of algorithms.", "Supervised learning uses labels."]
    embs = get_embeddings(texts)
    assert len(embs) == 2
    index, dim = build_faiss_index(embs)
    # Query with the first text
    q_emb = embs[0]
    ids, distances = search_index(index, q_emb, k=2)
    assert len(ids) == 2
    assert ids[0] == 0
