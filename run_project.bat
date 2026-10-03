@echo off
TITLE LegalEase AI - Launcher
echo =====================================================================
echo                LEGALEASE AI - SYSTEM LAUNCHER
echo            AI-Powered Legal Document Generator
echo =====================================================================
echo.

:: Check for virtual environment
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Please run: python -m venv venv
    echo And install requirements: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

:: Check for .env file
IF NOT EXIST ".env" (
    echo [WARNING] .env file not found. Copying .env.example to .env...
    copy .env.example .env
    echo Please edit .env and configure your GEMINI_API_KEY.
)

echo Starting LegalEase AI Services...
echo.
echo [1/2] Launching FastAPI Backend on http://localhost:8000 ...
start "LegalEase Backend" cmd /k "venv\Scripts\activate && uvicorn backend.main:app --reload --port 8000"

:: Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak >nul

echo [2/2] Launching Streamlit Frontend on http://localhost:8501 ...
start "LegalEase Frontend" cmd /k "venv\Scripts\activate && streamlit run frontend/app.py"

echo.
echo =====================================================================
echo LegalEase AI is running!
echo Backend API:  http://localhost:8000 (Swagger docs at /docs)
echo Frontend App: http://localhost:8501
echo =====================================================================
echo Keep the terminal windows open while using LegalEase AI.
pause
