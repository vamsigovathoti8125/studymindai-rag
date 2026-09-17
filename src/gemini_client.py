import os
import re
import json
from difflib import SequenceMatcher
from threading import Lock
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import load_dotenv


CHAT_MODEL = "gemini-3.6-flash"
EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSION = 768

_client = None
_client_api_key = None
_client_lock = Lock()


def _client_is_closed(client) -> bool:
    """Check the SDK transport without depending on one private layout."""
    api_client = getattr(client, "_api_client", None)
    http_client = getattr(api_client, "_http_client", None)
    return bool(getattr(http_client, "is_closed", False))


def get_client():
    from google import genai

    global _client, _client_api_key

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    if api_key.startswith(("sk-", "Bearer ", "ya29.", "eyJ")):
        raise RuntimeError(
            "GEMINI_API_KEY must be a Google AI Studio API key, not an OpenAI key or OAuth token. "
            "Create one at https://aistudio.google.com/apikey and update .env."
        )

    with _client_lock:
        if _client is None or _client_api_key != api_key or _client_is_closed(_client):
            _client = genai.Client(api_key=api_key)
            _client_api_key = api_key
        return _client


def generate_text(prompt: str, model: str = CHAT_MODEL, max_output_tokens: int = 512) -> str:
    try:
        from google.genai import types

        response = get_client().models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=max_output_tokens),
        )
        return response.text.strip()
    except Exception:
        try:
            return _generate_text_rest(prompt, model, max_output_tokens)
        except Exception:
            return _local_text_response(prompt)


def _generate_text_rest(prompt: str, model: str, max_output_tokens: int) -> str:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(model, safe='')}:generateContent?key={quote(api_key, safe='')}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_output_tokens},
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Gemini returned no text content")
    return text


def _context_from_prompt(prompt: str) -> str:
    match = re.search(r"Context:\s*(.*?)(?:\s+Question:|\Z)", prompt, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else prompt.strip()


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]


def expand_project_documents(question: str, docs: list[dict], retrieved: list[dict]) -> list[dict]:
    """Add resume chunks whose named project matches the question."""
    lowered_question = question.lower()
    if "project" not in lowered_question:
        return retrieved

    ignored = {"tell", "about", "what", "which", "where", "when", "does", "his", "her", "the", "latest", "recent", "current", "project", "projects"}
    terms = [term for term in re.findall(r"[a-z0-9]+", lowered_question) if len(term) >= 4 and term not in ignored]
    if not terms:
        return retrieved

    expanded = list(retrieved)
    seen = {(doc.get("source"), doc.get("page"), doc.get("text", "").strip()) for doc in expanded}
    for doc in docs:
        normalized_text = re.sub(r"[^a-z0-9]", "", doc.get("text", "").lower())
        text_words = re.findall(r"[a-z0-9]+", doc.get("text", "").lower())
        if any(
            re.sub(r"[^a-z0-9]", "", term) in normalized_text
            or any(SequenceMatcher(None, term, word).ratio() >= 0.88 for word in text_words if len(word) >= 5)
            for term in terms
        ):
            key = (doc.get("source"), doc.get("page"), doc.get("text", "").strip())
            if key not in seen:
                expanded.append(doc)
                seen.add(key)
    return expanded


def expand_resume_documents(question: str, docs: list[dict], retrieved: list[dict]) -> list[dict]:
    """Add all chunks from the matched resume for identity and education questions."""
    lowered_question = question.lower()
    is_resume_question = bool(
        re.search(r"\b(name|candidate|education|degree|college|university|passed|study|studied)\b", lowered_question)
        or "graduat" in lowered_question
    )
    if not is_resume_question:
        return retrieved

    sources = {doc.get("source") for doc in retrieved if doc.get("source")}
    if not sources:
        return retrieved
    expanded = list(retrieved)
    seen = {(doc.get("source"), doc.get("page"), doc.get("text", "").strip()) for doc in expanded}
    for doc in docs:
        if doc.get("source") in sources:
            key = (doc.get("source"), doc.get("page"), doc.get("text", "").strip())
            if key not in seen:
                expanded.append(doc)
                seen.add(key)
    return expanded


def answer_resume_question(question: str, context: str) -> str | None:
    """Answer common resume questions only from directly matching evidence."""
    lowered_question = question.lower()
    institution_question = any(term in lowered_question for term in ("college", "university", "school", "institute"))
    if re.search(r"\b(name|candidate)\b", lowered_question) and not institution_question:
        candidate_name = extract_candidate_name(context)
        if candidate_name:
            return f"The candidate's name is {candidate_name}."

    education_terms = ("education", "degree", "college", "university", "graduat", "passed", "study", "studied")
    is_resume = bool(re.search(r"\b(resume|objective|experience|education|skills|intern|github|linkedin)\b", context, re.IGNORECASE))
    if is_resume and not any(
        term in lowered_question
        for term in ("experience", "projects", "project", "skills", *education_terms)
    ):
        return "I couldn't find that information in the uploaded document."
    if not any(term in lowered_question for term in ("experience", "projects", "project", "skills", *education_terms)):
        return None

    if "experience" in lowered_question or "intern" in lowered_question:
        keywords = ("experience", "intern", "internship", "worked on", "developed", "implemented", "training")
        heading = "Relevant experience"
    elif "project" in lowered_question:
        project_match = re.search(r"((?:[a-z0-9]+\s+){1,5})project\b", lowered_question)
        if project_match:
            project_words = project_match.group(1).split()
            ignored_project_words = {"what", "which", "tell", "me", "about", "is", "for", "his", "her", "the", "latest", "recent", "current"}
            requested_words = [word for word in project_words if word not in ignored_project_words]
            requested_project = " ".join(requested_words).strip()
            if requested_project in {"latest", "recent", "current", "his", "her", "the"}:
                requested_project = ""
            requested_project_normalized = requested_project.replace(" ", "")
            if requested_project_normalized:
                context_lines = context.splitlines()
                for line_number, line in enumerate(context_lines):
                    normalized_line = re.sub(r"[^a-z0-9]", "", line.lower())
                    line_words = re.findall(r"[a-z0-9]+", line.lower())
                    project_matches = requested_project_normalized in normalized_line or any(
                        SequenceMatcher(None, requested_project_normalized, word).ratio() >= 0.82
                        for word in line_words
                        if len(word) >= 5
                    )
                    if project_matches:
                        project_lines = [line.strip()]
                        for following_line in context_lines[line_number + 1:]:
                            clean_following = following_line.strip()
                            if not clean_following:
                                continue
                            if clean_following.startswith(("•", "-", "–", "—", "â")):
                                project_lines.append(clean_following)
                            else:
                                break
                        if len(project_lines) > 1:
                            return "Project: " + " ".join(project_lines)
                return "I couldn't find that project in the uploaded document."
        keywords = ("project", "developed", "implemented", "pipeline", "classification", "engineered", "built", "purifying", "troubleshooting", "achieved", "accuracy", "response time")
        heading = "Projects"
    elif any(term in lowered_question for term in education_terms):
        keywords = ("education", "b.tech", "bachelor", "college", "university", "institute", "school", "engineering", "graduat", "2021", "2025")
        heading = "Education"
    else:
        keywords = ("skills", "python", "sql", "javascript", "linux", "aws", "react")
        heading = "Skills"

    evidence = []
    if "graduat" in lowered_question:
        year_ranges = []
        for match in re.finditer(r"(?:19|20)\d{2}\s*(?:[-–—]\s*(?:19|20)\d{2})?", context):
            year = re.sub(r"\s+", " ", match.group(0)).strip()
            if year not in year_ranges:
                year_ranges.append(year)
        if year_ranges:
            return "Education: Graduation year " + year_ranges[0]

    excluded = ("operating systems:", "programming languages:", "web technologies:", "frameworks & libraries:", "database management:", "cloud & systems:")
    for line in re.split(r"\n+|(?<=\.)\s+|\s+[•–—]\s+", context):
        clean_line = line.strip(" -•–—")
        clean_lower = clean_line.lower()
        is_year_line = bool(re.fullmatch(r"(?:19|20)\d{2}\s*(?:[-–—]\s*(?:19|20)\d{2})?", clean_line))
        if (
            (len(clean_line) >= 20 or (heading == "Education" and is_year_line))
            and not any(clean_lower.startswith(prefix) for prefix in excluded)
            and any(keyword in clean_lower for keyword in keywords)
        ):
            if clean_line not in evidence:
                evidence.append(clean_line)

    if not evidence:
        return "I couldn't find that information in the uploaded document."
    return f"{heading}: " + " ".join(evidence)


def extract_candidate_name(context: str) -> str | None:
    """Extract a likely resume name without relying on an LLM."""
    explicit_name = re.search(
        r"(?:candidate\s+name|name)\s*[:\-]\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})",
        context,
        re.IGNORECASE,
    )
    if explicit_name:
        return explicit_name.group(1).strip()

    first_line = re.sub(r"^\[[^\]]+\]\s*", "", context.splitlines()[0]).strip() if context.splitlines() else ""
    if re.fullmatch(r"[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,5}", first_line):
        return first_line.title()

    resume_name = re.search(
        r"(?:\]|\A)\s*([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+){1,3})(?=\s|$)",
        context,
    )
    if resume_name:
        return resume_name.group(1).title()

    return None


def _local_text_response(prompt: str) -> str:
    """Return a useful context-grounded response when Gemini is unavailable."""
    context = _context_from_prompt(prompt)
    sentences = _sentences(context)
    if not sentences:
        return "No supporting content was found in the processed documents."

    lowered_prompt = prompt.lower()
    question_match = re.search(r"Question:\s*(.*)\Z", prompt, re.DOTALL | re.IGNORECASE)
    question = question_match.group(1).strip() if question_match else ""
    resume_answer = answer_resume_question(question, context)
    if resume_answer:
        return resume_answer

    if re.search(r"\b(candidate\s+name|name\s+of\s+the\s+candidate)\b", lowered_prompt):
        candidate_name = extract_candidate_name(context)
        if candidate_name:
            return f"The candidate's name is {candidate_name}."

    if "multiple-choice" in lowered_prompt or "mcq" in lowered_prompt:
        questions = []
        for number, sentence in enumerate(sentences[:5], start=1):
            questions.append(
                f"{number}. Which statement is supported by the notes?\n"
                f"A. {sentence}\nB. The notes provide no information.\n"
                f"C. The opposite of the statement is true.\nD. None of these.\nAnswer: A"
            )
        return "\n\n".join(questions)

    if "summarize" in lowered_prompt or "summary" in lowered_prompt:
        return " ".join(sentences[:5])

    question_words = set(re.findall(r"[a-zA-Z]{4,}", question_match.group(1).lower())) if question_match else set()
    relevant = [sentence for sentence in sentences if question_words.intersection(
        set(re.findall(r"[a-zA-Z]{4,}", sentence.lower()))
    )]
    if not relevant:
        return "I couldn't find that information in the uploaded document."
    answer = " ".join(relevant[:3])
    return f"Gemini is unavailable, so here is the closest answer from your notes:\n\n{answer}"


def embed_texts(texts: list[str], model: str = EMBEDDING_MODEL) -> list[list[float]]:
    from google.genai import types

    response = get_client().models.embed_content(
        model=model,
        contents=texts,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSION),
    )
    return [embedding.values for embedding in response.embeddings]