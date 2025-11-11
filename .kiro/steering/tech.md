---
inclusion: always
---

# Technology Stack

## Stack
- Python >=3.10, <3.14
- Package Manager: UV
- Build: Hatchling
- CrewAI v1.2.0 (multi-agent framework)
- Google API Client (Gmail integration)
- Pydantic (validation)
- Python-dotenv (env management)

## Commands

Install dependencies: `crewai install`

Run flow: `crewai run` or `python src/briefler/main.py`

Run with payload: `python src/briefler/main.py '{"sender_emails": ["user@example.com"], "days": 7, "language": "en"}'`

Visualize: `crewai plot`

Run examples: `python examples/gmail_crew_example.py` or `python examples/gmail_reader_example.py`

## Environment Variables

Required in `.env`:
- `OPENAI_API_KEY`: OpenAI API key
- `GMAIL_CREDENTIALS_PATH`: Path to credentials.json (supports `~` expansion)
- `GMAIL_TOKEN_PATH`: Path for token.json storage

## Gmail OAuth Flow

First run opens browser for authorization. Token auto-refreshes and persists to configured path.
