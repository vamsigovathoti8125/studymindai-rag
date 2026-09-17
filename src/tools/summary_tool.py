from src.gemini_client import CHAT_MODEL, generate_text


def generate_summary(context: str, model: str = CHAT_MODEL) -> str:
    prompt = (
        "Summarize the following content in a concise and clear way, focusing on the main ideas and key points. "
        "Return the summary as a short paragraph.\n\n"
        f"Context:\n{context}\n\n"
    )

    return generate_text(prompt, model=model, max_output_tokens=500)
