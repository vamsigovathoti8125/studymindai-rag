# StudyMind AI - Setup Instructions

## Quick Start

### 1. Set up Python environment
```powershell
cd "C:\Users\Acer\OneDrive\Desktop\studyproject"
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. (Optional) Add OpenAI API Key
Edit `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY="sk-your-key-here"
```

Get a key from: https://platform.openai.com/api-keys

### 4. Run the app
```powershell
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Features

✅ **Upload & Process PDFs** - Upload study materials and extract text  
✅ **Semantic Search** - Ask questions and get relevant excerpts from your documents  
✅ **Quiz Generation** - Automatically generate multiple-choice questions  
✅ **Summarization** - Get concise summaries of your materials  
✅ **Calculator** - Perform arithmetic calculations  
✅ **Persistent Index** - Saves FAISS index and documents for fast restarting  
✅ **Works without OpenAI** - Falls back to local embeddings  

## Project Structure

```
studyproject/
├── app.py                 # Main Streamlit app
├── .env                   # Environment variables (add your API key)
├── requirements.txt       # Python dependencies
├── faiss_index.bin       # Saved FAISS index (auto-generated)
├── docs.json             # Saved documents metadata (auto-generated)
├── README.md             # Project documentation
├── src/
│   ├── ingest.py         # PDF extraction & chunking
│   ├── vectorstore.py    # FAISS index management
│   ├── agent/
│   │   └── agent.py      # Tool selection logic
│   └── tools/
│       ├── calculator.py # Math calculations
│       ├── quiz_tool.py  # MCQ generation
│       ├── rag_tool.py   # Context formatting
│       └── summary_tool.py # Summarization
├── tests/                # Unit tests
└── scripts/
    └── smoke_test.py     # Quick functionality test
```

## Testing

Run a quick smoke test:
```powershell
python scripts/smoke_test.py
```

Run unit tests:
```powershell
python -m pytest tests/ -v
```

## Troubleshooting

**"ModuleNotFoundError" errors?**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**OpenAI errors?**
- Check that your API key is correct in `.env`
- Verify you have API credits available

**FAISS/embedding errors?**
- The app will use local embeddings as fallback
- No OpenAI key needed for basic functionality

## Next Steps

1. Upload a PDF with study notes using the sidebar
2. Click "Process Documents"
3. Ask questions about your materials in the chat
4. Use quiz generation to test yourself
5. The index is saved automatically for future sessions
