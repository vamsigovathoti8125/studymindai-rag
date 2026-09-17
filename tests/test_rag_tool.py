from src.tools.rag_tool import format_retrieved_chunks


def test_format_retrieved_chunks():
    chunks = [
        {"text": "First chunk text.", "source": "notes.pdf", "page": 1},
        {"text": "Second chunk text.", "source": "notes.pdf", "page": 2},
    ]
    formatted = format_retrieved_chunks(chunks)
    assert "notes.pdf - p.1" in formatted
    assert "notes.pdf - p.2" in formatted
    assert "First chunk text." in formatted
    assert "Second chunk text." in formatted
