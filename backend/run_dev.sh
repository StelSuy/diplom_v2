#!/usr/bin/env bash
set -euo pipefail

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
else
  echo "[WARN] venv not found. Create it:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements.txt"
fi

export PYTHONPATH="F:\Вуз\ДИПЛОМ\SYSTEM\backend"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
