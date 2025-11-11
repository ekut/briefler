---
inclusion: always
---

# Architecture & Code Conventions

## Project Structure

```
src/briefler/
├── main.py                          # Entry point with kickoff(), plot(), run_with_trigger()
├── flows/gmail_read_flow/           # Flow orchestration with FlowState
├── crews/gmail_reader_crew/         # Crew implementation
│   └── config/                      # agents.yaml, tasks.yaml
└── tools/                           # GmailReaderTool implementation
```

## CrewAI Framework Patterns

### Flow Pattern
- Use `@start()` and `@listen()` decorators for flow methods
- Define FlowState as Pydantic model with fields:
  - `sender_emails: List[str]` (required)
  - `language: str = "en"`
  - `days: int = 7`
  - `result: Optional[str] = None`

### Crew Pattern
- Decorate class with `@CrewBase`
- Store configuration in YAML files (agents.yaml, tasks.yaml)
- Use decorators: `@agent`, `@task`, `@crew`
- Default to sequential process execution

### Tool Pattern
- Extend `crewai.tools.BaseTool`
- Define Pydantic `args_schema` with Field descriptions for all parameters
- Implement `_run()` method with business logic
- Include exponential backoff retry logic for API calls

### Entry Points (main.py)
- `kickoff()`: Used by `crewai run` command
- `plot()`: Used by `crewai plot` for visualization
- `run_with_trigger()`: Accepts JSON payload, supports legacy `sender_email` (singular)

## Code Style

### Naming Conventions
- Packages/modules: `snake_case`
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Private members: `_prefix`
- Constants: `UPPERCASE_WITH_UNDERSCORES`

### Documentation
- Use Google-style docstrings with complete type hints
- All documentation (README, docstrings, comments) MUST be in English only
- Include parameter descriptions, return types, and raised exceptions

### Error Handling
- Retry API calls with exponential backoff
- Raise specific exceptions (`ValueError`, `FileNotFoundError`) with descriptive messages
- Log errors with `exc_info=True` for stack traces
- Provide detailed authentication error messages

### Configuration
- Validate all `os.getenv()` calls for required variables
- Use `os.path.expanduser()` for file paths supporting `~`
- Never commit credentials or tokens to version control

## Gmail API Integration

### Authentication
- OAuth 2.0 local server flow
- Scope: `gmail.readonly` (read-only access)
- First run opens browser for authorization
- Token auto-refreshes and persists

### Rate Limiting
- Auto-retry HTTP 429 errors with exponential backoff
- Handle pagination for large result sets

### Message Processing
- Base64url decode message bodies with UTF-8 fallback
- Parse MIME types: text/plain, text/html, multipart (recursive)
- Strip HTML tags while preserving text formatting
- Extract attachment metadata only (filename, size, type) - do not download content
