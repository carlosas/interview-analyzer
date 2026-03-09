# AI Assistant Instructions - Interview Analyzer

You are a Senior Python/Django developer. When generating code or modifications for this project, adhere to the following architectural standards and conventions.

## Project Architecture

- **Single Service**: `analyzer/` contains the Django models/services + Streamlit UI.
- **Service Layer**: Business logic belongs in `src/services.py`. Views should be thin. Check services before modifying views.
- **Orchestrator**: `src/orchestrator.py` coordinates multi-step interview processing (transcribe + analyze). Uses services synchronously with Streamlit spinners.
- **AI Integration**: All OpenAI/LangChain calls must go through `LLMService` in `src/services.py`.
- **UI**: Streamlit multi-page app. Entry point: `src/streamlit_app.py`. Views in `src/views/`.
- **Auth**: Redis-backed session auth in `src/auth.py` with rate limiting.

## Technical Stack

- **Framework**: Django ORM + Streamlit UI.
- **Dependency Management**: Poetry.
- **Linting/Formatting**: Ruff and Mypy.
- **Database**: PostgreSQL.
- **Cache/Auth Store**: Redis (django-redis cache + login rate limiting).
- **AI**: OpenAI (Whisper for transcription, GPT-4o for analysis) + LangChain.

## Coding Standards

1. **Typing**: Always use type hints (Python 3.14+).
2. **Idempotency**: All data ingestion logic must be idempotent.
3. **Testing**:
   - Unit tests in `tests/unit/`.
   - Functional/Integration tests in `tests/functional/`.
   - Use Django's built-in `TestCase`.
   - Mock all OpenAI/LLM calls in tests. Never make real API calls.
4. **Makefile**: Use `make help` to see available commands. Prioritize using make commands when possible.
