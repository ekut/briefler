---
inclusion: always
---

# Technology Stack & Commands

## Core Dependencies

- Python: >=3.10, <3.14
- Package Manager: UV
- Build System: Hatchling
- Framework: CrewAI v1.2.0
- APIs: Google API Client (Gmail)
- Validation: Pydantic
- Config: Python-dotenv

## Common Commands

```bash
# Install dependencies
crewai install

# Run the flow
crewai run
python src/briefler/main.py

# Run with JSON payload
python src/briefler/main.py '{"sender_emails": ["user@example.com"], "days": 7, "language": "en"}'

# Visualize flow
crewai plot

# Run examples
python examples/gmail_crew_example.py
python examples/gmail_reader_example.py
```

## Environment Configuration

Required `.env` variables:

```bash
OPENAI_API_KEY=sk-...                              # OpenAI API key
GMAIL_CREDENTIALS_PATH=~/path/to/credentials.json  # OAuth credentials (~ expansion supported)
GMAIL_TOKEN_PATH=~/path/to/token.json              # Token storage location
```

Never commit `.env`, `credentials.json`, or `token.json` to version control.

## Gmail OAuth Flow

1. First run opens browser for authorization
2. Token saved to `GMAIL_TOKEN_PATH` and auto-refreshes
3. Subsequent runs use stored token
