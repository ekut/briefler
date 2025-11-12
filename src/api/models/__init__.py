"""Pydantic data models for requests and responses."""

from .requests import GmailAnalysisRequest
from .responses import (
    GmailAnalysisResponse,
    ErrorResponse,
    HistoryItem,
    HistoryListResponse
)

__all__ = [
    "GmailAnalysisRequest",
    "GmailAnalysisResponse",
    "ErrorResponse",
    "HistoryItem",
    "HistoryListResponse",
]
