@echo off
setlocal EnableDelayedExpansion
cd /d %~dp0

echo.
echo  ============================================
echo   TimeTracker API ^— Local Development Server
echo  ============================================
echo.

:: ── 1. Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ and add it to PATH.
    pause & exit /b 1
)

:: ── 2. Create venv if missing ────────────────────────────────────────────────
if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 ( echo [ERROR] Failed to create venv. & pause & exit /b 1 )
)

:: ── 3. Activate venv ─────────────────────────────────────────────────────────
call .venv\Scripts\activate

:: ── 4. Sync dependencies (always — catches newly added packages) ─────────────
echo [DEPS]  Syncing dependencies from requirements.txt...
pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause & exit /b 1
)
echo [OK]    Dependencies up to date.

:: ── 5. Check .env ────────────────────────────────────────────────────────────
if not exist ".env" (
    echo [SETUP] .env not found — copying from .env.example...
    copy .env.example .env >nul
    echo [WARN]  Review .env — set real DB credentials and passwords.
    echo         Press any key to continue...
    pause >nul
)

set PYTHONPATH=%CD%

:: ── 6. Ensure DB + user exist ────────────────────────────────────────────────
echo [DB]    Ensuring database and user exist...
python scripts\ensure_db.py
if errorlevel 1 (
    echo [WARN]  DB setup had issues. Check MySQL connection in .env.
)

:: ── 7. Apply Alembic migrations (creates / updates ALL tables) ───────────────
echo [DB]    Applying migrations ^(alembic upgrade head^)...
alembic upgrade head
if errorlevel 1 (
    echo [WARN]  Alembic failed — running create_all fallback...
    python scripts\ensure_db.py --tables-only
    if errorlevel 1 (
        echo [ERROR] Could not create tables. Check DB connection.
        pause & exit /b 1
    )
)
echo [OK]    All tables are up to date.

:: ── 8. Start dev server ──────────────────────────────────────────────────────
echo.
echo [RUN]   Starting FastAPI development server...
echo         API:  http://localhost:8000
echo         Docs: http://localhost:8000/docs
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

endlocal
