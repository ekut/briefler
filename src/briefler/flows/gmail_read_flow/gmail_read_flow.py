"""Gmail Read Flow implementation with enhanced input parameters."""

from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List, Optional
import re
import logging
from crewai.flow.flow import Flow, listen, start
from briefler.crews.gmail_reader_crew import GmailReaderCrew
from briefler.models.task_outputs import AnalysisTaskOutput, TokenUsage

# Configure logger for this module
logger = logging.getLogger(__name__)


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
    structured_result: Optional[AnalysisTaskOutput] = Field(
        default=None,
        description="Structured analysis result with typed fields"
    )
    total_token_usage: Optional[TokenUsage] = Field(
        default=None,
        description="Aggregated token usage across all tasks"
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
    
    def __init__(self, *args, **kwargs):
        """Initialize flow with validation failure tracking."""
        super().__init__(*args, **kwargs)
        self._validation_failure_count = 0
    
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
        
        # Store result.raw in self.state.result for backward compatibility
        self.state.result = result.raw
        
        # Extract structured result if available
        try:
            # Try to extract result.pydantic first (primary method)
            if hasattr(result, 'pydantic') and result.pydantic:
                self.state.structured_result = result.pydantic
                logger.info("Successfully extracted structured result from result.pydantic")
                print("Successfully extracted structured result from result.pydantic")
            # Fallback to parsing result.json_dict if pydantic not available
            elif hasattr(result, 'json_dict') and result.json_dict:
                self.state.structured_result = AnalysisTaskOutput(**result.json_dict)
                logger.info("Successfully parsed structured result from result.json_dict")
                print("Successfully parsed structured result from result.json_dict")
            else:
                logger.warning("No structured result available (neither pydantic nor json_dict)")
                print("Warning: No structured result available (neither pydantic nor json_dict)")
        except ValidationError as e:
            # Handle Pydantic validation errors specifically
            self._validation_failure_count += 1
            
            # Log validation error with field details (sanitized)
            error_details = []
            for error in e.errors():
                field_path = '.'.join(str(loc) for loc in error['loc'])
                error_type = error['type']
                error_msg = error['msg']
                error_details.append(f"{field_path}: {error_type} - {error_msg}")
            
            logger.error(
                f"Pydantic validation error extracting structured result: "
                f"{len(e.errors())} validation error(s) occurred",
                extra={'validation_errors': error_details}
            )
            print(f"Warning: Validation error extracting structured result - {len(e.errors())} field error(s)")
            
            # Check for repeated validation failures
            if self._validation_failure_count >= 3:
                logger.warning(
                    f"Repeated validation failures detected ({self._validation_failure_count} times). "
                    "This may indicate a schema mismatch between task output and expected model."
                )
            
            # Fall back to raw result only
            logger.info("Falling back to raw result only due to validation error")
            print("Falling back to raw result only")
            
            # Ensure flow continues execution - structured_result remains None
        except Exception as e:
            # Handle other unexpected errors
            logger.error(
                f"Unexpected error extracting structured result: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            print(f"Warning: Could not extract structured result: {e}")
            print("Falling back to raw result only")
        
        # Aggregate token usage from crew execution
        self._aggregate_token_usage(result)
    
    def _aggregate_token_usage(self, crew_result):
        """Aggregate token usage from crew execution.
        
        CrewAI provides usage_metrics at the crew level after kickoff,
        which aggregates token usage across all tasks automatically.
        
        Args:
            crew_result: The result object returned from crew.kickoff()
        """
        try:
            usage_metrics = None
            
            # Try to extract token usage from crew_result.token_usage first
            if hasattr(crew_result, 'token_usage') and crew_result.token_usage:
                usage_metrics = crew_result.token_usage
                print("Extracted token usage from crew_result.token_usage")
            # Try to access usage_metrics from the crew instance
            elif hasattr(crew_result, 'usage_metrics') and crew_result.usage_metrics:
                usage_metrics = crew_result.usage_metrics
                print("Extracted token usage from crew_result.usage_metrics")
            else:
                print("Warning: No usage_metrics available from crew result")
                return
            
            # Extract token values from usage_metrics object
            # UsageMetrics can be either a dict or an object with attributes
            if isinstance(usage_metrics, dict):
                # Handle dictionary format (for backward compatibility)
                total_tokens = usage_metrics.get('total_tokens', 0)
                prompt_tokens = usage_metrics.get('prompt_tokens', 0)
                completion_tokens = usage_metrics.get('completion_tokens', 0)
            else:
                # Handle object format (CrewAI UsageMetrics object)
                total_tokens = getattr(usage_metrics, 'total_tokens', 0)
                prompt_tokens = getattr(usage_metrics, 'prompt_tokens', 0)
                completion_tokens = getattr(usage_metrics, 'completion_tokens', 0)
            
            # Create TokenUsage instance from extracted values
            self.state.total_token_usage = TokenUsage(
                total_tokens=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            
            # Log token usage with prompt and completion breakdown
            print(f"Total token usage: {self.state.total_token_usage.total_tokens} tokens "
                  f"(prompt: {self.state.total_token_usage.prompt_tokens}, "
                  f"completion: {self.state.total_token_usage.completion_tokens})")
        except Exception as e:
            print(f"Warning: Could not extract token usage: {e}")
