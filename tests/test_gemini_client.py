from src.gemini_client import answer_resume_question, expand_project_documents, expand_resume_documents, extract_candidate_name, generate_text


def force_offline(monkeypatch):
    def unavailable(*args, **kwargs):
        raise RuntimeError("offline test")

    monkeypatch.setattr("src.gemini_client.get_client", unavailable)
    monkeypatch.setattr("src.gemini_client._generate_text_rest", unavailable)


def test_extract_candidate_name_from_resume_text():
    context = "[Amazon resume.pdf - p.1] GOVATHOTI VAMSI\n8125723070\nObjective"

    assert extract_candidate_name(context) == "Govathoti Vamsi"


def test_new_resume_name_and_graduation_questions():
    context = (
        "Prasanna Sai Ravi Teja Kambham\nObjective\nEducation\n"
        "B.Tech in Electronics and Communication Engineering\n2021 - 2025\n"
        "Seshadri Rao Gudlavalleru Engineering College"
    )

    assert answer_resume_question("what is his name", context) == "The candidate's name is Prasanna Sai Ravi Teja Kambham."
    education = answer_resume_question("which year is he graduated", context)
    assert "2021" in education
    assert "2025" in education


def test_college_name_question_does_not_return_candidate_name():
    context = (
        "SEELAM DURGA LOVA RAJU\nEducation\n"
        "B.Tech in Electronics and Communication Engineering\n"
        "Hyderabad Institute of Technology and Management"
    )

    result = answer_resume_question("what is his college name", context)

    assert "Hyderabad Institute of Technology and Management" in result
    assert "SEELAM DURGA LOVA RAJU" not in result


def test_resume_experience_answer_uses_matching_evidence_only():
    context = "[resume.pdf - p.1] GOVATHOTI VAMSI\nExperience AI/ML Intern - Developed an image classification system using Python and OpenCV."

    result = answer_resume_question("What is his experience?", context)

    assert "AI/ML Intern" in result
    assert "image classification" in result


def test_resume_unrelated_question_does_not_use_first_chunk():
    context = "[resume.pdf - p.1] GOVATHOTI VAMSI\nExperience AI/ML Intern - Developed an image classification system."

    result = answer_resume_question("Why did he stop in the middle?", context)

    assert result == "I couldn't find that information in the uploaded document."


def test_resume_project_answer_keeps_complete_project_evidence():
    context = (
        "[resume.pdf - p.1] Programming Languages: Python, JavaScript. "
        "Engineered the document processing pipeline using PDF extraction, text chunking, embeddings, FAISS vector search, and semantic retrieval. "
        "Achieved 94% query-answering accuracy with response times below 15 seconds. "
        "Operating Systems: Linux/Unix Fundamentals."
    )

    result = answer_resume_question("What is his latest project?", context)

    assert "document processing pipeline" in result
    assert "94% query-answering accuracy" in result
    assert "Operating Systems" not in result


def test_resume_named_project_answer_does_not_return_first_project():
    context = (
        "First Project\n"
        "• Built a document processing application.\n"
        "Air Pen – Hand Gesture Controlled Virtual Drawing Application\n"
        "• Created a Python and OpenCV computer vision application for touchless drawing.\n"
        "• Achieved 90% gesture detection accuracy.\n"
        "AI-Based Driver Drowsiness Detection System\n"
        "• Built a real-time driver monitoring application."
    )

    result = answer_resume_question("Tell me about his Airpen project", context)

    assert "touchless drawing" in result
    assert "90% gesture detection accuracy" in result
    assert "document processing application" not in result
    assert "driver monitoring" not in result


def test_any_named_project_can_expand_beyond_top_results():
    first = {"text": "First document processing project.", "source": "resume.pdf", "page": 1}
    requested = {"text": "AI-Based Driver Drowsiness Detection System using ESP32 and Blynk.", "source": "resume.pdf", "page": 1}

    expanded = expand_project_documents("Tell me about his driver drowsiness project", [first, requested], [first])

    assert requested in expanded


def test_education_question_expands_all_chunks_from_matching_resume():
    first = {"text": "SEELAM DURGA LOVA RAJU\nEducation\nB.Tech in Electronics and Communication Engineering", "source": "durga resume.pdf", "page": 1}
    second = {"text": "2022 - 2026\nHyderabad Institute of Technology and Management", "source": "durga resume.pdf", "page": 2}
    other = {"text": "2021 - 2025", "source": "other resume.pdf", "page": 2}

    expanded = expand_resume_documents("what is his graduation year", [first, second, other], [first])

    assert second in expanded
    assert other not in expanded


def test_misspelled_direct_project_question_finds_matching_project():
    context = (
        "AI-Based Driver Drowsiness Detection System\n"
        "• Built a real-time driver monitoring application using Python, OpenCV, ESP32, and Blynk.\n"
        "• Achieved 92% detection accuracy."
    )

    result = answer_resume_question("what is his drowsness project", context)

    assert "driver monitoring application" in result
    assert "92% detection accuracy" in result


def test_generate_text_answers_candidate_name_directly(monkeypatch):
    force_offline(monkeypatch)

    result = generate_text(
        "Answer the question.\n\n"
        "Context:\n[Amazon resume.pdf - p.1] GOVATHOTI VAMSI\nMachine learning skills.\n\n"
        "Question: What is the candidate name?"
    )

    assert result == "The candidate's name is Govathoti Vamsi."


def test_generate_text_falls_back_without_gemini_key(monkeypatch):
    force_offline(monkeypatch)

    result = generate_text(
        "Use the context.\n\n"
        "Context:\nPhotosynthesis converts light energy into chemical energy.\n\n"
        "Question: What does photosynthesis convert?"
    )

    assert "Photosynthesis converts light energy into chemical energy." in result
    assert "Question:" not in result


def test_generate_text_fallback_supports_summary(monkeypatch):
    force_offline(monkeypatch)

    result = generate_text(
        "Summarize the following content.\n\n"
        "Context:\nA triangle has three sides. A square has four sides."
    )

    assert result == "A triangle has three sides. A square has four sides."


def test_generate_text_fallback_does_not_dump_unrelated_context(monkeypatch):
    force_offline(monkeypatch)

    result = generate_text(
        "Answer the question.\n\n"
        "Context:\nGOVATHOTI VAMSI. Python, Linux, SQL, and cloud fundamentals.\n\n"
        "Question: Which university did the candidate attend?"
    )

    assert result == "I couldn't find that information in the uploaded document."
