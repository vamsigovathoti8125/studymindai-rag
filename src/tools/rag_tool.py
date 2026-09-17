from typing import List, Dict


def format_retrieved_chunks(chunks: List[Dict]) -> str:
    """Turn retrieved chunk dicts into a single context string with citations."""
    parts = []
    for c in chunks:
        src = f"{c.get('source')} - p.{c.get('page')}"
        parts.append(f"[{src}]\n{c.get('text')}")
    return "\n\n---\n\n".join(parts)
