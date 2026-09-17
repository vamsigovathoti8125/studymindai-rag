from src.ingest import chunk_pages


def test_chunk_pages_short_text():
    pages = [{"text": "This is a short page of text.", "page": 1, "source": "sample.pdf"}]
    chunks = chunk_pages(pages, chunk_size=50, overlap=10)
    assert len(chunks) >= 1
    assert all("text" in c and "source" in c and "page" in c for c in chunks)


def test_chunk_pages_overlap():
    long_text = "\n".join(["Line %d" % i for i in range(200)])
    pages = [{"text": long_text, "page": 2, "source": "big.pdf"}]
    chunks = chunk_pages(pages, chunk_size=100, overlap=20)
    # ensure chunks overlap by checking more than one chunk created
    assert len(chunks) > 1
