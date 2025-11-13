"""Health check endpoints for API monitoring."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import os
from typing import Dict, Any

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns server status and timestamp if the API is running.
    Always returns 200 if the server is operational.
    
    Returns:
        dict: Health status with timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/ready")
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint with dependency validation.
    
    Checks if the service is ready to accept requests by verifying:
    - Gmail OAuth credentials file exists
    - OpenAI API key is configured
    - History storage directory exists
    
    Returns:
        JSONResponse: Readiness status with individual check results
        - 200 if all checks pass
        - 503 if any dependency is unavailable
    """
    checks = {}
    
    # Check Gmail credentials
    gmail_creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "")
    if gmail_creds_path:
        # Expand ~ to home directory
        expanded_path = os.path.expanduser(gmail_creds_path)
        checks["gmail_credentials"] = os.path.exists(expanded_path)
    else:
        checks["gmail_credentials"] = False
    
    # Check OpenAI API key
    checks["openai_api_key"] = bool(os.getenv("OPENAI_API_KEY"))
    
    # Check history storage directory
    history_dir = os.getenv("HISTORY_STORAGE_DIR", "data/history")
    checks["history_storage"] = os.path.exists(history_dir)
    
    # Determine overall readiness
    ready = all(checks.values())
    status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": ready,
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
