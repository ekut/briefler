# Design Document: FastAPI Backend for Briefler

## Overview

This document outlines the technical design for adding a FastAPI-based REST API backend to the Briefler application. The API Server exposes the existing `GmailReadFlow` functionality via HTTP endpoints, enabling programmatic access for future frontend clients and integrations. The design focuses on minimal disruption to existing code, clear API contracts, and developer-friendly local development.

### Design Goals

1. **Minimal Disruption**: Integrate with existing `GmailReadFlow` without modifying core logic
2. **Developer Experience**: Fast local development with auto-reload and clear error messages
3. **API Design**: RESTful endpoints with automatic OpenAPI documentation
4. **Type Safety**: Pydantic models for request/response validation
5. **Extensibility**: Architecture that supports future features (authentication, webhooks, etc.)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Clients                              │
│  (curl, Postman, future React SPA, mobile apps, etc.)       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/SSE
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              API Layer                                │  │
│  │  - POST /api/flows/gmail-read                         │  │
│  │  - GET  /api/flows/gmail-read/stream (SSE)            │  │
│  │  - GET  /api/history                                  │  │
│  │  - GET  /api/history/{analysis_id}                    │  │
│  │  - GET  /health                                       │  │
│  │  - GET  /ready                                        │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          Business Logic Layer                         │  │
│  │  - Input Validation (Pydantic)                        │  │
│  │  - Flow Orchestration Service                         │  │
│  │  - History Service                                    │  │
│  │  - Error Handling                                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Existing CrewAI Infrastructure                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           GmailReadFlow                               │  │
│  │  - FlowState Management                               │  │
│  │  - initialize() → analyze_emails()                    │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         GmailReaderCrew                               │  │
│  │  - Gmail API Integration                              │  │
│  │  - AI Analysis                                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
briefler/
├── src/
│   ├── briefler/                  # Existing CrewAI code (UNCHANGED)
│   │   ├── flows/
│   │   │   └── gmail_read_flow/
│   │   ├── crews/
│   │   │   └── gmail_reader_crew/
│   │   ├── tools/
│   │   └── main.py
│   │
│   └── api/                       # FastAPI server (NEW)
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── flows.py           # Flow endpoints
│       │   ├── history.py         # History endpoints
│       │   └── health.py          # Health check
│       ├── models/
│       │   ├── __init__.py
│       │   ├── requests.py        # Pydantic request models
│       │   └── responses.py       # Pydantic response models
│       ├── services/
│       │   ├── __init__.py
│       │   ├── flow_service.py    # Flow orchestration
│       │   └── history_service.py # History storage
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py          # Settings
│       │   └── logging.py         # Logging config
│       ├── __init__.py
│       └── main.py                # FastAPI app entry point
│
├── data/
│   └── history/                   # JSON file storage for analyses
│
├── tests/
│   ├── api/                       # API tests
│   │   ├── unit/
│   │   └── integration/
│   └── briefler/                  # Existing tests
│
├── .env                           # Environment variables
├── pyproject.toml                 # Project dependencies
└── README.md
```


## Components and Interfaces

### Backend Components

#### 1. FastAPI Application (`src/api/main.py`)

**Responsibilities:**
- Initialize FastAPI application
- Configure CORS for local development
- Register API routers
- Setup logging and error handlers
- Serve OpenAPI documentation at `/docs`

**Key Configuration:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.core.config import settings
from api.routes import flows, history, health

app = FastAPI(
    title="Briefler API",
    description="REST API for Gmail analysis using CrewAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(flows.router, prefix="/api/flows", tags=["flows"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(health.router, tags=["health"])
```

#### 2. Flow Routes (`src/api/routes/flows.py`)

**Endpoints:**

**POST `/api/flows/gmail-read`**
- Accepts: `GmailAnalysisRequest` (Pydantic model)
- Returns: `GmailAnalysisResponse` (Pydantic model)
- Executes: `GmailReadFlow` synchronously
- Status Codes: 200 (success), 400 (validation error), 500 (execution error)

**GET `/api/flows/gmail-read/stream`**
- Query Params: `sender_emails` (comma-separated), `language`, `days`
- Returns: Server-Sent Events stream
- Content-Type: `text/event-stream`
- Events: `progress`, `complete`, `error`

**Implementation Pattern:**
```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.models.requests import GmailAnalysisRequest
from api.models.responses import GmailAnalysisResponse
from api.services.flow_service import FlowService

router = APIRouter()
flow_service = FlowService()

@router.post("/gmail-read", response_model=GmailAnalysisResponse)
async def analyze_emails(request: GmailAnalysisRequest):
    """Execute Gmail analysis flow synchronously."""
    try:
        result = await flow_service.execute_flow(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gmail-read/stream")
async def analyze_emails_stream(
    sender_emails: str,
    language: str = "en",
    days: int = 7
):
    """Execute Gmail analysis flow with SSE progress updates."""
    # Parse comma-separated emails
    emails_list = [e.strip() for e in sender_emails.split(",")]
    request = GmailAnalysisRequest(
        sender_emails=emails_list,
        language=language,
        days=days
    )
    return StreamingResponse(
        flow_service.execute_flow_stream(request),
        media_type="text/event-stream"
    )
```

#### 3. History Routes (`src/api/routes/history.py`)

**Endpoints:**

**GET `/api/history`**
- Query Params: `limit` (default: 20), `offset` (default: 0)
- Returns: `HistoryListResponse` with pagination metadata
- Response: List of past analyses with metadata

**GET `/api/history/{analysis_id}`**
- Path Param: `analysis_id` (UUID)
- Returns: `GmailAnalysisResponse`
- Status Codes: 200 (found), 404 (not found)

**Implementation Pattern:**
```python
from fastapi import APIRouter, HTTPException
from api.models.responses import HistoryListResponse, GmailAnalysisResponse
from api.services.history_service import HistoryService

router = APIRouter()
history_service = HistoryService()

@router.get("", response_model=HistoryListResponse)
async def get_history(limit: int = 20, offset: int = 0):
    """Get paginated list of past analyses."""
    return await history_service.get_history(limit, offset)

@router.get("/{analysis_id}", response_model=GmailAnalysisResponse)
async def get_analysis_by_id(analysis_id: str):
    """Get specific analysis by ID."""
    result = await history_service.get_by_id(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result
```

#### 4. Health Check (`src/api/routes/health.py`)

**Endpoints:**

**GET `/health`**
- Returns: `{"status": "healthy", "timestamp": "..."}`
- Always returns 200 if server is running

**GET `/ready`**
- Checks: Gmail credentials, environment variables, file system access
- Returns: `{"ready": true/false, "checks": {...}}`
- Status Codes: 200 (ready), 503 (not ready)

**Implementation Pattern:**
```python
from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready")
async def readiness_check():
    """Check if service is ready to accept requests."""
    checks = {
        "gmail_credentials": os.path.exists(
            os.path.expanduser(os.getenv("GMAIL_CREDENTIALS_PATH", ""))
        ),
        "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "history_storage": os.path.exists("data/history")
    }
    
    ready = all(checks.values())
    status_code = 200 if ready else 503
    
    return {
        "ready": ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```


## Data Models

### Request Models (`src/api/models/requests.py`)

```python
from pydantic import BaseModel, Field, field_validator
from typing import List
import re

class GmailAnalysisRequest(BaseModel):
    """Request model for Gmail analysis."""
    
    sender_emails: List[str] = Field(
        ...,
        description="List of sender email addresses to analyze",
        min_length=1,
        examples=[["user@example.com", "another@example.com"]]
    )
    language: str = Field(
        default="en",
        description="ISO 639-1 language code for output",
        pattern="^[a-z]{2}$",
        examples=["en", "ru", "es"]
    )
    days: int = Field(
        default=7,
        description="Number of days to look back",
        ge=1,
        le=365,
        examples=[7, 14, 30]
    )
    
    @field_validator('sender_emails')
    @classmethod
    def validate_emails(cls, v: List[str]) -> List[str]:
        """Validate email format for each sender."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        validated = []
        for email in v:
            stripped = email.strip()
            if not re.match(email_pattern, stripped):
                raise ValueError(f"Invalid email format: '{email}'")
            validated.append(stripped)
        return validated
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate ISO 639-1 language code."""
        valid_codes = {
            'en', 'ru', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko',
            'ar', 'hi', 'nl', 'pl', 'tr', 'sv', 'no', 'da', 'fi', 'cs'
        }
        if v.lower() not in valid_codes:
            raise ValueError(f"Invalid language code: '{v}'")
        return v.lower()
```

### Response Models (`src/api/models/responses.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class GmailAnalysisResponse(BaseModel):
    """Response model for Gmail analysis."""
    
    analysis_id: str = Field(
        ...,
        description="Unique identifier for this analysis"
    )
    result: str = Field(
        ...,
        description="Analysis result text (markdown formatted)"
    )
    parameters: dict = Field(
        ...,
        description="Input parameters used for analysis"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the analysis was completed"
    )
    execution_time_seconds: float = Field(
        ...,
        description="Time taken to complete analysis"
    )

class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")

class HistoryItem(BaseModel):
    """History list item model."""
    
    analysis_id: str
    timestamp: datetime
    sender_count: int
    language: str
    days: int
    preview: str = Field(..., description="First 200 chars of result")

class HistoryListResponse(BaseModel):
    """History list response."""
    
    items: List[HistoryItem]
    total: int
    limit: int
    offset: int
```

## Services

### Flow Service (`src/api/services/flow_service.py`)

**Responsibilities:**
- Orchestrate `GmailReadFlow` execution
- Handle Flow state management
- Capture execution metrics (start time, end time, duration)
- Generate unique analysis IDs (UUID)
- Stream progress updates via SSE
- Save results to history

**Key Methods:**

```python
import uuid
import time
from typing import AsyncGenerator
from api.models.requests import GmailAnalysisRequest
from api.models.responses import GmailAnalysisResponse
from briefler.flows.gmail_read_flow import GmailReadFlow
from api.services.history_service import HistoryService

class FlowService:
    """Service for managing CrewAI Flow execution."""
    
    def __init__(self):
        self.history_service = HistoryService()
    
    async def execute_flow(
        self,
        request: GmailAnalysisRequest
    ) -> GmailAnalysisResponse:
        """Execute Gmail Read Flow synchronously."""
        analysis_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Prepare trigger payload
        trigger_payload = {
            "sender_emails": request.sender_emails,
            "language": request.language,
            "days": request.days
        }
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={"crewai_trigger_payload": trigger_payload})
        
        # Get result from flow state
        result_text = flow.state.result
        execution_time = time.time() - start_time
        
        # Create response
        response = GmailAnalysisResponse(
            analysis_id=analysis_id,
            result=result_text,
            parameters=trigger_payload,
            execution_time_seconds=execution_time
        )
        
        # Save to history
        await self.history_service.save(response)
        
        return response
    
    async def execute_flow_stream(
        self,
        request: GmailAnalysisRequest
    ) -> AsyncGenerator[str, None]:
        """Execute Gmail Read Flow with SSE progress updates."""
        analysis_id = str(uuid.uuid4())
        
        try:
            # Send initial progress event
            yield f"event: progress\ndata: Initializing analysis...\n\n"
            
            # Execute flow (in future, can hook into flow events)
            result = await self.execute_flow(request)
            
            # Send completion event
            import json
            yield f"event: complete\ndata: {json.dumps(result.dict())}\n\n"
            
        except Exception as e:
            # Send error event
            yield f"event: error\ndata: {str(e)}\n\n"
```

### History Service (`src/api/services/history_service.py`)

**Responsibilities:**
- Persist analysis results to JSON files
- Retrieve analysis history with pagination
- Manage storage limits (100 most recent)
- Generate analysis previews (first 200 chars)
- Handle file I/O operations

**Storage Format:**
```json
{
  "analysis_id": "uuid-here",
  "timestamp": "2025-11-11T10:30:00Z",
  "parameters": {
    "sender_emails": ["user@example.com"],
    "language": "en",
    "days": 7
  },
  "result": "Full analysis text...",
  "execution_time_seconds": 45.2
}
```

**Storage Location:** `data/history/{analysis_id}.json`

**Key Methods:**

```python
import os
import json
from typing import List, Optional
from datetime import datetime
from api.models.responses import GmailAnalysisResponse, HistoryItem, HistoryListResponse

class HistoryService:
    """Service for managing analysis history storage."""
    
    def __init__(self, storage_dir: str = "data/history"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    async def save(self, response: GmailAnalysisResponse) -> None:
        """Save analysis result to JSON file."""
        file_path = os.path.join(self.storage_dir, f"{response.analysis_id}.json")
        
        data = {
            "analysis_id": response.analysis_id,
            "timestamp": response.timestamp.isoformat(),
            "parameters": response.parameters,
            "result": response.result,
            "execution_time_seconds": response.execution_time_seconds
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Cleanup old files if exceeding limit
        await self._cleanup_old_files()
    
    async def get_history(self, limit: int = 20, offset: int = 0) -> HistoryListResponse:
        """Get paginated list of past analyses."""
        files = sorted(
            [f for f in os.listdir(self.storage_dir) if f.endswith('.json')],
            key=lambda x: os.path.getmtime(os.path.join(self.storage_dir, x)),
            reverse=True
        )
        
        total = len(files)
        paginated_files = files[offset:offset + limit]
        
        items = []
        for filename in paginated_files:
            file_path = os.path.join(self.storage_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            items.append(HistoryItem(
                analysis_id=data["analysis_id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                sender_count=len(data["parameters"]["sender_emails"]),
                language=data["parameters"]["language"],
                days=data["parameters"]["days"],
                preview=data["result"][:200] + "..." if len(data["result"]) > 200 else data["result"]
            ))
        
        return HistoryListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )
    
    async def get_by_id(self, analysis_id: str) -> Optional[GmailAnalysisResponse]:
        """Get specific analysis by ID."""
        file_path = os.path.join(self.storage_dir, f"{analysis_id}.json")
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return GmailAnalysisResponse(
            analysis_id=data["analysis_id"],
            result=data["result"],
            parameters=data["parameters"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            execution_time_seconds=data["execution_time_seconds"]
        )
    
    async def _cleanup_old_files(self, max_files: int = 100) -> None:
        """Remove oldest files if exceeding limit."""
        files = sorted(
            [f for f in os.listdir(self.storage_dir) if f.endswith('.json')],
            key=lambda x: os.path.getmtime(os.path.join(self.storage_dir, x)),
            reverse=True
        )
        
        if len(files) > max_files:
            for filename in files[max_files:]:
                os.remove(os.path.join(self.storage_dir, filename))
```


## Configuration

### Settings (`src/api/core/config.py`)

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Storage Configuration
    HISTORY_STORAGE_DIR: str = "data/history"
    HISTORY_MAX_FILES: int = 100
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Environment Variables (`.env`)

```bash
# OpenAI API Key (required by CrewAI)
OPENAI_API_KEY=sk-...

# Gmail OAuth Credentials (required by GmailReaderTool)
GMAIL_CREDENTIALS_PATH=~/path/to/credentials.json
GMAIL_TOKEN_PATH=~/path/to/token.json

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Environment
ENVIRONMENT=development
```

## Error Handling

### Backend Error Handling Strategy

**1. Validation Errors (400)**
- Pydantic validation failures return detailed field errors
- Example: Invalid email format, invalid language code

**2. Flow Execution Errors (500)**
- Catch exceptions from `GmailReadFlow`
- Log full stack trace for debugging
- Return sanitized error message to client

**3. Gmail API Errors**
- Specific handling for auth failures, quota limits, network errors
- Return appropriate HTTP status codes

**4. File System Errors**
- Handle history storage failures gracefully
- Log errors but don't fail the analysis

**5. Unexpected Errors**
- Global exception handler logs full context
- Returns generic error message to prevent information leakage

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid input parameters",
  "details": {
    "sender_emails": ["Invalid email format: 'not-an-email'"]
  }
}
```

### Global Exception Handler

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "ValidationError",
            "message": "Invalid input parameters",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": None if settings.ENVIRONMENT == "production" else str(exc)
        }
    )
```

## Testing Strategy

### Backend Testing

**Unit Tests:**
- Pydantic model validation logic
- Flow service methods (mocked Flow execution)
- History service CRUD operations
- Utility functions

**Integration Tests:**
- API endpoint responses
- Flow execution with test data
- SSE streaming functionality
- CORS configuration
- Error handling scenarios

**Tools:**
- `pytest` for test framework
- `pytest-asyncio` for async tests
- `httpx` for API client testing
- `pytest-cov` for coverage reports

**Test Structure:**
```
tests/api/
├── unit/
│   ├── test_models.py
│   ├── test_flow_service.py
│   └── test_history_service.py
├── integration/
│   ├── test_flows_api.py
│   ├── test_history_api.py
│   ├── test_health_api.py
│   └── test_sse.py
├── conftest.py
└── __init__.py
```

**Example Test:**
```python
import pytest
from httpx import AsyncClient
from api.main import app

@pytest.mark.asyncio
async def test_analyze_emails_success():
    """Test successful email analysis."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/flows/gmail-read",
            json={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "result" in data
    assert data["parameters"]["language"] == "en"

@pytest.mark.asyncio
async def test_analyze_emails_invalid_email():
    """Test validation error for invalid email."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/flows/gmail-read",
            json={
                "sender_emails": ["not-an-email"],
                "language": "en",
                "days": 7
            }
        )
    
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "ValidationError"
```

## Security Considerations

### Development Mode (Current Scope)

**Assumptions:**
- Running on localhost only
- No public network exposure
- Single user (developer)

**Security Measures:**
1. **Input Validation**: Strict Pydantic validation prevents injection attacks
2. **CORS**: Restricted to localhost origins
3. **Logging**: No sensitive data (emails, credentials) logged
4. **Environment Variables**: Gmail credentials stored in `.env`, never committed
5. **Error Messages**: Sanitized error messages in production mode

### Production Mode (Future)

**Required Additions:**
1. **Authentication**: JWT-based auth with secure token storage
2. **HTTPS**: TLS encryption for all traffic
3. **Rate Limiting**: Prevent abuse of API endpoints
4. **API Keys**: Require API keys for all requests
5. **Audit Logging**: Log all API access with user identification

## Performance Considerations

### Backend Performance

**Optimization Strategies:**
1. **Async Execution**: Use FastAPI's async capabilities for I/O operations
2. **Connection Pooling**: Reuse Gmail API connections (handled by existing tool)
3. **Streaming**: Use SSE to avoid blocking on long-running analyses
4. **File I/O**: Async file operations for history storage

**Expected Performance:**
- API response time: < 100ms (excluding Flow execution)
- Flow execution time: 30-60 seconds (depends on email count and AI processing)
- SSE latency: < 500ms per progress update
- History retrieval: < 50ms for 20 items

**Monitoring:**
- Log execution times for all operations
- Track Flow execution duration
- Monitor file system usage for history storage

## Deployment and Development

### Local Development Setup

**1. Install Dependencies:**
```bash
# Already installed via uv/pip in project root
# API dependencies are part of pyproject.toml
```

**2. Configure Environment:**
Create `.env` file in project root:
```bash
OPENAI_API_KEY=sk-...
GMAIL_CREDENTIALS_PATH=~/path/to/credentials.json
GMAIL_TOKEN_PATH=~/path/to/token.json
ENVIRONMENT=development
```

**3. Run Development Server:**
```bash
# From project root
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**4. Access API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Production Deployment (Future)

**1. Build:**
```bash
# Dependencies already in pyproject.toml
pip install -e .
```

**2. Run with Gunicorn:**
```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**3. Environment:**
- Set `ENVIRONMENT=production`
- Use production-grade ASGI server (Gunicorn + Uvicorn workers)
- Configure reverse proxy (nginx, Caddy)
- Setup SSL/TLS certificates

## Technology Stack Summary

### Backend
- **Framework**: FastAPI 0.104+
- **Python**: 3.11+
- **Validation**: Pydantic 2.0+
- **ASGI Server**: Uvicorn (development), Gunicorn + Uvicorn (production)
- **Testing**: pytest, pytest-asyncio, httpx
- **Logging**: Python logging module

### Dependencies
```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
```

## API Documentation

FastAPI automatically generates OpenAPI documentation:

**Swagger UI:** http://localhost:8000/docs
- Interactive API testing
- Request/response examples
- Schema definitions

**ReDoc:** http://localhost:8000/redoc
- Clean, readable documentation
- Detailed schema information

## Future Enhancements

### Phase 2 Features
1. **Authentication**: JWT-based user authentication
2. **WebSocket Support**: Real-time bidirectional communication
3. **Database Storage**: PostgreSQL instead of JSON files
4. **Caching**: Redis for frequently accessed analyses
5. **Rate Limiting**: Prevent API abuse
6. **Webhooks**: Notify external systems on completion

### Phase 3 Features
1. **Multi-tenancy**: Support for multiple organizations
2. **API Versioning**: v1, v2 endpoints
3. **GraphQL API**: Alternative to REST
4. **Metrics**: Prometheus metrics endpoint
5. **Distributed Tracing**: OpenTelemetry integration

## Design Decisions and Rationale

### Why FastAPI?
- Native async support for long-running Flow execution
- Automatic OpenAPI documentation (Swagger UI, ReDoc)
- Pydantic integration for type safety and validation
- High performance (comparable to Node.js, Go)
- Modern Python features (type hints, async/await)
- Large ecosystem and active community

### Why JSON File Storage?
- Simple implementation for MVP
- No additional database dependencies
- Easy to inspect and debug
- Sufficient for single-user local development
- Can migrate to database later without API changes
- Portable and version-control friendly

### Why SSE over WebSockets?
- Simpler protocol for one-way server-to-client streaming
- Built-in reconnection in browsers
- Works with standard HTTP infrastructure
- Sufficient for progress updates use case
- Lower overhead than WebSockets

### Why `src/api/` Structure?
- All source code under `src/` (Python best practice)
- Clear separation: `briefler` (CrewAI) vs `api` (FastAPI)
- Easy imports: `from briefler.flows import ...` and `from api.services import ...`
- Consistent with existing `src/briefler/` structure
- No monolith - modules are independent but in same source tree

## Conclusion

This design provides a solid foundation for exposing Briefler functionality via a REST API while maintaining the integrity of the existing CrewAI Flow architecture. The FastAPI-based backend offers modern, performant, and maintainable solutions with automatic documentation and type safety. The design prioritizes developer experience for local development while laying groundwork for future production deployment and feature enhancements.

The placement of the API under `src/api/` maintains consistency with the existing `src/briefler/` structure while providing clear separation of concerns. This allows for independent development and testing of the API layer, while the integration with the existing `GmailReadFlow` ensures minimal disruption to the core application logic. The JSON-based history storage provides a simple yet effective solution for the MVP, with a clear migration path to more robust storage solutions in the future.
