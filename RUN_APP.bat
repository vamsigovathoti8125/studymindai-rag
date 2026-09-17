@echo off
REM StudyMind AI - Quick Setup Script
REM Run this script to set up and start your project

echo.
echo ========================================
echo    StudyMind AI - Quick Setup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found!
    echo Please create it first with: python -m venv .venv
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\Activate.ps1

echo.
echo Installing dependencies (this may take a minute)...
pip install -q -r requirements.txt

echo.
echo ========================================
echo Setup complete! Starting Streamlit app...
echo ========================================
echo.
echo The app will open in your browser at:
echo http://localhost:8501
echo.

streamlit run app.py
