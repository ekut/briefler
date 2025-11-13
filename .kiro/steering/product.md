---
inclusion: always
---

# Product: Briefler

AI-powered email analysis using CrewAI. Fetches unread Gmail from specified senders and generates structured summaries with insights and action items.

## Architecture

**Two Access Modes:**
1. **CLI Mode**: Direct Python execution via `crewai run` or `python src/briefler/main.py`
2. **API Mode**: REST API via FastAPI server at `http://localhost:8000`

## Core Behavior

**Email Processing:**
- Filter unread emails by sender list within time window (default: 7 days)
- Process MIME: text/plain, text/html, multipart/nested
- Base64url decode with UTF-8 fallback
- Extract attachment metadata only (filename, size, type) - never download
- Strip HTML, preserve text formatting

**Output:**
- Multilingual summaries using ISO 639-1 codes
- Structured with insights and action items
- Default language: English ("en")

## API Contract

### REST API Endpoints

**POST `/api/flows/gmail-read`**
- Executes email analysis synchronously
- Returns complete analysis result with metadata

**GET `/api/flows/gmail-read/stream`**
- Executes email analysis with Server-Sent Events (SSE)
- Streams progress updates in real-time

**GET `/api/history`**
- Returns paginated list of past analyses
- Query params: `limit` (default: 20), `offset` (default: 0)

**GET `/api/history/{analysis_id}`**
- Returns specific analysis by UUID

**GET `/health`**
- Basic health check (always returns 200 if server running)

**GET `/ready`**
- Readiness check (validates Gmail credentials, env vars, storage)

### Input Parameters

**Request Body (POST) / Query Params (GET):**
- `sender_emails`: List[str] - Required
- `language`: str - Optional, ISO 639-1 (default: "en")
- `days`: int - Optional, lookback period (default: 7)

**Legacy:**
- `sender_email` (singular) supported but deprecated - convert to `sender_emails` list

### Response Format

```json
{
  "analysis_id": "uuid",
  "result": "markdown formatted analysis",
  "parameters": {
    "sender_emails": ["user@example.com"],
    "language": "en",
    "days": 7
  },
  "timestamp": "2025-11-12T10:30:00Z",
  "execution_time_seconds": 45.2
}
```

## History Storage

- Analyses persisted to `data/history/{analysis_id}.json`
- Automatic cleanup: keeps 100 most recent analyses
- Each file contains full analysis result and metadata

## Security

- Use `gmail.readonly` scope only - never modify emails
- Store credentials locally - never commit `.env`, `credentials.json`, `token.json`
- OAuth: first run opens browser, token auto-refreshes
- Exponential backoff for HTTP 429
- Handle malformed emails gracefully
