---
inclusion: always
---

# Architecture & Code Conventions

## Project Structure
```
src/
├── briefler/                  # CrewAI Core (CLI Mode)
│   ├── main.py                # kickoff(), plot(), run_with_trigger()
│   ├── flows/gmail_read_flow/ # Flow orchestration (FlowState)
│   ├── crews/gmail_reader_crew/ # Crew + YAML config (agents.yaml, tasks.yaml)
│   └── tools/                 # GmailReaderTool
│
└── api/                       # FastAPI Server (API Mode)
    ├── main.py                # FastAPI app entry point
    ├── routes/                # API endpoints
    │   ├── flows.py           # POST /api/flows/gmail-read, GET /stream
    │   ├── history.py         # GET /api/history, GET /{id}
    │   └── health.py          # GET /health, GET /ready
    ├── models/                # Pydantic schemas
    │   ├── requests.py        # GmailAnalysisRequest
    │   └── responses.py       # GmailAnalysisResponse, HistoryListResponse
    ├── services/              # Business logic
    │   ├── flow_service.py    # Flow orchestration, SSE streaming
    │   └── history_service.py # JSON file storage (data/history/)
    └── core/                  # Configuration
        ├── config.py          # Settings (Pydantic BaseSettings)
        └── logging.py         # Logging configuration

data/
└── history/                   # Analysis results (JSON files)
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

## FastAPI Patterns

**Application Structure:**
- Main app in `src/api/main.py` with CORS middleware
- Routers organized by domain: flows, history, health
- Automatic OpenAPI docs at `/docs` and `/redoc`

**Request/Response Models:**
- Use Pydantic models for validation
- Define in `api/models/requests.py` and `api/models/responses.py`
- Include Field descriptions and examples for OpenAPI docs
- Use `@field_validator` for custom validation logic

**Services:**
- Business logic in `api/services/`
- `FlowService`: Orchestrates GmailReadFlow execution, generates UUIDs, tracks metrics
- `HistoryService`: Manages JSON file storage in `data/history/`

**Error Handling:**
- Global exception handlers for validation and unexpected errors
- Return structured error responses: `{"error": "...", "message": "...", "details": {...}}`
- Log full stack traces with `exc_info=True`
- Sanitize error messages in production mode

**Streaming:**
- Use Server-Sent Events (SSE) for long-running operations
- Return `StreamingResponse` with `media_type="text/event-stream"`
- Event format: `event: {type}\ndata: {json}\n\n`
- Event types: `progress`, `complete`, `error`

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
- API settings via Pydantic BaseSettings (auto-loads from `.env`)

## Testing

**API Tests:**
- Use `pytest` with `pytest-asyncio` for async tests
- Use `httpx.AsyncClient` for API endpoint testing
- Test structure: `tests/api/` with unit and integration tests
- Mock Flow execution in unit tests
- Integration tests validate full request/response cycle
- Test CORS, validation errors, SSE streaming, error handling

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
