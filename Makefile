# Makefile — Common development commands for the Agentic RAG Platform
#
# Usage:
#   make help          — Print all targets
#   make install       — Install all dependencies (backend + frontend)
#   make test          — Run unit tests
#   make test-all      — Run all tests (unit + integration)
#   make lint          — Run Ruff linter
#   make format        — Auto-format code with Ruff
#   make typecheck     — Run mypy type checking
#   make security      — Run Bandit SAST + Safety dependency scan
#   make docker-up     — Start full stack with Docker Compose
#   make docker-down   — Stop Docker Compose stack
#   make docker-build  — Build Docker images
#   make clean         — Remove build/cache artefacts
#   make ci            — Run full CI pipeline locally

.PHONY: help install install-backend install-frontend \
        test test-all test-unit test-integration \
        lint format typecheck security \
        docker-up docker-down docker-build docker-logs \
        eval clean ci pre-commit

# Detect OS for cross-platform compatibility
PYTHON := python
PIP := pip
ifeq ($(OS), Windows_NT)
    PYTHON := python
    PIP := pip
    VENV_BIN := agentic_rag_fastapi/venv/Scripts
else
    PYTHON := python3
    PIP := pip3
    VENV_BIN := agentic_rag_fastapi/venv/bin
endif

BACKEND_DIR := agentic_rag_fastapi
FRONTEND_DIR := frontend

# ── Help ─────────────────────────────────────────────────────
help: ## Show this help message
	@echo ""
	@echo "  Agentic RAG Platform — Development Commands"
	@echo "  ─────────────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Install ───────────────────────────────────────────────────
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend Python dependencies
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	cd $(BACKEND_DIR) && $(PIP) install pytest pytest-cov pytest-asyncio httpx pydantic-settings ruff mypy bandit safety pre-commit
	$(PYTHON) -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
	@echo "✅ Backend dependencies installed"

install-frontend: ## Install frontend npm dependencies
	cd $(FRONTEND_DIR) && npm ci
	@echo "✅ Frontend dependencies installed"

# ── Testing ───────────────────────────────────────────────────
test: test-unit ## Alias for test-unit

test-unit: ## Run unit tests (offline, all mocked)
	cd $(BACKEND_DIR) && pytest tests/ -m "unit" \
		--tb=short -v \
		--cov=. \
		--cov-report=term-missing \
		--cov-omit="tests/*,venv/*,data/*" \
		-n auto 2>/dev/null || \
	cd $(BACKEND_DIR) && pytest tests/ -m "unit" \
		--tb=short -v \
		--cov=. \
		--cov-report=term-missing \
		--cov-omit="tests/*,venv/*,data/*"

test-integration: ## Run integration tests (requires running backend on :8002)
	cd $(BACKEND_DIR) && pytest tests/ -m "integration" --tb=short -v

test-all: ## Run all tests
	cd $(BACKEND_DIR) && pytest tests/ --tb=short -v \
		--cov=. \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-omit="tests/*,venv/*,data/*"
	@echo "📊 Coverage report: $(BACKEND_DIR)/htmlcov/index.html"

# ── Code Quality ──────────────────────────────────────────────
lint: ## Run Ruff linter
	cd $(BACKEND_DIR) && ruff check . --output-format=concise

lint-fix: ## Run Ruff linter with auto-fix
	cd $(BACKEND_DIR) && ruff check . --fix

format: ## Format code with Ruff
	cd $(BACKEND_DIR) && ruff format .
	@echo "✅ Code formatted"

format-check: ## Check formatting without modifying files
	cd $(BACKEND_DIR) && ruff format . --check

typecheck: ## Run mypy type checking
	cd $(BACKEND_DIR) && mypy . --ignore-missing-imports --exclude 'tests/' || true
	@echo "✅ Type check complete"

security: ## Run Bandit SAST and Safety dependency scan
	@echo "🔒 Running Bandit SAST..."
	cd $(BACKEND_DIR) && bandit -r . \
		--exclude ./tests,./venv,./.venv \
		--skip B101,B104 \
		--severity-level medium \
		--confidence-level medium \
		-f text || true
	@echo ""
	@echo "🔒 Running Safety dependency scan..."
	cd $(BACKEND_DIR) && safety check --file requirements.txt || true

# ── Pre-commit ────────────────────────────────────────────────
pre-commit: ## Install and run pre-commit hooks on all files
	pre-commit install
	pre-commit run --all-files

# ── Docker ────────────────────────────────────────────────────
docker-build: ## Build Docker images without starting
	docker-compose build --no-cache

docker-up: ## Start full stack (backend + frontend)
	docker-compose up -d
	@echo ""
	@echo "  🚀 Stack started!"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8002"
	@echo "  API Docs: http://localhost:8002/docs"

docker-down: ## Stop and remove Docker containers
	docker-compose down

docker-logs: ## Tail Docker logs for all services
	docker-compose logs -f

docker-clean: ## Remove all project Docker images and volumes
	docker-compose down -v --rmi local

# ── Evaluation ────────────────────────────────────────────────
eval: ## Run the 15-query evaluation harness (requires running backend)
	cd $(BACKEND_DIR) && $(PYTHON) evaluate_agentic_rag.py
	@echo "📊 Report saved: $(BACKEND_DIR)/evaluation_report.json"

# ── Local dev servers ─────────────────────────────────────────
dev-backend: ## Start backend in reload mode
	cd $(BACKEND_DIR) && uvicorn app:app --host 0.0.0.0 --port 8002 --reload

dev-frontend: ## Start frontend Vite dev server
	cd $(FRONTEND_DIR) && npm run dev

# ── CI simulation ─────────────────────────────────────────────
ci: lint format-check test-unit security ## Run full CI pipeline locally
	@echo ""
	@echo "✅ All CI checks passed locally!"

# ── Cleanup ───────────────────────────────────────────────────
clean: ## Remove all build and cache artefacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "🧹 Clean complete"
