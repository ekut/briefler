# Design Document

## Overview

This design extends the Gmail Reader Crew to support enhanced input parameters including multiple sender emails, configurable output language, and time-based filtering. The implementation modifies the FlowState model, updates the GmailReaderTool to support date filtering, and enhances the crew configuration to handle language-specific summaries.

The design maintains backward compatibility with existing implementations while providing flexible configuration options through default values. All changes follow the existing CrewAI Flow architecture pattern and maintain the current error handling and logging conventions.

## Architecture

### Component Overview

The enhancement touches four main components:

1. **GmailReadFlow** (`src/briefler/flows/gmail_read_flow/`)
   - New dedicated flow class for Gmail reading functionality
   - Contains FlowState model with enhanced input parameters
   - Maintains state across flow steps
   - Provides validation for input parameters

2. **Main Entry Point** (`src/briefler/main.py`)
   - Imports and delegates to GmailReadFlow
   - Maintains backward compatibility with existing entry points

3. **GmailReaderTool** (`src/briefler/tools/gmail_reader_tool.py`)
   - Updated input schema to support multiple senders and date filtering
   - Enhanced query construction for Gmail API
   - Date calculation logic for time-based filtering

4. **Crew Configuration** (`src/briefler/crews/gmail_reader_crew/config/`)
   - Updated agent and task YAML files to support language parameter
   - Modified prompts to include language instructions

### Data Flow

```
User Input (kickoff/trigger)
    ↓
main.py (entry point)
    ↓
GmailReadFlow (orchestration)
    ↓
FlowState (validation & defaults)
    ↓
GmailReaderCrew (language-aware prompts)
    ↓
GmailReaderTool (multi-sender + date filtering)
    ↓
Gmail API (filtered queries)
    ↓
AI Agent (language-specific summary)
    ↓
Output (formatted in specified language)
```

### Directory Structure

```
src/briefler/
├── main.py                          # Entry point (imports GmailReadFlow)
├── flows/
│   └── gmail_read_flow/
│       ├── __init__.py             # Exports GmailReadFlow
│       └── gmail_read_flow.py      # Flow implementation with FlowState
├── crews/
│   └── gmail_reader_crew/
│       ├── config/
│       │   ├── agents.yaml         # Updated with language parameter
│       │   └── tasks.yaml          # Updated with language parameter
│       └── gmail_reader_crew.py
└── tools/
    └── custom_tool.py
```

## Components and Interfaces

### 1. GmailReadFlow Module

**Location:** `src/briefler/flows/gmail_read_flow/gmail_read_flow.py`

**FlowState Model:**
```python
from pydantic import BaseModel, Field, field_validator
from typing import List

class FlowState(BaseModel):
    """State model for Gmail Reader Flow with enhanced parameters."""
    
    sender_emails: List[str] = Field(
        ...,
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
    def validate_sender_emails(cls, v):
        """Validate sender_emails list is not empty and contains valid emails."""
        if not v or len(v) == 0:
            raise ValueError("sender_emails must contain at least one email address")
        
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in v:
            if not re.match(email_pattern, email.strip()):
                raise ValueError(f"Invalid email format: '{email}'")
        
        return [email.strip() for email in v]
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language is a valid ISO 639-1 code."""
        # Common ISO 639-1 codes - can be extended
        valid_codes = {
            'en', 'ru', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko',
            'ar', 'hi', 'nl', 'pl', 'tr', 'sv', 'no', 'da', 'fi', 'cs',
            'el', 'he', 'th', 'vi', 'id', 'ms', 'uk', 'ro', 'hu', 'sk'
        }
        
        if v.lower() not in valid_codes:
            raise ValueError(
                f"Invalid language code: '{v}'. Must be a valid ISO 639-1 code "
                f"(e.g., 'en', 'ru', 'es')"
            )
        
        return v.lower()
    
    @field_validator('days')
    @classmethod
    def validate_days(cls, v):
        """Validate days is a positive integer."""
        if not isinstance(v, int) or v <= 0:
            raise ValueError("days must be a positive integer greater than zero")
        
        return v
```

**GmailReadFlow Class:**
```python
from crewai.flow import Flow, listen, start
from briefler.crews.gmail_reader_crew.gmail_reader_crew import GmailReaderCrew

class GmailReadFlow(Flow[FlowState]):
    """Flow for orchestrating Gmail Reader Crew execution."""

    @start()
    def initialize(self, crewai_trigger_payload: dict = None):
        """Entry point of the flow with parameter handling."""
        print("Initializing Gmail Read Flow...")
        
        if crewai_trigger_payload:
            print(f"Using trigger payload: {crewai_trigger_payload}")
            
            # Handle backward compatibility for single sender_email
            if 'sender_email' in crewai_trigger_payload and 'sender_emails' not in crewai_trigger_payload:
                crewai_trigger_payload['sender_emails'] = [crewai_trigger_payload['sender_email']]
            
            # Update state with trigger payload
            self.state.sender_emails = crewai_trigger_payload.get('sender_emails', [])
            self.state.language = crewai_trigger_payload.get('language', 'en')
            self.state.days = crewai_trigger_payload.get('days', 7)

    @listen(initialize)
    def analyze_emails(self):
        """Execute Gmail Reader Crew with enhanced parameters."""
        print(f"Analyzing emails from {len(self.state.sender_emails)} sender(s)...")
        print(f"Language: {self.state.language}, Days: {self.state.days}")
        
        # Prepare inputs for crew
        crew_inputs = {
            'sender_emails': self.state.sender_emails,
            'language': self.state.language,
            'days': self.state.days
        }
        
        # Execute crew
        result = GmailReaderCrew().crew().kickoff(inputs=crew_inputs)
        self.state.result = result.raw
```

**Module __init__.py:**
```python
# src/briefler/flows/gmail_read_flow/__init__.py
from .gmail_read_flow import GmailReadFlow, FlowState

__all__ = ['GmailReadFlow', 'FlowState']
```

**Backward Compatibility:**
- Support single `sender_email` parameter by converting to list
- Handle in `initialize()` method of GmailReadFlow

### 2. GmailReaderTool Updates

**Location:** `src/briefler/tools/gmail_reader_tool.py`

#### 2.1 Updated Input Schema

```python
class GmailReaderToolInput(BaseModel):
    """Input schema for GmailReaderTool with enhanced parameters."""
    
    sender_emails: List[str] = Field(
        ...,
        description="List of sender email addresses to filter unread messages from"
    )
    days: int = Field(
        default=7,
        description="Number of days in the past to retrieve unread messages from"
    )
```

#### 2.2 Date Filtering Logic

**New Method:**
```python
def _calculate_date_threshold(self, days: int) -> str:
    """Calculate date threshold for Gmail API query.
    
    Args:
        days: Number of days in the past from current date
    
    Returns:
        Date string in Gmail API format (YYYY/MM/DD)
    """
    from datetime import datetime, timedelta
    
    threshold_date = datetime.now() - timedelta(days=days)
    return threshold_date.strftime('%Y/%m/%d')
```

#### 2.3 Enhanced Query Construction

**Updated Method:** `_get_unread_messages()`

```python
def _get_unread_messages(self, sender_emails: List[str], days: int) -> list:
    """Retrieve unread messages from multiple senders within date range.
    
    Args:
        sender_emails: List of sender email addresses
        days: Number of days in the past to retrieve messages from
    
    Returns:
        List of full message dictionaries
    """
    # Calculate date threshold
    date_threshold = self._calculate_date_threshold(days)
    
    # Construct query with multiple senders and date filter
    # Format: "is:unread (from:email1 OR from:email2) after:YYYY/MM/DD"
    sender_query = " OR ".join([f"from:{email}" for email in sender_emails])
    query = f"is:unread ({sender_query}) after:{date_threshold}"
    
    # Rest of implementation remains similar...
```

#### 2.4 Updated _run() Method

```python
def _run(self, sender_emails: List[str], days: int = 7) -> str:
    """Execute the tool to retrieve unread messages.
    
    Args:
        sender_emails: List of sender email addresses
        days: Number of days in the past (default: 7)
    
    Returns:
        Formatted string containing unread messages
    """
    # Validation handled by Pydantic schema
    # Call updated _get_unread_messages with new parameters
    raw_messages = self._get_unread_messages(sender_emails, days)
    
    # Process and format messages (existing logic)
    # Update _format_output to handle multiple senders
```

#### 2.5 Updated Output Formatting

**Updated Method:** `_format_output()`

```python
def _format_output(self, messages: list, sender_emails: List[str], days: int) -> str:
    """Format message list into readable string output.
    
    Args:
        messages: List of message dictionaries
        sender_emails: List of sender email addresses
        days: Number of days filtered
    
    Returns:
        Formatted string with header showing all senders and date range
    """
    if not messages:
        senders_str = ", ".join(sender_emails)
        return f"No unread messages found from {senders_str} in the last {days} days"
    
    # Format header with multiple senders and date range
    senders_str = ", ".join(sender_emails)
    message_count = len(messages)
    
    output_lines = [
        f"Found {message_count} unread message{'s' if message_count != 1 else ''} "
        f"from {senders_str} in the last {days} days:",
        ""
    ]
    
    # Rest of formatting logic remains similar...
```

### 3. Crew Configuration Updates

**Location:** `src/briefler/crews/gmail_reader_crew/config/`

#### 3.1 Updated agents.yaml

```yaml
email_analyst:
  role: >
    Email Analyst
  goal: >
    Read and analyze unread emails from specified senders and provide 
    comprehensive summaries in {language} language with key insights
  backstory: >
    You are an expert email analyst who helps users stay on top of 
    important communications. You can read unread emails from multiple 
    senders and provide summaries and insights in the user's preferred 
    language. You have years of experience in information extraction, 
    summarization, and multilingual communication. You always respond 
    in the language specified by the user ({language}).
```

#### 3.2 Updated tasks.yaml

```yaml
analyze_emails:
  description: >
    Read all unread emails from the specified senders received in the last 
    {days} days and provide a comprehensive summary in {language} language.
    Include the number of messages, their subjects, timestamps, and key points 
    from the content. Organize the information in a clear and readable format.
    
    IMPORTANT: You MUST write your entire summary in {language} language. 
    All text, headings, and descriptions must be in {language}.
  expected_output: >
    A structured summary of unread emails in {language} language including:
    - Total message count
    - List of subjects with timestamps
    - Key information and action items from each message
    - Overall priority assessment
    
    The entire output must be written in {language} language.
  agent: email_analyst
```

#### 3.3 Updated GmailReaderCrew

**Location:** `src/briefler/crews/gmail_reader_crew/gmail_reader_crew.py`

```python
@CrewBase
class GmailReaderCrew:
    """Gmail Reader Crew for analyzing unread emails"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def email_analyst(self) -> Agent:
        gmail_tool = GmailReaderTool()
        return Agent(
            config=self.agents_config["email_analyst"],
            tools=[gmail_tool],
        )

    @task
    def analyze_emails(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_emails"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Gmail Reader Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

### 4. Main Entry Point Updates

**Location:** `src/briefler/main.py`

#### 4.1 Updated main.py

```python
#!/usr/bin/env python
"""
Main entry point for Briefler Project.

This module provides standard entry points for running the Gmail Read Flow.
"""

from briefler.flows.gmail_read_flow import GmailReadFlow


def kickoff():
    """
    Standard entry point for running the flow.
    Usage: crewai run
    """
    flow = GmailReadFlow()
    flow.kickoff()


def plot():
    """
    Generate a visual plot of the flow structure.
    Usage: crewai plot
    """
    flow = GmailReadFlow()
    flow.plot()


def run_with_trigger():
    """
    Run the flow with external trigger payload.
    
    Usage:
        python src/briefler/main.py '{"sender_emails": ["user@example.com"], "language": "en", "days": 7}'
    """
    import json
    import sys

    # Get trigger payload from command line argument
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    # Create flow and kickoff with trigger payload
    flow = GmailReadFlow()

    try:
        result = flow.kickoff({"crewai_trigger_payload": trigger_payload})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}")


if __name__ == "__main__":
    kickoff()
```

## Data Models

### Input Parameters

```python
{
    "sender_emails": ["user1@example.com", "user2@example.com"],  # Required, List[str]
    "language": "en",                                              # Optional, default: "en"
    "days": 7                                                      # Optional, default: 7
}
```

### Gmail API Query Format

```
is:unread (from:email1@example.com OR from:email2@example.com) after:2025/11/04
```

### Tool Output Format

```
Found 5 unread messages from user1@example.com, user2@example.com in the last 7 days:

---
Message 1:
Subject: Important Update
From: user1@example.com
Date: Mon, 11 Nov 2025 10:30:00 +0000

[Message body content]

Attachments: 2 files
- document.pdf (application/pdf, 1024 bytes)
- image.png (image/png, 2048 bytes)

---
[Additional messages...]
```

## Error Handling

### Validation Errors

1. **Empty sender_emails list**
   - Error: `ValueError: sender_emails must contain at least one email address`
   - Raised by: FlowState validator

2. **Invalid email format**
   - Error: `ValueError: Invalid email format: 'invalid-email'`
   - Raised by: FlowState validator

3. **Invalid language code**
   - Error: `ValueError: Invalid language code: 'xx'. Must be a valid ISO 639-1 code`
   - Raised by: FlowState validator

4. **Invalid days parameter**
   - Error: `ValueError: days must be a positive integer greater than zero`
   - Raised by: FlowState validator

### Runtime Errors

All existing error handling from GmailReaderTool is preserved:
- Authentication errors (401)
- Rate limiting (429) with exponential backoff
- Server errors (5xx) with retry logic
- Missing credentials file
- Token refresh failures

### Logging

Enhanced logging to include new parameters:
```python
logger.info(f"Querying Gmail API for unread messages from {len(sender_emails)} sender(s) in the last {days} days")
logger.debug(f"Gmail API query: {query}")
logger.info(f"Language setting: {language}")
```

## Testing Strategy

### Unit Tests

1. **FlowState Validation Tests**
   - Test valid input combinations
   - Test empty sender_emails list
   - Test invalid email formats
   - Test invalid language codes
   - Test invalid days values
   - Test default value application

2. **Date Calculation Tests**
   - Test `_calculate_date_threshold()` with various day values
   - Verify correct date format (YYYY/MM/DD)
   - Test edge cases (1 day, 365 days)

3. **Query Construction Tests**
   - Test single sender query
   - Test multiple sender query (2, 5, 10 senders)
   - Test date filter integration
   - Verify correct OR operator usage

4. **Backward Compatibility Tests**
   - Test single `sender_email` parameter conversion
   - Verify default values are applied
   - Test existing example scripts continue to work

### Integration Tests

1. **Gmail API Integration**
   - Test multi-sender message retrieval
   - Test date filtering accuracy
   - Test with no messages in date range
   - Test with messages from only some senders

2. **Crew Execution Tests**
   - Test language parameter propagation to agents
   - Verify summaries are generated in specified language
   - Test with different language codes (en, ru, es)

3. **Flow Execution Tests**
   - Test complete flow with trigger payload
   - Test with various parameter combinations
   - Test error handling at flow level

### Example Test Cases

```python
# Test 1: Multiple senders with default parameters
{
    "sender_emails": ["user1@example.com", "user2@example.com"]
}

# Test 2: Single sender with custom language and days
{
    "sender_emails": ["user@example.com"],
    "language": "ru",
    "days": 14
}

# Test 3: Backward compatibility
{
    "sender_email": "user@example.com"  # Should convert to sender_emails list
}

# Test 4: Maximum parameters
{
    "sender_emails": ["user1@example.com", "user2@example.com", "user3@example.com"],
    "language": "es",
    "days": 30
}
```

## Migration and Backward Compatibility

### Existing Code Support

The design maintains full backward compatibility:

1. **Single sender_email parameter**
   - Automatically converted to `sender_emails` list in `initialize()` method
   - No changes required to existing code

2. **Default values**
   - `language` defaults to "en" (existing behavior)
   - `days` defaults to 7 (new feature, reasonable default)

3. **Output format**
   - Maintains same structure
   - Enhanced header to show multiple senders and date range

### Migration Path

For users wanting to adopt new features:

**Before:**
```python
flow.kickoff({"crewai_trigger_payload": {
    "sender_email": "user@example.com"
}})
```

**After:**
```python
flow.kickoff({"crewai_trigger_payload": {
    "sender_emails": ["user1@example.com", "user2@example.com"],
    "language": "ru",
    "days": 14
}})
```

### Example Updates

Update example files to demonstrate new features:

**examples/gmail_crew_example.py:**
```python
# Example with enhanced parameters
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": [
            "notifications@github.com",
            "noreply@medium.com"
        ],
        "language": "en",
        "days": 7
    }
})
```

## Performance Considerations

### Gmail API Efficiency

1. **Single Query for Multiple Senders**
   - Uses OR operator to combine senders in one query
   - Reduces API calls compared to separate queries per sender
   - Maintains pagination support for large result sets

2. **Date Filtering**
   - Reduces message volume by filtering at API level
   - Improves response time for large mailboxes
   - Reduces processing overhead

### Rate Limiting

- Existing retry logic with exponential backoff is preserved
- No additional API calls introduced
- Date filtering may reduce likelihood of hitting rate limits

### Memory Usage

- Message processing remains sequential
- No significant memory overhead from multiple senders
- Existing pagination handles large result sets

## Security Considerations

### Input Validation

- Email format validation prevents injection attacks
- Language code whitelist prevents arbitrary input
- Days parameter type checking prevents overflow

### Credential Handling

- No changes to existing OAuth 2.0 flow
- Token storage and refresh logic unchanged
- Environment variable configuration maintained

### Data Privacy

- No logging of email content
- Sender emails logged only at INFO level
- Existing privacy practices preserved

## Documentation Updates

### README.md

Add section on enhanced parameters:
```markdown
### Enhanced Parameters

The Gmail Reader Crew supports the following input parameters:

- `sender_emails` (required): List of sender email addresses
- `language` (optional, default: "en"): ISO 639-1 language code for summaries
- `days` (optional, default: 7): Number of days in the past to retrieve messages

Example:
```python
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["user1@example.com", "user2@example.com"],
        "language": "ru",
        "days": 14
    }
})
```
```

### .env.example

No changes required - existing environment variables are sufficient.

### Code Comments

Update docstrings in modified methods to reflect new parameters and behavior.
