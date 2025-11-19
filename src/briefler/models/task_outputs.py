"""Pydantic models for structured task outputs in CrewAI workflows.

This module defines all output models for the Gmail Reader Crew tasks,
enabling type-safe, validated, and programmatically accessible data structures.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage statistics for LLM calls.
    
    This model matches the structure returned by CrewAI's usage_metrics
    and webhook payloads for consistency with the framework.
    """
    
    total_tokens: int = Field(
        default=0,
        ge=0,
        description="Total tokens used (prompt + completion)"
    )
    prompt_tokens: int = Field(
        default=0,
        ge=0,
        description="Number of tokens in the prompt"
    )
    completion_tokens: int = Field(
        default=0,
        ge=0,
        description="Number of tokens in the completion"
    )


class CleanedEmail(BaseModel):
    """Represents a single cleaned email with boilerplate removed."""
    
    subject: str = Field(
        ...,
        min_length=1,
        description="Email subject line"
    )
    sender: str = Field(
        ...,
        min_length=1,
        description="Sender email address"
    )
    timestamp: datetime = Field(
        ...,
        description="Email timestamp in ISO 8601 format"
    )
    body: str = Field(
        ...,
        description="Cleaned email body with boilerplate removed"
    )
    image_urls: List[str] = Field(
        default_factory=list,
        description="List of image URLs found in the email"
    )


class CleanupTaskOutput(BaseModel):
    """Output from the cleanup task that removes boilerplate from emails."""
    
    emails: List[CleanedEmail] = Field(
        ...,
        description="List of cleaned emails"
    )
    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of emails processed"
    )
    token_usage: Optional[TokenUsage] = Field(
        None,
        description="Token usage statistics for this task"
    )


class ExtractedImageText(BaseModel):
    """Represents text extracted from a single image."""
    
    image_url: str = Field(
        ...,
        min_length=1,
        description="URL of the image"
    )
    extracted_text: str = Field(
        ...,
        description="Text extracted from the image, or 'No text found' if empty"
    )
    has_text: bool = Field(
        ...,
        description="Whether any text was found in the image"
    )


class VisionTaskOutput(BaseModel):
    """Output from the vision task that extracts text from images."""
    
    extracted_texts: List[ExtractedImageText] = Field(
        default_factory=list,
        description="List of extracted texts from images"
    )
    total_images_processed: int = Field(
        ...,
        ge=0,
        description="Total number of images processed"
    )
    images_with_text: int = Field(
        ...,
        ge=0,
        description="Number of images that contained text"
    )
    token_usage: Optional[TokenUsage] = Field(
        None,
        description="Token usage statistics for this task"
    )


class EmailSummary(BaseModel):
    """Summary of a single email with key points and action items."""
    
    subject: str = Field(
        ...,
        min_length=1,
        description="Email subject"
    )
    sender: str = Field(
        ...,
        min_length=1,
        description="Sender email address"
    )
    timestamp: datetime = Field(
        ...,
        description="Email timestamp in ISO 8601 format"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points from the email"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="Action items identified in this email"
    )
    has_deadline: bool = Field(
        default=False,
        description="Whether the email contains time-sensitive information"
    )


class AnalysisTaskOutput(BaseModel):
    """Output from the analysis task that generates the final email summary."""
    
    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of emails analyzed"
    )
    email_summaries: List[EmailSummary] = Field(
        ...,
        description="List of email summaries"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="All action items across all emails"
    )
    priority_assessment: str = Field(
        ...,
        min_length=1,
        description="Overall priority assessment (e.g., High, Medium, Low)"
    )
    summary_text: str = Field(
        ...,
        description="Full markdown-formatted summary (for backward compatibility)"
    )
    token_usage: Optional[TokenUsage] = Field(
        None,
        description="Token usage statistics for this task"
    )
