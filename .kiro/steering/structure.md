# Project Structure

## Directory Organization

```
briefler/
├── src/
│   ├── briefler/              # Main application package
│   │   ├── main.py           # Flow entry point and orchestration
│   │   ├── crews/            # CrewAI crew definitions
│   │   │   └── gmail_reader_crew/
│   │   │       ├── config/   # Agent and task YAML configs
│   │   │       │   ├── agents.yaml
│   │   │       │   └── tasks.yaml
│   │   │       └── gmail_reader_crew.py
│   │   └── tools/            # Custom CrewAI tools (legacy/template)
│   │       └── custom_tool.py
│   └── mailbox_briefler/      # Gmail integration package
│       └── tools/
│           └── gmail_reader_tool.py  # Gmail API tool implementation
├── examples/                  # Usage examples
│   ├── gmail_crew_example.py
│   └── gmail_reader_example.py
├── tests/                     # Test directory (currently empty)
├── .env                       # Environment variables (gitignored)
├── .env.example              # Environment template
└── pyproject.toml            # Project metadata and dependencies
```

## Architecture Patterns

### CrewAI Flow Pattern

The project uses CrewAI's Flow architecture:
- **FlowState**: Pydantic model defining state passed between flow steps
- **Flow Class**: Orchestrates crew execution with decorators
  - `@start()`: Entry point method
  - `@listen(method)`: Triggered after specified method completes
- **Entry Points**: `kickoff()`, `plot()`, `run_with_trigger()`

### Crew Structure

Crews are defined using the `@CrewBase` decorator pattern:
- **Configuration**: YAML files in `config/` directory
  - `agents.yaml`: Agent roles, goals, backstories
  - `tasks.yaml`: Task descriptions and expected outputs
- **Decorators**:
  - `@agent`: Define agent methods
  - `@task`: Define task methods
  - `@crew`: Define crew composition
- **Process**: Sequential execution by default

### Tool Implementation

Custom tools extend `crewai.tools.BaseTool`:
- **Input Schema**: Pydantic model with Field descriptions
- **Attributes**: `name`, `description`, `args_schema`
- **Execution**: Implement `_run()` method
- **Error Handling**: Retry logic with exponential backoff for API calls

## Code Conventions

### Naming Conventions
- **Packages**: lowercase with underscores (`mailbox_briefler`)
- **Classes**: PascalCase (`GmailReaderTool`, `GmailReaderCrew`)
- **Methods**: snake_case with leading underscore for private (`_get_unread_messages`)
- **Constants**: UPPERCASE (`SCOPES`)

### Documentation
- **Docstrings**: Google-style format with sections:
  - Description
  - Args
  - Returns
  - Raises
- **Type Hints**: Use throughout (typing module, Optional, ClassVar)
- **Logging**: Use Python logging module with appropriate levels

### Error Handling
- **API Calls**: Wrap in retry logic with exponential backoff
- **Authentication**: Detailed error messages with recovery instructions
- **Validation**: Raise ValueError/FileNotFoundError with context
- **Logging**: Log errors with `exc_info=True` for stack traces

### Configuration Management
- **Environment Variables**: Use `os.getenv()` with validation
- **Path Expansion**: Use `os.path.expanduser()` for `~` support
- **Secrets**: Never commit credentials; use `.env` (gitignored)

## Key Implementation Details

### Gmail API Integration
- **Scopes**: Read-only access (`gmail.readonly`)
- **Authentication**: OAuth 2.0 with local server flow
- **Rate Limiting**: Automatic retry with backoff for 429 errors
- **Message Formats**: Handles text/plain, text/html, multipart
- **Pagination**: Handles large result sets with page tokens

### Message Processing
- **Decoding**: Base64url decoding with UTF-8 error handling
- **HTML Conversion**: Strip tags, preserve formatting, extract links
- **Attachments**: Extract metadata only (filename, mime_type, size)
- **Recursive Parsing**: Handle nested multipart message structures
