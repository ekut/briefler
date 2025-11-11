"""Gmail Read Flow implementation with enhanced input parameters."""

from pydantic import BaseModel, Field, field_validator
from typing import List
import re
from crewai.flow.flow import Flow, listen, start
from briefler.crews.gmail_reader_crew import GmailReaderCrew


class FlowState(BaseModel):
    """State model for Gmail Reader Flow with enhanced parameters.
    
    This model defines the state passed between flow steps, including
    sender emails, language preferences, and time-based filtering.
    """
    
    sender_emails: List[str] = Field(
        default=[],
        description="List of sender email addresses to retrieve messages from"
    )
    language: str = Field(
        default="en",
        description="ISO 639-1 language code for summary output (e.g., 'en', 'ru', 'es')"
    )
    days: int = Field(
        default=7,
        description="Number of days in the past to retrieve unread messages from"
    )
    result: str = Field(
        default="",
        description="Crew execution result"
    )
    
    @field_validator('sender_emails')
    @classmethod
    def validate_sender_emails(cls, v: List[str]) -> List[str]:
        """Validate sender_emails list is not empty and contains valid email formats.
        
        Args:
            v: List of sender email addresses
            
        Returns:
            List of validated and stripped email addresses
            
        Raises:
            ValueError: If list is empty or any email has invalid format
        """
        # Allow empty list during initialization (will be populated by initialize method)
        if not v or len(v) == 0:
            return v
        
        # Email validation regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Validate each email format and strip whitespace
        validated_emails = []
        for email in v:
            stripped_email = email.strip()
            if not re.match(email_pattern, stripped_email):
                raise ValueError(f"Invalid email format: '{email}'")
            validated_emails.append(stripped_email)
        
        return validated_emails
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language is a valid ISO 639-1 code.
        
        Args:
            v: Language code string
            
        Returns:
            Lowercase validated language code
            
        Raises:
            ValueError: If language code is not a valid ISO 639-1 code
        """
        # Define set of valid ISO 639-1 language codes
        valid_codes = {
            'en', 'ru', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko',
            'ar', 'hi', 'nl', 'pl', 'tr', 'sv', 'no', 'da', 'fi', 'cs',
            'el', 'he', 'th', 'vi', 'id', 'ms', 'uk', 'ro', 'hu', 'sk'
        }
        
        # Convert to lowercase for validation
        language_lower = v.lower()
        
        # Validate language code is in valid set
        if language_lower not in valid_codes:
            raise ValueError(
                f"Invalid language code: '{v}'. Must be a valid ISO 639-1 code "
                f"(e.g., 'en', 'ru', 'es')"
            )
        
        return language_lower
    
    @field_validator('days')
    @classmethod
    def validate_days(cls, v: int) -> int:
        """Validate days is a positive integer greater than zero.
        
        Args:
            v: Number of days
            
        Returns:
            Validated days value
            
        Raises:
            ValueError: If days is not a positive integer greater than zero
        """
        # Validate days is an integer and greater than zero
        if not isinstance(v, int) or v <= 0:
            raise ValueError("days must be a positive integer greater than zero")
        
        return v


class GmailReadFlow(Flow[FlowState]):
    """Flow for orchestrating Gmail Reader Crew execution.
    
    This flow manages the execution of the Gmail Reader Crew with enhanced
    input parameters including multiple sender emails, language preferences,
    and time-based filtering.
    """
    
    @start()
    def initialize(self, crewai_trigger_payload: dict = None):
        """Entry point of the flow with parameter handling.
        
        This method initializes the flow state with parameters from the trigger
        payload. It handles backward compatibility for single sender_email
        parameter and applies default values when parameters are not provided.
        
        Args:
            crewai_trigger_payload: Optional dictionary containing input parameters
                - sender_emails: List of sender email addresses
                - sender_email: Single sender email (backward compatibility)
                - language: ISO 639-1 language code (default: "en")
                - days: Number of days to retrieve messages (default: 7)
        """
        print("Initializing Gmail Read Flow...")
        
        if crewai_trigger_payload:
            print(f"Using trigger payload: {crewai_trigger_payload}")
            
            # Handle backward compatibility for single sender_email parameter
            # Convert single sender_email to sender_emails list if needed
            if 'sender_email' in crewai_trigger_payload and 'sender_emails' not in crewai_trigger_payload:
                crewai_trigger_payload['sender_emails'] = [crewai_trigger_payload['sender_email']]
            
            # Extract parameters from trigger payload with default values
            sender_emails = crewai_trigger_payload.get('sender_emails', [])
            language = crewai_trigger_payload.get('language', 'en')
            days = crewai_trigger_payload.get('days', 7)
            
            # Update self.state with extracted values
            self.state.sender_emails = sender_emails
            self.state.language = language
            self.state.days = days
    
    @listen(initialize)
    def analyze_emails(self):
        """Execute Gmail Reader Crew with enhanced parameters.
        
        This method is triggered after the initialize() method completes.
        It prepares the crew inputs with sender emails, language, and days
        parameters, then executes the GmailReaderCrew and stores the result.
        """
        # Print analysis start message with sender count, language, and days
        print(f"Analyzing emails from {len(self.state.sender_emails)} sender(s)...")
        print(f"Language: {self.state.language}, Days: {self.state.days}")
        
        # Prepare crew_inputs dictionary with sender_emails, language, and days
        crew_inputs = {
            'sender_emails': self.state.sender_emails,
            'language': self.state.language,
            'days': self.state.days
        }
        
        # Instantiate GmailReaderCrew and call crew().kickoff(inputs=crew_inputs)
        result = GmailReaderCrew().crew().kickoff(inputs=crew_inputs)
        
        # Store result.raw in self.state.result
        self.state.result = result.raw
