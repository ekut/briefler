---
inclusion: always
---

# Architecture & Code Conventions

## Project Structure
```
src/briefler/
├── main.py                    # kickoff(), plot(), run_with_trigger()
├── flows/gmail_read_flow/     # Flow orchestration (FlowState)
├── crews/gmail_reader_crew/   # Crew + YAML config (agents.yaml, tasks.yaml)
└── tools/                     # GmailReaderTool
```

## CrewAI Patterns

**Flow:**
- Use `@start()` and `@listen()` decorators
- FlowState (Pydantic): `sender_emails: List[str]`, `language: str = "en"`, `days: int = 7`, `result: Optional[str] = None`

**Crew:**
- Use `@CrewBase` class decorator
- Store agent/task definitions in `config/*.yaml`
- Use `@agent`, `@task`, `@crew` decorators
- Default to sequential process

**Tool:**
- Extend `crewai.tools.BaseTool`
- Define Pydantic `args_schema` with Field descriptions
- Implement `_run()` method
- Include exponential backoff for API retries

**Entry Points:**
- `kickoff()`: CLI for `crewai run`
- `plot()`: CLI for `crewai plot`
- `run_with_trigger()`: JSON payload, supports legacy `sender_email` (singular)

## Code Style

**Naming:**
- Modules: `snake_case`
- Classes: `PascalCase`
- Functions: `snake_case`
- Private: `_prefix`
- Constants: `UPPERCASE_WITH_UNDERSCORES`

**Documentation:**
- Google-style docstrings with type hints
- English only
- Include params, returns, raises

**Error Handling:**
- Exponential backoff for API retries
- Specific exceptions with descriptive messages
- Log errors with `exc_info=True`

**Configuration:**
- Validate all `os.getenv()` for required vars
- Use `os.path.expanduser()` for `~` paths
- Never commit credentials

## Gmail API

**Auth:**
- OAuth 2.0 with `gmail.readonly` scope only
- Token auto-refreshes at `GMAIL_TOKEN_PATH`

**Processing:**
- Base64url decode with UTF-8 fallback
- Parse MIME: text/plain, text/html, multipart (recursive)
- Strip HTML, preserve text formatting
- Extract attachment metadata only (no downloads)
- Retry HTTP 429 with exponential backoff
- Handle pagination
