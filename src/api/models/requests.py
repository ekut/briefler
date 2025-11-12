"""Request models for the Briefler API."""

from pydantic import BaseModel, Field, field_validator
from typing import List
import re


class GmailAnalysisRequest(BaseModel):
    """Request model for Gmail analysis.
    
    Attributes:
        sender_emails: List of sender email addresses to analyze
        language: ISO 639-1 language code for output (default: "en")
        days: Number of days to look back (default: 7, range: 1-365)
    """
    
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
        """Validate email format for each sender.
        
        Args:
            v: List of email addresses to validate
            
        Returns:
            List of validated and stripped email addresses
            
        Raises:
            ValueError: If any email has invalid format
        """
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
        """Validate ISO 639-1 language code.
        
        Args:
            v: Language code to validate
            
        Returns:
            Lowercase validated language code
            
        Raises:
            ValueError: If language code is not valid ISO 639-1
        """
        # Common ISO 639-1 language codes
        valid_codes = {
            'en', 'ru', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko',
            'ar', 'hi', 'nl', 'pl', 'tr', 'sv', 'no', 'da', 'fi', 'cs',
            'sk', 'hu', 'ro', 'bg', 'hr', 'sr', 'uk', 'el', 'he', 'th',
            'vi', 'id', 'ms', 'tl', 'sw', 'af', 'sq', 'am', 'hy', 'az',
            'eu', 'be', 'bn', 'bs', 'ca', 'ceb', 'ny', 'co', 'cy', 'eo',
            'et', 'fa', 'fy', 'gd', 'gl', 'ka', 'gu', 'ht', 'ha', 'haw',
            'iw', 'hmn', 'is', 'ig', 'ga', 'jw', 'kn', 'kk', 'km', 'rw',
            'ku', 'ky', 'lo', 'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ml',
            'mt', 'mi', 'mr', 'mn', 'my', 'ne', 'ps', 'pa', 'sm', 'sn',
            'sd', 'si', 'so', 'st', 'su', 'ta', 'te', 'tg', 'tt', 'ur',
            'ug', 'uz', 'xh', 'yi', 'yo', 'zu'
        }
        if v.lower() not in valid_codes:
            raise ValueError(f"Invalid language code: '{v}'. Must be a valid ISO 639-1 code.")
        return v.lower()
