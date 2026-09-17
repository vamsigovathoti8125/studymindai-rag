import os
import streamlit as st
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda *args, **kwargs: None
from src.ingest import extract_pages_from_pdf, chunk_pages
from src.vectorstore import get_embeddings, build_faiss_index, search_index, load_index, save_index
from src.tools.rag_tool import format_retrieved_chunks
from src.tools.quiz_tool import generate_mcqs
from src.tools.summary_tool import generate_summary
from src.tools.calculator import calculate
from src.agent.agent import decide_tool
from src.gemini_client import CHAT_MODEL, EMBEDDING_MODEL, answer_resume_question, expand_project_documents, expand_resume_documents, extract_candidate_name, generate_text

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="StudyMind AI",
    page_icon="🧠",
    layout="wide"
)

# Load .env if present
load_dotenv()

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hello! I'm StudyMind AI.\n\n"
                "Upload your study materials and ask me "
                "questions about them."
            )
        }
    ]

if "docs" not in st.session_state:
    st.session_state.docs = []

if "index" not in st.session_state:
    st.session_state.index = None

if "index_loaded" not in st.session_state:
    st.session_state.index_loaded = False

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("🧠 StudyMind AI")

    st.write(
        "Your personal Agentic RAG study assistant."
    )

    st.divider()

    st.subheader("⚙️ Settings")

    model = st.selectbox(
        "LLM Model",
        [
            "Gemini",
        ]
    )

    top_k = st.slider(
        "Retrieved Documents",
        min_value=1,
        max_value=10,
        value=4
    )

    st.write(f"Top K: {top_k}")

    chat_model = CHAT_MODEL
    embedding_model = EMBEDDING_MODEL

    st.caption("Gemini is optional. Local answers remain available when the API key or quota is unavailable.")

    st.divider()

    st.subheader("📚 Knowledge Base")

    uploaded_files = st.file_uploader(
        "Upload study materials",
        type=["pdf"],
        accept_multiple_files=True
    )

    process_docs = st.button("Process Documents")

    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded")
        for file in uploaded_files:
            st.write(f"📄 {file.name}")

    if process_docs and uploaded_files:
        st.info("Processing documents and building the knowledge base...")
        try:
            st.session_state.docs = []
            for file in uploaded_files:
                try:
                    pdf_bytes = file.read()
                    pages = extract_pages_from_pdf(pdf_bytes, file.name)
                    chunks = chunk_pages(pages)
                    st.session_state.docs.extend(chunks)
                except Exception as e:
                    st.error(f"Failed to process {file.name}: {e}")

            if st.session_state.docs:
                texts = [d["text"] for d in st.session_state.docs]
                embeddings = get_embeddings(texts, embedding_model=embedding_model)
                st.session_state.index, _ = build_faiss_index(embeddings)
                try:
                    save_index(st.session_state.index, st.session_state.docs)
                except Exception:
                    pass
                st.success("Knowledge base built — ready for questions.")
        except Exception as e:
            st.error(f"Failed to build vector index: {e}")
    elif uploaded_files and not process_docs:
        st.info("Click 'Process Documents' after uploading PDFs to build the knowledge base.")

# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------

st.title("🧠 StudyMind AI")

st.subheader(
    "Your Personal AI Study Assistant"
)

st.write(
    """
Upload your study materials and interact with them
using Retrieval Augmented Generation, semantic search,
LLMs and Agentic AI.
"""
)

st.divider()

# Attempt to load persisted index on startup (runs once per session)
if not st.session_state.index_loaded:
    try:
        idx, docs = load_index()
        if idx is not None and docs:
            st.session_state.index = idx
            st.session_state.docs = docs
    except Exception:
        pass
    st.session_state.index_loaded = True

# --------------------------------------------------
# DISPLAY CHAT HISTORY
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])

# --------------------------------------------------
# CHAT INPUT
# --------------------------------------------------

question = st.chat_input(
    "Ask something about your study materials..."
)

if question:

    # Store user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.write(question)

    # Temporary response
    # If we have an index, run RAG; otherwise return a helpful message
    if st.session_state.index is None:
        response = (
            "🚧 Knowledge base not ready. Upload and process PDFs in the sidebar."
        )
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)
    else:
        # Decide which tool to use
        tool = decide_tool(question)

        if tool == "calculator":
            try:
                result = calculate(question)
                answer = f"Result: {result}"
            except Exception as e:
                answer = f"Calculator error: {e}"

            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.write(answer)

        elif tool == "quiz":
            # Retrieve top-k and generate MCQs
            q_emb = get_embeddings([question], embedding_model=embedding_model)[0]
            ids, _ = search_index(st.session_state.index, q_emb, k=top_k)
            retrieved = [st.session_state.docs[i] for i in ids if i < len(st.session_state.docs)]
            retrieved = expand_project_documents(question, st.session_state.docs, retrieved)
            retrieved = expand_resume_documents(question, st.session_state.docs, retrieved)
            context = format_retrieved_chunks(retrieved)
            try:
                mcqs = generate_mcqs(context, num_questions=5, model=chat_model)
            except Exception as e:
                mcqs = f"LLM request failed: {e}\n\nHere is the retrieved context:\n\n{context}"
            st.session_state.messages.append({"role": "assistant", "content": mcqs})
            with st.chat_message("assistant"):
                st.write(mcqs)

        elif tool == "summary":
            q_emb = get_embeddings([question], embedding_model=embedding_model)[0]
            ids, _ = search_index(st.session_state.index, q_emb, k=top_k)
            retrieved = [st.session_state.docs[i] for i in ids if i < len(st.session_state.docs)]
            retrieved = expand_project_documents(question, st.session_state.docs, retrieved)
            retrieved = expand_resume_documents(question, st.session_state.docs, retrieved)
            context = format_retrieved_chunks(retrieved)
            try:
                summary = generate_summary(context, model=chat_model)
            except Exception as e:
                summary = f"LLM request failed: {e}\n\nHere is the retrieved context:\n\n{context}"
            st.session_state.messages.append({"role": "assistant", "content": summary})
            with st.chat_message("assistant"):
                st.write(summary)

        else:
            # RAG flow
            q_emb = get_embeddings([question], embedding_model=embedding_model)[0]
            ids, _ = search_index(st.session_state.index, q_emb, k=top_k)
            retrieved = [st.session_state.docs[i] for i in ids if i < len(st.session_state.docs)]
            retrieved = expand_project_documents(question, st.session_state.docs, retrieved)
            retrieved = expand_resume_documents(question, st.session_state.docs, retrieved)
            context = format_retrieved_chunks(retrieved)
            prompt = (
                "You are StudyMind AI. Answer using ONLY the provided context. If insufficient, say so.\n\n"
                f"Context:\n{context}\n\nQuestion: {question}"
            )

            try:
                resume_answer = answer_resume_question(question, context)
                candidate_name = extract_candidate_name(context) if "name" in question.lower() else None
                answer = (
                    resume_answer
                    if resume_answer
                    else f"The candidate's name is {candidate_name}."
                    if candidate_name
                    else generate_text(
                        "You are a helpful study assistant.\n\n" + prompt,
                        model=chat_model,
                        max_output_tokens=512,
                    )
                )
            except Exception as e:
                answer = f"LLM request failed: {e}"

            # Append sources after answer
            sources = []
            for d in retrieved:
                sources.append(f"• {d.get('source')} — p.{d.get('page')}")

            if sources:
                answer = answer + "\n\nSources:\n" + "\n".join(dict.fromkeys(sources))

            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.write(answer)
