---
inclusion: always
---

# Architecture & Code Conventions

## Project Structure

```
src/briefler/
├── main.py                          # Entry point: kickoff(), plot(), run_with_trigger()
├── flows/gmail_read_flow/           # Flow orchestration with FlowState
├── crews/gmail_reader_crew/         # Crew implementation
│   └── config/                      # agents.yaml, tasks.yaml
└── tools/                           # GmailReaderTool implementation
```

## CrewAI Framework Patterns

### Flow Pattern
- Use `@start()` and `@listen()` decorators
- FlowState (Pydantic model) fields: `sender_emails: List[str]`, `language: str = "en"`, `days: int = 7`, `result: Optional[str] = None`

### Crew Pattern
- Decorate class with `@CrewBase`
- Store config in YAML files (agents.yaml, tasks.yaml)
- Use decorators: `@agent`, `@task`, `@crew`
- Default to sequential process execution

### Tool Pattern
- Extend `crewai.tools.BaseTool`
- Define Pydantic `args_schema` with Field descriptions for all parameters
- Implement `_run()` method with business logic
- Include exponential backoff retry for API calls

### Entry Points (main.py)
- `kickoff()`: Used by `crewai run`
- `plot()`: Used by `crewai plot`
- `run_with_trigger()`: Accepts JSON payload, supports legacy `sender_email` (singular)

## Code Style

### Naming
- Packages/modules: `snake_case`
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Private members: `_prefix`
- Constants: `UPPERCASE_WITH_UNDERSCORES`

### Documentation
- Google-style docstrings with complete type hints
- All documentation in English only
- Include parameter descriptions, return types, raised exceptions

### Error Handling
- Retry API calls with exponential backoff
- Raise specific exceptions (`ValueError`, `FileNotFoundError`) with descriptive messages
- Log errors with `exc_info=True`

### Configuration
- Validate all `os.getenv()` calls for required variables
- Use `os.path.expanduser()` for paths supporting `~`
- Never commit credentials or tokens

## Gmail API Integration

### Authentication
- OAuth 2.0 local server flow with `gmail.readonly` scope
- First run opens browser, token auto-refreshes and persists

### Message Processing
- Base64url decode with UTF-8 fallback
- Parse MIME types: text/plain, text/html, multipart (recursive)
- Strip HTML tags, preserve text formatting
- Extract attachment metadata only (filename, size, type) - never download content
- Auto-retry HTTP 429 with exponential backoff
- Handle pagination for large result sets
