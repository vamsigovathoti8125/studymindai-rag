# 🧠 StudyMind AI

StudyMind AI is an agentic RAG study assistant built with Streamlit. Upload PDFs, build a knowledge base, and ask questions using retrieval-augmented generation, quiz generation, and calculator support.

## What it does

- Upload PDF study notes and extract page text
- Split documents into overlapping chunks
- Build a FAISS vector index for semantic search
- Answer questions using retrieved document context
- Generate multiple-choice questions from your notes
- Perform safe arithmetic calculations
- Load/save an index for faster restarting
- Use Gemini if `GEMINI_API_KEY` is available
- Fall back to local embeddings and context-grounded answers when Gemini is unavailable

## Requirements

- Python 3.11 or newer
- `Flask`, `streamlit`, `google-genai`, `faiss-cpu`, `pymupdf`, `numpy`, `python-dotenv`, `sentence-transformers`
- `pytest` for running tests

## Setup

1. Activate the repository virtual environment:

```powershell
cd "C:\Users\Acer\OneDrive\Desktop\studyproject"
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Set your Google AI Studio key:

```powershell
$env:GEMINI_API_KEY = "AIza..."
```

You can create a key at https://aistudio.google.com/apikey.

## Run the app

For the Streamlit interface:

```powershell
streamlit run app.py
```

For the lightweight Flask interface, which works without Streamlit or Gemini:

```powershell
python app_flask.py
```

Then open the browser at `http://localhost:8501`.

## Testing

Run the unit tests with:

```powershell
python -m pytest -q
```

## Notes

- If no Gemini key is found, the app still builds embeddings with a local fallback and answers from retrieved context.
- The app saves `faiss_index.bin` and `docs.json` to the working directory after processing documents.
