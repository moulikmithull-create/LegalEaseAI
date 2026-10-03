# LegalEase AI - Development Setup Guide

## Overview
This guide provides the exact step-by-step instructions to set up, configure, and run **LegalEase AI** on Windows and within the Antigravity workspace.

---

## Prerequisites
- **Python**: Version 3.10+ (Tested on Python 3.14.6)
- **Pip**: Latest version
- **Google Gemini API Key**: Free tier or paid key from [Google AI Studio](https://aistudio.google.com/)

---

## Step 1 — Verify Python Installation
Open PowerShell and verify Python is installed:
```powershell
python --version
```
Expected output:
```text
Python 3.10+ (or Python 3.14.x)
```

---

## Step 2 — Create Virtual Environment
Navigate to the project root directory:
```powershell
cd C:\Users\DELL\.gemini\antigravity\scratch\LegalEase-AI
python -m venv venv
```

---

## Step 3 — Activate the Virtual Environment
```powershell
venv\Scripts\activate
```
Upon activation, your shell prompt will show `(venv)`.

---

## Step 4 — Install Required Dependencies
Upgrade `pip` and install all project packages:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verified packages installed:
- `fastapi` & `uvicorn` (REST API & ASGI server)
- `streamlit` (Web UI frontend)
- `requests` (Frontend HTTP client)
- `pydantic` (Data validation)
- `python-dotenv` (Environment configuration)
- `google-genai` & `google-generativeai` (Gemini SDKs)
- `python-docx` (Microsoft Word generator)
- `reportlab` (PDF document generator)
- `Pillow` (Image verification & logo generation)
- `pytest` & `httpx` (Automated testing suite)

---

## Step 5 — Configure Environment Variables (.env)
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Open `.env` in an editor and enter your Gemini API key:
```env
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Gemini Model Selection
GEMINI_MODEL=gemini-2.5-flash

# Backend Network Settings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_URL=http://localhost:8000
```

---

## Step 6 — Start the FastAPI Backend
Launch the backend server in a terminal window:
```powershell
uvicorn backend.main:app --reload --port 8000
```
Expected startup log:
```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```
- Verify API root: `http://localhost:8000/`
- Verify Swagger UI: `http://localhost:8000/docs`

---

## Step 7 — Start the Streamlit Frontend
Open a second PowerShell window, activate `venv`, and start Streamlit:
```powershell
venv\Scripts\activate
streamlit run frontend/app.py
```
Expected startup log:
```text
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```
Open your browser to `http://localhost:8501`.

---

## Quick One-Click Windows Launcher
Alternatively, run the provided batch script to launch both services simultaneously:
```powershell
.\run_project.bat
```
