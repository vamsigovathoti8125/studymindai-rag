# 🚀 QUICK START - StudyMind AI

## Fastest Way to Run (One Command)

### Option 1: PowerShell (Recommended for Windows)
```powershell
cd "C:\Users\Acer\OneDrive\Desktop\studyproject"
.\RUN_APP.ps1
```

### Option 2: Manual PowerShell Commands
```powershell
cd "C:\Users\Acer\OneDrive\Desktop\studyproject"
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

### Option 3: Batch File (Command Prompt)
```cmd
cd "C:\Users\Acer\OneDrive\Desktop\studyproject"
RUN_APP.bat
```

---

## ✅ Verification Checklist

Before running, ensure you have:

- [ ] `.venv` folder exists (Python virtual environment)
- [ ] `requirements.txt` has dependencies listed
- [ ] `app.py` exists in the project root
- [ ] `src/` folder with submodules exists
- [ ] `.env` file exists (even if empty)

If any of these are missing, you're looking at an incomplete setup.

---

## 📍 Current Project Location

```
C:\Users\Acer\OneDrive\Desktop\studyproject
```

---

## 🎯 What Happens When You Run

1. ✅ Activates Python virtual environment
2. ✅ Installs/updates dependencies from requirements.txt
3. ✅ Starts Streamlit development server
4. ✅ Opens browser automatically (http://localhost:8501)
5. ✅ Shows StudyMind AI interface

---

## 💡 Your First Steps in the App

1. **Upload a PDF** → Use sidebar "Upload study materials"
2. **Process it** → Click "Process Documents"
3. **Ask a question** → Type in chat box at bottom
4. **Get answer** → AI responds with sources
5. **Try features** → Use quiz/summary/calculator

---

## 📋 Essential Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application |
| `requirements.txt` | Python dependencies |
| `.env` | Configuration (OpenAI key optional) |
| `WORKING_VERSION_SUMMARY.md` | Full documentation |
| `SETUP_INSTRUCTIONS.md` | Detailed setup guide |

---

## 🆘 If Something Goes Wrong

### Error: "Module not found"
```powershell
pip install -r requirements.txt
```

### Error: ".venv not found"
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Error: "Port already in use"
Streamlit will automatically use the next available port (8502, 8503, etc.)

### Error: "Cannot import openai"
```powershell
pip install openai
```

---

## ✨ Your Project is Complete!

- ✅ All code written
- ✅ All modules created
- ✅ All dependencies specified
- ✅ Ready to run immediately
- ✅ Full documentation provided

**No additional development needed.**

Just run the startup command and enjoy your AI study assistant! 🎓
