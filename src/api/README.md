# Briefler API

REST API backend for the Briefler Gmail analysis application. Exposes CrewAI Flow functionality via HTTP endpoints with automatic OpenAPI documentation.

## Quick Start

### Prerequisites

- Python >=3.10, <3.14
- UV package manager installed
- Gmail OAuth credentials configured
- OpenAI API key

### Installation

Dependencies are managed at the project root level:

```bash
# From project root
crewai install
```

### Configuration

Create a `.env` file in the project root with the following variables:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=sk-...

# Required: Gmail OAuth Credentials
GMAIL_CREDENTIALS_PATH=~/path/to/credentials.json
GMAIL_TOKEN_PATH=~/path/to/token.json

# Optional: API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Optional: CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Optional: Environment
ENVIRONMENT=development
```

**Important:** Never commit `.env`, `credentials.json`, or `token.json` to version control.

### Running the Server

Start the development server with auto-reload:

```bash
# From project root
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, access the interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Flow Endpoints

#### POST `/api/flows/gmail-read`

Execute Gmail analysis flow synchronously.

**Request Body:**
```json
{
  "sender_emails": ["user@example.com", "another@example.com"],
  "language": "en",
  "days": 7
}
```

**Parameters:**
- `sender_emails` (required): List of email addresses to analyze
- `language` (optional): ISO 639-1 language code (default: "en")
- `days` (optional): Number of days to look back, 1-365 (default: 7)

**Response (200 OK):**
```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": "# Email Analysis\n\n## Summary\n...",
  "parameters": {
    "sender_emails": ["user@example.com"],
    "language": "en",
    "days": 7
  },
  "timestamp": "2025-11-12T10:30:00Z",
  "execution_time_seconds": 45.2
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "ValidationError",
  "message": "Invalid input parameters",
  "details": {
    "sender_emails": ["Invalid email format: 'not-an-email'"]
  }
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8000/api/flows/gmail-read \
  -H "Content-Type: application/json" \
  -d '{
    "sender_emails": ["user@example.com"],
    "language": "en",
    "days": 7
  }'
```

#### GET `/api/flows/gmail-read/stream`

Execute Gmail analysis flow with Server-Sent Events (SSE) for real-time progress updates.

**Query Parameters:**
- `sender_emails` (required): Comma-separated list of email addresses
- `language` (optional): ISO 639-1 language code (default: "en")
- `days` (optional): Number of days to look back, 1-365 (default: 7)

**Response:** Server-Sent Events stream

**Event Types:**
- `progress`: Status updates during execution
- `complete`: Final result with full analysis
- `error`: Error information if execution fails

**Example with curl:**
```bash
curl -N http://localhost:8000/api/flows/gmail-read/stream?sender_emails=user@example.com&language=en&days=7
```

**Example SSE Output:**
```
event: progress
data: Initializing analysis...

event: complete
data: {"analysis_id":"550e8400-e29b-41d4-a716-446655440000","result":"# Email Analysis...","parameters":{"sender_emails":["user@example.com"],"language":"en","days":7},"timestamp":"2025-11-12T10:30:00Z","execution_time_seconds":45.2}
```

### History Endpoints

#### GET `/api/history`

Retrieve paginated list of past analyses.

**Query Parameters:**
- `limit` (optional): Number of items per page (default: 20)
- `offset` (optional): Number of items to skip (default: 0)

**Response (200 OK):**
```json
{
  "items": [
    {
      "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2025-11-12T10:30:00Z",
      "sender_count": 2,
      "language": "en",
      "days": 7,
      "preview": "# Email Analysis\n\n## Summary\nYou received 15 emails from 2 senders..."
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**Example with curl:**
```bash
# Get first page (20 items)
curl http://localhost:8000/api/history

# Get second page with custom limit
curl http://localhost:8000/api/history?limit=10&offset=10
```

#### GET `/api/history/{analysis_id}`

Retrieve specific analysis by ID.

**Path Parameters:**
- `analysis_id` (required): UUID of the analysis

**Response (200 OK):**
```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": "# Email Analysis\n\n## Summary\n...",
  "parameters": {
    "sender_emails": ["user@example.com"],
    "language": "en",
    "days": 7
  },
  "timestamp": "2025-11-12T10:30:00Z",
  "execution_time_seconds": 45.2
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Analysis not found"
}
```

**Example with curl:**
```bash
curl http://localhost:8000/api/history/550e8400-e29b-41d4-a716-446655440000
```

### Health Check Endpoints

#### GET `/health`

Basic health check to verify server is running.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T10:30:00Z"
}
```

**Example with curl:**
```bash
curl http://localhost:8000/health
```

#### GET `/ready`

Readiness check that verifies all dependencies are available.

**Response (200 OK):**
```json
{
  "ready": true,
  "checks": {
    "gmail_credentials": true,
    "openai_api_key": true,
    "history_storage": true
  },
  "timestamp": "2025-11-12T10:30:00Z"
}
```

**Response (503 Service Unavailable):**
```json
{
  "ready": false,
  "checks": {
    "gmail_credentials": false,
    "openai_api_key": true,
    "history_storage": true
  },
  "timestamp": "2025-11-12T10:30:00Z"
}
```

**Example with curl:**
```bash
curl http://localhost:8000/ready
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for CrewAI agents |
| `GMAIL_CREDENTIALS_PATH` | Yes | - | Path to Gmail OAuth credentials JSON file (supports `~`) |
| `GMAIL_TOKEN_PATH` | Yes | - | Path to store Gmail OAuth token (supports `~`) |
| `API_HOST` | No | `0.0.0.0` | Host address for API server |
| `API_PORT` | No | `8000` | Port for API server |
| `API_RELOAD` | No | `true` | Enable auto-reload in development |
| `CORS_ORIGINS` | No | `http://localhost:5173,http://localhost:3000` | Comma-separated list of allowed CORS origins |
| `HISTORY_STORAGE_DIR` | No | `data/history` | Directory for storing analysis history |
| `HISTORY_MAX_FILES` | No | `100` | Maximum number of history files to retain |
| `ENVIRONMENT` | No | `development` | Environment mode (`development` or `production`) |

## Supported Language Codes

The API supports the following ISO 639-1 language codes for the `language` parameter:

`en`, `ru`, `es`, `fr`, `de`, `it`, `pt`, `zh`, `ja`, `ko`, `ar`, `hi`, `nl`, `pl`, `tr`, `sv`, `no`, `da`, `fi`, `cs`

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid input parameters (validation error)
- `404 Not Found`: Resource not found (e.g., analysis ID doesn't exist)
- `500 Internal Server Error`: Server error during flow execution
- `503 Service Unavailable`: Dependencies not available (readiness check failed)

### Error Response Format

All errors follow a consistent JSON format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "field_name": ["Specific validation error"]
  }
}
```

## Development Tips

### Testing with curl

```bash
# Test health check
curl http://localhost:8000/health

# Test readiness check
curl http://localhost:8000/ready

# Test email analysis
curl -X POST http://localhost:8000/api/flows/gmail-read \
  -H "Content-Type: application/json" \
  -d '{"sender_emails": ["user@example.com"], "language": "en", "days": 7}'

# Test SSE streaming
curl -N http://localhost:8000/api/flows/gmail-read/stream?sender_emails=user@example.com&days=7

# Get analysis history
curl http://localhost:8000/api/history

# Get specific analysis
curl http://localhost:8000/api/history/YOUR_ANALYSIS_ID
```

### Testing with Python

```python
import requests

# Synchronous analysis
response = requests.post(
    "http://localhost:8000/api/flows/gmail-read",
    json={
        "sender_emails": ["user@example.com"],
        "language": "en",
        "days": 7
    }
)
result = response.json()
print(f"Analysis ID: {result['analysis_id']}")
print(f"Result: {result['result']}")

# Get history
history = requests.get("http://localhost:8000/api/history").json()
print(f"Total analyses: {history['total']}")
```

### Testing SSE with Python

```python
import requests

url = "http://localhost:8000/api/flows/gmail-read/stream"
params = {
    "sender_emails": "user@example.com",
    "language": "en",
    "days": 7
}

with requests.get(url, params=params, stream=True) as response:
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
```

## CORS Configuration

The API is configured to accept requests from localhost origins during development:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (React/Next.js default)

To add additional origins, update the `CORS_ORIGINS` environment variable:

```bash
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8080
```

## Storage

Analysis results are stored as JSON files in `data/history/` directory:
- Each analysis is saved with its UUID as the filename
- Maximum of 100 most recent analyses are retained
- Older analyses are automatically deleted when limit is exceeded

## Troubleshooting

### Server won't start

1. Check that all required environment variables are set in `.env`
2. Verify Gmail credentials file exists at `GMAIL_CREDENTIALS_PATH`
3. Ensure port 8000 is not already in use

### Readiness check fails

Run the readiness endpoint to see which dependencies are missing:

```bash
curl http://localhost:8000/ready
```

Common issues:
- `gmail_credentials: false` - Check `GMAIL_CREDENTIALS_PATH` points to valid file
- `openai_api_key: false` - Verify `OPENAI_API_KEY` is set in `.env`
- `history_storage: false` - Ensure `data/history/` directory exists

### Gmail authentication fails

On first run, the Gmail OAuth flow will open a browser window for authorization. The token is saved to `GMAIL_TOKEN_PATH` and will auto-refresh on subsequent runs.

If authentication fails:
1. Delete the token file at `GMAIL_TOKEN_PATH`
2. Restart the API server
3. Complete the OAuth flow in the browser

## Production Deployment

For production deployment, consider:

1. **Use production ASGI server:**
```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. **Set environment to production:**
```bash
ENVIRONMENT=production
```

3. **Configure reverse proxy** (nginx, Caddy) with SSL/TLS

4. **Implement authentication** (not included in current version)

5. **Setup monitoring and logging**

## Architecture

The API is organized into the following layers:

- **Routes** (`routes/`): HTTP endpoint definitions
- **Models** (`models/`): Pydantic request/response schemas
- **Services** (`services/`): Business logic and flow orchestration
- **Core** (`core/`): Configuration and logging

The API integrates with the existing CrewAI infrastructure:
- `GmailReadFlow` from `briefler.flows.gmail_read_flow`
- `GmailReaderCrew` for email analysis
- `GmailReaderTool` for Gmail API access

## License

Same as parent Briefler project.
