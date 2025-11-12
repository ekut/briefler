"""History API routes.

This module provides HTTP endpoints for retrieving analysis history,
including paginated list views and individual analysis retrieval.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Annotated
import logging

from api.models.responses import (
    GmailAnalysisResponse,
    HistoryListResponse
)
from api.services.history_service import HistoryService


logger = logging.getLogger(__name__)

# Create router for history endpoints
router = APIRouter()

# Initialize history service
history_service = HistoryService()


@router.get("", response_model=HistoryListResponse)
async def get_history(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0
) -> HistoryListResponse:
    """Get paginated list of past analyses.
    
    Retrieves analysis history sorted by timestamp (newest first).
    Supports pagination via limit and offset parameters.
    
    Args:
        limit: Maximum number of items to return (1-100, default: 20)
        offset: Number of items to skip (default: 0)
        
    Returns:
        HistoryListResponse containing paginated history items
        
    Raises:
        HTTPException: 500 if history retrieval fails
        
    Example:
        GET /api/history?limit=10&offset=0
    """
    try:
        logger.info(f"Retrieving history with limit={limit}, offset={offset}")
        result = await history_service.get_history(limit=limit, offset=offset)
        return result
        
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=GmailAnalysisResponse)
async def get_analysis_by_id(analysis_id: str) -> GmailAnalysisResponse:
    """Get specific analysis by ID.
    
    Retrieves a complete analysis result including the full text,
    parameters, and metadata.
    
    Args:
        analysis_id: Unique identifier (UUID) of the analysis
        
    Returns:
        GmailAnalysisResponse with complete analysis data
        
    Raises:
        HTTPException: 404 if analysis not found
        HTTPException: 500 if retrieval fails
        
    Example:
        GET /api/history/550e8400-e29b-41d4-a716-446655440000
    """
    try:
        logger.info(f"Retrieving analysis {analysis_id}")
        result = await history_service.get_by_id(analysis_id)
        
        if result is None:
            logger.warning(f"Analysis {analysis_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID '{analysis_id}' not found"
            )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
        
    except Exception as e:
        logger.error(
            f"Failed to retrieve analysis {analysis_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analysis: {str(e)}"
        )
