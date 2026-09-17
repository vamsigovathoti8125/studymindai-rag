# StudyMind AI - Quick Setup Script (PowerShell)
# Run this script to set up and start your project

Write-Host ""
Write-Host "========================================"
Write-Host "    StudyMind AI - Quick Setup"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create it first with: python -m venv .venv"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Installing dependencies (this may take a minute)..." -ForegroundColor Yellow
pip install -q -r requirements.txt

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup complete! Starting Streamlit app..."
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The app will open in your browser at:" -ForegroundColor Cyan
Write-Host "http://localhost:8501" -ForegroundColor Green
Write-Host ""

streamlit run app.py
