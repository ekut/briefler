---
inclusion: always
---

# Technology Stack

## Dependencies
- Python: >=3.10, <3.14
- Package Manager: UV
- Framework: CrewAI v1.2.0
- Google API Client (Gmail), Pydantic, Python-dotenv

## Commands
```bash
# Install
crewai install

# Run
crewai run
python src/briefler/main.py
python src/briefler/main.py '{"sender_emails": ["user@example.com"], "days": 7, "language": "en"}'

# Visualize
crewai plot

# Examples
python examples/gmail_crew_example.py
python examples/gmail_reader_example.py
```

## Environment Variables
Required in `.env`:
- `OPENAI_API_KEY`: OpenAI API key
- `GMAIL_CREDENTIALS_PATH`: OAuth credentials path (supports `~` expansion)
- `GMAIL_TOKEN_PATH`: Token storage path

Never commit `.env`, `credentials.json`, or `token.json`.

## Gmail OAuth
First run opens browser for authorization. Token auto-refreshes and persists to `GMAIL_TOKEN_PATH`.
