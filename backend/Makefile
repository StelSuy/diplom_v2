.PHONY: help install dev init-db migrate upgrade health test clean

help:
	@echo "TimeTracker Backend - Available commands:"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run development server"
	@echo "  make init-db    - Initialize database (create tables + seed)"
	@echo "  make migrate    - Create new migration"
	@echo "  make upgrade    - Apply migrations"
	@echo "  make health     - Run health check"
	@echo "  make clean      - Clean cache files"
	@echo ""

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

init-db:
	python init_db.py

migrate:
	@echo "Creating migration..."
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

upgrade:
	alembic upgrade head

health:
	python health_check.py

test:
	@echo "No tests configured yet"
	@echo "TODO: Add pytest tests"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
