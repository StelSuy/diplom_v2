@echo off
setlocal
cd /d %~dp0

if exist .venv\Scripts\python.exe (
  call .venv\Scripts\activate
) else (
  echo [WARN] venv not found. Create it:
  echo   python -m venv .venv
  echo   .venv\Scripts\pip install -r requirements.txt
)

set PYTHONPATH=%CD%
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
endlocal
