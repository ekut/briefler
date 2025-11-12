"""Flow execution endpoints for the Briefler API.

This module provides HTTP endpoints for executing the GmailReadFlow,
including both synchronous POST requests and Server-Sent Events (SSE)
streaming for real-time progress updates.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List

from api.models.requests import GmailAnalysisRequest
from api.models.responses import GmailAnalysisResponse, ErrorResponse
from api.services.flow_service import FlowService


logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize flow service
flow_service = FlowService()


@router.post(
    "/gmail-read",
    response_model=GmailAnalysisResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Validation error - invalid input parameters"
        },
        500: {
            "model": ErrorResponse,
            "description": "Execution error - flow execution failed"
        }
    },
    summary="Execute Gmail analysis flow",
    description=(
        "Executes the Gmail Read Flow synchronously to analyze unread emails "
        "from specified senders. Returns the complete analysis result with "
        "summaries, insights, and action items."
    )
)
async def analyze_emails(request: GmailAnalysisRequest) -> GmailAnalysisResponse:
    """Execute Gmail analysis flow synchronously.
    
    Accepts a request with sender emails, language preference, and time window,
    then executes the CrewAI Flow to fetch and analyze emails. The analysis
    result is persisted to history and returned in the response.
    
    Args:
        request: GmailAnalysisRequest containing:
            - sender_emails: List of email addresses to analyze
            - language: ISO 639-1 language code (default: "en")
            - days: Number of days to look back (default: 7, range: 1-365)
    
    Returns:
        GmailAnalysisResponse with analysis results and metadata
    
    Raises:
        HTTPException 400: If input validation fails
        HTTPException 500: If flow execution encounters an error
    """
    try:
        logger.info(
            f"Received analysis request for {len(request.sender_emails)} sender(s), "
            f"language={request.language}, days={request.days}"
        )
        
        # Execute flow
        result = await flow_service.execute_flow(request)
        
        logger.info(f"Analysis completed successfully: {result.analysis_id}")
        
        return result
        
    except ValueError as e:
        # Validation errors from flow execution
        logger.warning(f"Validation error in flow execution: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "details": None
            }
        )
        
    except Exception as e:
        # Unexpected errors during flow execution
        logger.error(f"Flow execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "An error occurred during flow execution",
                "details": str(e)
            }
        )


@router.get(
    "/gmail-read/stream",
    responses={
        200: {
            "description": "Server-Sent Events stream with progress updates",
            "content": {
                "text/event-stream": {
                    "example": (
                        "event: progress\n"
                        "data: {\"status\": \"Initializing analysis...\", \"analysis_id\": \"uuid\"}\n\n"
                        "event: complete\n"
                        "data: {\"analysis_id\": \"uuid\", \"result\": \"...\", ...}\n\n"
                    )
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Validation error - invalid query parameters"
        }
    },
    summary="Execute Gmail analysis with SSE streaming",
    description=(
        "Executes the Gmail Read Flow with real-time progress updates via "
        "Server-Sent Events (SSE). Emits progress events during execution "
        "and a complete event with the final result."
    )
)
async def analyze_emails_stream(
    sender_emails: str = Query(
        ...,
        description="Comma-separated list of sender email addresses",
        example="user@example.com,another@example.com"
    ),
    language: str = Query(
        default="en",
        description="ISO 639-1 language code for output",
        pattern="^[a-z]{2}$",
        example="en"
    ),
    days: int = Query(
        default=7,
        description="Number of days to look back",
        ge=1,
        le=365,
        example=7
    )
) -> StreamingResponse:
    """Execute Gmail analysis flow with SSE progress updates.
    
    Streams progress events during flow execution using Server-Sent Events.
    Clients can listen for 'progress', 'complete', and 'error' events.
    
    Args:
        sender_emails: Comma-separated list of email addresses
        language: ISO 639-1 language code (default: "en")
        days: Number of days to look back (default: 7, range: 1-365)
    
    Returns:
        StreamingResponse with text/event-stream content type
    
    Event Types:
        - progress: Status updates during execution
        - complete: Final result with full analysis data
        - error: Error information if execution fails
    
    Raises:
        HTTPException 400: If query parameter validation fails
    """
    try:
        # Parse comma-separated emails
        emails_list = [email.strip() for email in sender_emails.split(",") if email.strip()]
        
        if not emails_list:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ValidationError",
                    "message": "At least one sender email is required",
                    "details": None
                }
            )
        
        logger.info(
            f"Received streaming analysis request for {len(emails_list)} sender(s), "
            f"language={language}, days={days}"
        )
        
        # Create request object (will validate emails and language)
        request = GmailAnalysisRequest(
            sender_emails=emails_list,
            language=language,
            days=days
        )
        
        # Return streaming response
        return StreamingResponse(
            flow_service.execute_flow_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering in nginx
            }
        )
        
    except ValueError as e:
        # Validation errors from Pydantic model
        logger.warning(f"Validation error in streaming request: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "details": None
            }
        )
