---
inclusion: always
---

# Technology Stack

## Dependencies
- Python: >=3.10, <3.14
- Package Manager: UV
- Framework: CrewAI v1.2.0
- Web Framework: FastAPI >=0.104.0
- ASGI Server: Uvicorn (dev), Gunicorn + Uvicorn workers (prod)
- Google API Client (Gmail), Pydantic >=2.0, Python-dotenv

## Commands

### CLI Mode
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

### API Mode
```bash
# Development server (auto-reload)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production server
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Access documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc

# Test endpoints
curl -X POST http://localhost:8000/api/flows/gmail-read \
  -H "Content-Type: application/json" \
  -d '{"sender_emails": ["user@example.com"], "language": "en", "days": 7}'

curl http://localhost:8000/api/history?limit=10

curl http://localhost:8000/health
```

## Environment Variables
Required in `.env`:
- `OPENAI_API_KEY`: OpenAI API key
- `GMAIL_CREDENTIALS_PATH`: OAuth credentials path (supports `~` expansion)
- `GMAIL_TOKEN_PATH`: Token storage path

Optional (API Mode):
- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `API_RELOAD`: Auto-reload on code changes (default: true)
- `CORS_ORIGINS`: Comma-separated allowed origins (default: http://localhost:5173,http://localhost:3000)
- `ENVIRONMENT`: development or production (default: development)
- `HISTORY_STORAGE_DIR`: Path for analysis history (default: data/history)
- `HISTORY_MAX_FILES`: Max stored analyses (default: 100)

Never commit `.env`, `credentials.json`, or `token.json`.

## Gmail OAuth
First run opens browser for authorization. Token auto-refreshes and persists to `GMAIL_TOKEN_PATH`.
