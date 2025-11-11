---
inclusion: always
---

# Technology Stack & Commands

## Core Dependencies

- **Python**: >=3.10, <3.14
- **Package Manager**: UV
- **Build System**: Hatchling
- **Framework**: CrewAI v1.2.0 (multi-agent orchestration)
- **APIs**: Google API Client (Gmail integration)
- **Validation**: Pydantic
- **Config**: Python-dotenv

## Common Commands

```bash
# Install dependencies
crewai install

# Run the flow
crewai run
# OR
python src/briefler/main.py

# Run with JSON payload
python src/briefler/main.py '{"sender_emails": ["user@example.com"], "days": 7, "language": "en"}'

# Visualize flow structure
crewai plot

# Run examples
python examples/gmail_crew_example.py
python examples/gmail_reader_example.py
```

## Environment Configuration

Create `.env` file with required variables:

```bash
OPENAI_API_KEY=sk-...                           # Required: OpenAI API key
GMAIL_CREDENTIALS_PATH=~/path/to/credentials.json  # Required: OAuth credentials (supports ~ expansion)
GMAIL_TOKEN_PATH=~/path/to/token.json          # Required: Token storage location
```

**Important**: Never commit `.env`, `credentials.json`, or `token.json` to version control.

## Gmail OAuth Setup

1. First run opens browser for Google account authorization
2. Token is saved to `GMAIL_TOKEN_PATH` and auto-refreshes
3. Subsequent runs use stored token without browser interaction
