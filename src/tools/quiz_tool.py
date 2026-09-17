from src.gemini_client import CHAT_MODEL, generate_text


def generate_mcqs(context: str, num_questions: int = 5, model: str = CHAT_MODEL) -> str:
    prompt = (
        f"Generate {num_questions} multiple-choice questions (with answers) based on the following context. "
        "Be concise and prefix each question with its number.\n\n"
        f"Context:\n{context}\n\n"
    )

    return generate_text(prompt, model=model, max_output_tokens=800)
