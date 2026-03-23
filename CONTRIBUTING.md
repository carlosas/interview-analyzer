# Contributing

## Prerequisites

- Docker and Docker Compose

No local Python installation is needed — everything runs inside containers.

## Getting Started

1. Clone the repository
2. Copy the environment file and configure it:
   ```bash
   cp .env.dist .env
   ```
3. Build and set up the project:
   ```bash
   make install
   ```
4. Enable git hooks:
   ```bash
   make hooks
   ```
5. Start the services:
   ```bash
   make start
   ```
   - App: http://localhost:8501
   - Adminer (DB UI): http://localhost:8080

## Development Workflow

### Useful Commands

| Command                    | Description                              |
|----------------------------|------------------------------------------|
| `make start`               | Start all services                       |
| `make stop`                | Stop all services                        |
| `make restart`             | Restart all services                     |
| `make logs`                | Tail logs from all services              |
| `make shell`               | Open a bash shell in the app container   |
| `make migrate`             | Run database migrations                  |
| `make lint`                | Auto-fix lint and formatting issues      |
| `make tests`               | Run the test suite                       |
| `make rebuild`             | Rebuild images from scratch and restart  |
| `make poetry-lock-update`  | Update Poetry lock files                 |

### Git Hooks

Run `make hooks` once after cloning. This configures git to use the project's `.githooks/` directory, which includes:

- **pre-commit**: Runs ruff lint checks, ruff format checks, and the full test suite. The commit is blocked if any check fails.
- **commit-msg**: Rejects commit messages that reference AI tools (Claude, Anthropic, Gemini, Codex, Copilot).

### Making Changes

1. Run `make lint` and `make tests` before committing.
2. Commit your changes. The pre-commit hook will verify everything passes.
3. If the hook fails, fix the issues and try again.

## Project Structure

```
analyzer/
├── src/
│   ├── streamlit_app.py     # UI entry point
│   ├── services.py          # Business logic and LLM calls
│   ├── orchestrator.py      # Multi-step processing coordinator
│   ├── models.py            # Django models
│   ├── auth.py              # Redis-backed session auth
│   ├── views/               # Streamlit pages
│   ├── management/          # Django management commands
│   └── migrations/
├── tests/
│   ├── unit/
│   └── functional/
├── pyproject.toml
├── Dockerfile
└── manage.py
```

### Architecture

- **Service layer**: Business logic goes in `src/services.py`. Views should be thin.
- **AI calls**: All OpenAI/LangChain interactions go through `LLMService` in `src/services.py`.
- **Orchestrator**: `src/orchestrator.py` coordinates multi-step workflows (transcribe + analyze).
- **UI**: Streamlit multi-page app. Entry point is `src/streamlit_app.py`, pages live in `src/views/`.

## Coding Standards

### Type Hints

All code must use type hints (Python 3.14+).

### Linting and Formatting

Enforced by [Ruff](https://docs.astral.sh/ruff/) with these rules: flake8-builtins, flake8-bugbear, pycodestyle, pyflakes, isort, pep8-naming, and flake8-django. Line length is 100 characters. Double quotes, space indentation.

### Testing

- Unit tests go in `tests/unit/`, functional/integration tests in `tests/functional/`.
- Use Django's `TestCase`.
- **Mock all OpenAI/LLM calls** — never make real API calls in tests.
- All data ingestion logic must be idempotent.
