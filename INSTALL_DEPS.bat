@echo off
REM StudyMind AI - Python 3.13 Installation Fix
REM This script installs dependencies with compatibility fixes for Python 3.13

echo.
echo ========================================
echo  StudyMind AI - Dependency Installation
echo  Python 3.13 Compatible Version
echo ========================================
echo.

echo Updating pip...
python.exe -m pip install --upgrade pip setuptools wheel -q

echo.
echo Installing dependencies (this may take a few minutes)...
echo.

REM Try to install minimal set of dependencies
python.exe -m pip install ^
  streamlit ^
  openai ^
  pymupdf ^
  numpy ^
  python-dotenv ^
  tiktoken ^
  --upgrade ^
  --prefer-binary ^
  2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Some dependencies failed to install.
    echo Attempting minimal installation...
    echo.
    python.exe -m pip install openai python-dotenv pymupdf -q
)

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo To run the app, use:
echo   streamlit run app.py
echo.
pause
