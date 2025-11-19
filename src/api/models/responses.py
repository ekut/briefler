"""Response models for the Briefler API."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GmailAnalysisResponse(BaseModel):
    """Response model for Gmail analysis.
    
    Attributes:
        analysis_id: Unique identifier for this analysis (UUID)
        result: Analysis result text in markdown format (for backward compatibility)
        structured_result: Structured analysis result with typed fields (optional)
        token_usage: Aggregated token usage statistics across all tasks (optional)
        parameters: Input parameters used for the analysis
        timestamp: When the analysis was completed (UTC)
        execution_time_seconds: Time taken to complete the analysis
    """
    
    analysis_id: str = Field(
        ...,
        description="Unique identifier for this analysis"
    )
    result: str = Field(
        ...,
        description="Analysis result text (markdown formatted) - for backward compatibility"
    )
    structured_result: Optional[dict] = Field(
        None,
        description="Structured analysis result with typed fields"
    )
    token_usage: Optional[dict] = Field(
        None,
        description="Aggregated token usage statistics across all tasks"
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
    """Error response model.
    
    Attributes:
        error: Error type or category
        message: Human-readable error message
        details: Additional error details (optional)
    """
    
    error: str = Field(
        ...,
        description="Error type"
    )
    message: str = Field(
        ...,
        description="Error message"
    )
    details: Optional[dict] = Field(
        None,
        description="Additional error details"
    )


class HistoryItem(BaseModel):
    """History list item model.
    
    Attributes:
        analysis_id: Unique identifier for the analysis
        timestamp: When the analysis was completed
        sender_count: Number of sender emails analyzed
        language: Language code used for the analysis
        days: Number of days looked back
        preview: First 200 characters of the result
    """
    
    analysis_id: str = Field(
        ...,
        description="Unique identifier for the analysis"
    )
    timestamp: datetime = Field(
        ...,
        description="When the analysis was completed"
    )
    sender_count: int = Field(
        ...,
        description="Number of sender emails analyzed"
    )
    language: str = Field(
        ...,
        description="Language code used for the analysis"
    )
    days: int = Field(
        ...,
        description="Number of days looked back"
    )
    preview: str = Field(
        ...,
        description="First 200 chars of result"
    )


class HistoryListResponse(BaseModel):
    """History list response with pagination.
    
    Attributes:
        items: List of history items
        total: Total number of analyses in history
        limit: Maximum number of items per page
        offset: Number of items skipped
    """
    
    items: List[HistoryItem] = Field(
        ...,
        description="List of history items"
    )
    total: int = Field(
        ...,
        description="Total number of analyses in history"
    )
    limit: int = Field(
        ...,
        description="Maximum number of items per page"
    )
    offset: int = Field(
        ...,
        description="Number of items skipped"
    )
