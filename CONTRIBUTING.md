# Contributing to Agentic RAG Platform

Thank you for your interest in contributing! This guide covers everything
you need to get started.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/).
By participating, you agree to uphold a welcoming and respectful environment.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional but recommended)
- Git

### Setup

```bash
# Clone the repo
git clone https://github.com/<your-org>/agentic-rag-platform.git
cd agentic-rag-platform

# Install all dependencies (backend + frontend)
make install

# Copy and configure environment
cp .env.example agentic_rag_fastapi/.env
# Edit .env and add your GROQ_API_KEY

# Start the backend
make dev-backend

# Start the frontend (new terminal)
make dev-frontend
```

---

## Development Workflow

We use **GitHub Flow**:

1. Fork the repository (external contributors) or create a branch (team members)
2. Create a feature/fix branch: `git checkout -b feat/your-feature-name`
3. Make changes, write tests, update docs
4. Run the full CI check locally: `make ci`
5. Push and open a Pull Request against `develop`
6. After review and CI pass, it is merged to `develop` then `main`

### Branch naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<description>` | `feat/streaming-endpoint` |
| Bug fix | `fix/<description>` | `fix/registry-race-condition` |
| Docs | `docs/<description>` | `docs/api-reference` |
| Refactor | `refactor/<description>` | `refactor/agentic-loop` |
| Test | `test/<description>` | `test/ingestion-ocr` |

### Commit message format (Conventional Commits)

```
<type>(<scope>): <short summary>

[optional body]

[optional footer: Closes #123]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `security`

Examples:
```
feat(api): add SSE streaming endpoint for real-time responses
fix(sc-agent): handle LLM returning list-wrapped JSON object
test(ingestion): add OCR auto-fallback unit tests
security(auth): restrict CORS to configured origins only
```

---

## Code Standards

### Python

- **Style**: [Ruff](https://docs.astral.sh/ruff/) (replaces black + isort + flake8)
- **Type hints**: Required on all public functions
- **Docstrings**: Google-style, required on all public functions and modules
- **Line length**: 100 characters

```bash
# Check and auto-fix
make lint-fix
make format
```

### JavaScript / React

- **Style**: Prettier (run automatically via pre-commit)
- **Naming**: PascalCase for components, camelCase for functions/variables
- **Accessibility**: All interactive elements must have ARIA labels

### Type annotations example

```python
# ✅ Correct
def planner_agent(query: str) -> list[str]:
    """Decompose query into sub-questions."""
    ...

# ❌ Incorrect — missing type hints and docstring
def planner_agent(query):
    ...
```

---

## Testing

All new code requires tests. We use `pytest`.

```bash
# Run unit tests (offline, fast)
make test-unit

# Run all tests
make test-all

# Run with specific markers
pytest tests/ -m "unit and not slow" -v
```

### Test requirements

| Change type | Required tests |
|-------------|----------------|
| New agent function | Unit tests for all branches (success + fallback) |
| New API endpoint | Endpoint test (200, 4xx, auth check) |
| New schema field | Validation test (valid + invalid values) |
| Bug fix | Regression test that fails without the fix |
| Refactor | All existing tests must continue to pass |

### Writing tests

```python
@pytest.mark.unit
def test_planner_falls_back_on_invalid_json(self):
    """planner_agent must return [query] when LLM returns non-JSON."""
    with patch("agents.llm.safe_generate", return_value="not JSON"):
        from agents.planner import planner_agent
        result = planner_agent("my query")
    assert result == ["my query"]
```

---

## Submitting a Pull Request

1. Ensure all CI checks pass: `make ci`
2. Ensure coverage did not decrease: `make test-all`
3. Update the README if you changed the API or configuration
4. Fill in the PR template completely
5. Request review from at least one maintainer
6. Address all review comments before merging

---

## Reporting Bugs

Use [GitHub Issues](../../issues/new?template=bug_report.md).

Include:
- Python / Node version
- Steps to reproduce
- Expected vs actual behaviour
- Error message / stack trace

---

## Suggesting Features

Use [GitHub Issues](../../issues/new?template=feature_request.md) with the `enhancement` label.

Include:
- The problem you're trying to solve
- Your proposed solution
- Alternatives you considered

---

## Security

Please read [SECURITY.md](SECURITY.md) before reporting security issues.
**Do not open public issues for security vulnerabilities.**
