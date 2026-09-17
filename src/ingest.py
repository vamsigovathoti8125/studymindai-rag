import fitz
from typing import List, Dict, Any


def extract_pages_from_pdf(pdf_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """Extract text per page and return list of dicts with metadata.

    Each item: {"text": str, "page": int, "source": filename}
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append({
            "text": text,
            "page": i + 1,
            "source": filename
        })
    return pages


def chunk_pages(pages: List[Dict[str, Any]], chunk_size: int = 800, overlap: int = 150) -> List[Dict[str, Any]]:
    """Chunk page texts into overlapping chunks while preserving metadata.

    Returns list of dicts: {"text": chunk_text, "source": filename, "page": page_number}
    """
    chunks = []
    for page in pages:
        text = page.get("text", "").strip()
        start = 0
        length = len(text)
        while start < length:
            end = start + chunk_size
            snippet = text[start:end].strip()
            if snippet:
                chunks.append({
                    "text": snippet,
                    "source": page.get("source"),
                    "page": page.get("page")
                })
            if end >= length:
                break
            start = end - overlap
    return chunks

