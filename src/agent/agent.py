import re
from typing import Tuple
from src.gemini_client import generate_text


def decide_tool(question: str) -> str:
    """Small heuristic + fallback LLM classifier to pick a tool.

    Returns: 'calculator', 'quiz', 'summary', or 'rag'
    """
    q = question.lower().strip()
    # Heuristic: math-like
    if re.fullmatch(r"[0-9\s\+\-\*/\(\)\.]+", q):
        return "calculator"

    if any(k in q for k in ["quiz", "mcq", "multiple choice", "questions"]):
        return "quiz"

    if any(k in q for k in ["summarize", "summary", "summarise", "recap"]):
        return "summary"

    # Fallback: short LLM classifier
    try:
        prompt = (
            "Classify the user's intent into one of: calculator, quiz, summary, rag. "
            f"Question: {question}\n\nRespond with only the label."
        )
        label = generate_text(prompt, max_output_tokens=10).lower()
        if label in ("calculator", "quiz", "summary", "rag"):
            return label
    except Exception:
        pass

    return "rag"
