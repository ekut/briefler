---
inclusion: always
---

# Architecture & Code Conventions

## Structure

`src/briefler/` - Main package
- `main.py` - Entry point, delegates to GmailReadFlow
- `flows/gmail_read_flow/` - Flow orchestration with state
- `crews/gmail_reader_crew/` - Crew with config/ (agents.yaml, tasks.yaml)
- `tools/` - Legacy/template tools

`src/mailbox_briefler/tools/` - Gmail API tool implementation

## CrewAI Patterns

**Flow Pattern**: Use `@start()` and `@listen()` decorators. FlowState (Pydantic) contains `sender_emails` (List[str], required), `language` (str, default "en"), `days` (int, default 7), `result` (Optional).

**Crew Pattern**: Use `@CrewBase` decorator. Config in YAML files. Methods decorated with `@agent`, `@task`, `@crew`. Sequential process by default.

**Tool Pattern**: Extend `crewai.tools.BaseTool`. Define Pydantic `args_schema` with Field descriptions. Implement `_run()`. Add retry logic with exponential backoff.

**Entry Points** (`main.py`): `kickoff()` for `crewai run`, `plot()` for visualization, `run_with_trigger()` for JSON payload. Supports legacy `sender_email` (singular).

## Code Style

**Naming**: packages `snake_case`, classes `PascalCase`, methods `snake_case`, private `_prefix`, constants `UPPERCASE`

**Docs**: Google-style docstrings with type hints throughout. All documentation (README, docstrings, comments) and code comments MUST be written in English only.

**Errors**: Retry API calls with backoff. Raise `ValueError`/`FileNotFoundError` with context. Log with `exc_info=True`. Detailed auth error messages.

**Config**: Validate `os.getenv()`. Use `os.path.expanduser()` for paths. Never commit credentials.

## Gmail API

**Auth**: OAuth 2.0 local server flow, `gmail.readonly` scope

**Rate Limiting**: Auto-retry 429 errors with backoff, handle pagination

**Message Processing**: Base64url decode with UTF-8 fallback. Parse text/plain, text/html, multipart (recursive). Strip HTML, preserve formatting. Extract attachment metadata only (no download).
