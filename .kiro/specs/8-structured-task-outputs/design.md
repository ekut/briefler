# Design Document: Structured Task Outputs

## Overview

This design implements structured task outputs for the Briefler email analysis system using CrewAI's `output_pydantic` feature. The implementation introduces Pydantic models for all task outputs, ensuring type-safe, validated, and programmatically accessible data throughout the agent workflow. This approach replaces the current unstructured string outputs with deterministic data structures that can be reliably parsed and consumed by downstream components.

The design maintains full backward compatibility with existing code while adding new structured data access patterns. All three tasks (CleanupTask, VisionTask, and AnalysisTask) will return Pydantic models, and the Flow will be updated to handle structured outputs.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GmailReadFlow                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              FlowState (Pydantic)                     │  │
│  │  - sender_emails, language, days                      │  │
│  │  - result: str (raw, backward compat)                 │  │
│  │  - structured_result: Optional[AnalysisTaskOutput]    │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           GmailReaderCrew.kickoff()                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ CleanupTask  │   │  VisionTask  │   │ AnalysisTask │
│              │   │              │   │              │
│ output_      │   │ output_      │   │ output_      │
│ pydantic:    │   │ pydantic:    │   │ pydantic:    │
│ Cleanup      │   │ Vision       │   │ Analysis     │
│ TaskOutput   │   │ TaskOutput   │   │ TaskOutput   │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  TaskOutput.pydantic  │
                │  TaskOutput.json_dict │
                │  TaskOutput.raw       │
                └───────────────────────┘
```

### Data Flow

1. **Flow Initialization**: GmailReadFlow receives input parameters and initializes FlowState
2. **Crew Execution**: GmailReaderCrew executes tasks sequentially with structured outputs
3. **Task Outputs**: Each task returns a TaskOutput object containing:
   - `.pydantic`: The Pydantic model instance
   - `.json_dict`: Dictionary representation
   - `.raw`: String representation (backward compatibility)
4. **Result Processing**: Flow extracts structured data from final task and stores in FlowState
5. **API Response**: API layer serializes structured data for client consumption

## Components and Interfaces

### 1. Task Output Models Module

**Location**: `src/briefler/models/task_outputs.py`

This new module defines all Pydantic models for task outputs.

#### CleanupTask Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CleanedEmail(BaseModel):
    """Represents a single cleaned email."""
    
    subject: str = Field(
        ...,
        description="Email subject line"
    )
    sender: str = Field(
        ...,
        description="Sender email address"
    )
    timestamp: datetime = Field(
        ...,
        description="Email timestamp"
    )
    body: str = Field(
        ...,
        description="Cleaned email body with boilerplate removed"
    )
    image_urls: List[str] = Field(
        default_factory=list,
        description="List of image URLs found in the email"
    )

class TokenUsage(BaseModel):
    """Token usage statistics for LLM calls.
    
    This model matches the structure returned by CrewAI's usage_metrics
    and webhook payloads for consistency with the framework.
    """
    
    total_tokens: int = Field(
        default=0,
        description="Total tokens used (prompt + completion)"
    )
    prompt_tokens: int = Field(
        default=0,
        description="Number of tokens in the prompt"
    )
    completion_tokens: int = Field(
        default=0,
        description="Number of tokens in the completion"
    )

class CleanupTaskOutput(BaseModel):
    """Output from the cleanup task."""
    
    emails: List[CleanedEmail] = Field(
        ...,
        description="List of cleaned emails"
    )
    total_count: int = Field(
        ...,
        description="Total number of emails processed"
    )
    token_usage: Optional[TokenUsage] = Field(
        None,
        description="Token usage statistics for this task"
    )
```

#### VisionTask Models

```python
class ExtractedImageText(BaseModel):
    """Represents text extracted from a single image."""
    
    image_url: str = Field(
        ...,
        description="URL of the image"
    )
    extracted_text: str = Field(
        ...,
        description="Text extracted from the image, or 'No text found'"
    )
    has_text: bool = Field(
        ...,
        description="Whether any text was found in the image"
    )

class VisionTaskOutput(BaseModel):
    """Output from the vision task."""
    
    extracted_texts: List[ExtractedImageText] = Field(
        default_factory=list,
        description="List of extracted texts from images"
    )
    total_images_processed: int = Field(
        ...,
        description="Total number of images processed"
    )
    images_with_text: int = Field(
        ...,
        description="Number of images that contained text"
    )
    token_usage: Optional[TokenUsage] = Field(
        None,
        description="Token usage statistics for this task"
    )
```

#### AnalysisTask Models

```python
class EmailSummary(BaseModel):
    """Summary of a single email."""
    
    subject: str = Field(
        ...,
        description="Email subject"
    )
    sender: str = Field(
        ...,
        description="Sender email address"
    )
    timestamp: datetime = Field(
        ...,
        description="Email timestamp"
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
    """Output from the analysis task."""
    
    total_count: int = Field(
        ...,
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
        description="Overall priority assessment"
    )
    summary_text: str = Field(
        ...,
        description="Full markdown-formatted summary (for backward compatibility)"
    )
    token_usage: Optional[TokenUsage] = Field(
        None,
        description="Token usage statistics for this task"
    )
```

### 2. Task Configuration Updates

**Location**: `src/briefler/crews/gmail_reader_crew/gmail_reader_crew.py`

Update task methods to include `output_pydantic` parameter:

```python
from briefler.models.task_outputs import (
    CleanupTaskOutput,
    VisionTaskOutput,
    AnalysisTaskOutput
)

@task
def cleanup_email_content(self) -> Task:
    """Task to clean email content by removing boilerplate"""
    return Task(
        config=self.tasks_config["cleanup_email_content"],
        output_pydantic=CleanupTaskOutput
    )

@task
def extract_text_from_images(self) -> Task:
    """Task to extract text from images in emails"""
    return Task(
        config=self.tasks_config["extract_text_from_images"],
        output_pydantic=VisionTaskOutput
    )

@task
def analyze_emails(self) -> Task:
    """Task to analyze cleaned email content and generate summary"""
    return Task(
        config=self.tasks_config["analyze_emails"],
        output_pydantic=AnalysisTaskOutput
    )
```

### 3. Task Description Updates

**Location**: `src/briefler/crews/gmail_reader_crew/config/tasks.yaml`

Update task descriptions to guide agents toward structured output format:

```yaml
cleanup_email_content:
  description: >
    [Existing description...]
    
    STRUCTURED OUTPUT FORMAT:
    You MUST return your response as a JSON object with the following structure:
    {
      "emails": [
        {
          "subject": "Email subject",
          "sender": "sender@example.com",
          "timestamp": "2025-11-19T10:30:00Z",
          "body": "Cleaned email body text",
          "image_urls": ["url1", "url2"]
        }
      ],
      "total_count": 5
    }
  expected_output: >
    A JSON object containing a list of cleaned emails with subject, sender, 
    timestamp, body, and image_urls fields, plus a total_count field.
```

Similar updates for `extract_text_from_images` and `analyze_emails` tasks.

### 4. Flow Updates

**Location**: `src/briefler/flows/gmail_read_flow/gmail_read_flow.py`

Update FlowState and analyze_emails method:

```python
from briefler.models.task_outputs import AnalysisTaskOutput

class FlowState(BaseModel):
    """State model for Gmail Reader Flow."""
    
    sender_emails: List[str] = Field(default=[])
    language: str = Field(default="en")
    days: int = Field(default=7)
    result: str = Field(default="")  # Backward compatibility
    structured_result: Optional[AnalysisTaskOutput] = Field(
        default=None,
        description="Structured analysis result"
    )
    total_token_usage: Optional[TokenUsage] = Field(
        default=None,
        description="Aggregated token usage across all tasks"
    )
    
    # ... existing validators ...

class GmailReadFlow(Flow[FlowState]):
    """Flow for orchestrating Gmail Reader Crew execution."""
    
    @listen(initialize)
    def analyze_emails(self):
        """Execute Gmail Reader Crew with enhanced parameters."""
        print(f"Analyzing emails from {len(self.state.sender_emails)} sender(s)...")
        print(f"Language: {self.state.language}, Days: {self.state.days}")
        
        crew_inputs = {
            'sender_emails': self.state.sender_emails,
            'language': self.state.language,
            'days': self.state.days
        }
        
        result = GmailReaderCrew().crew().kickoff(inputs=crew_inputs)
        
        # Store raw result for backward compatibility
        self.state.result = result.raw
        
        # Store structured result if available
        try:
            if hasattr(result, 'pydantic') and result.pydantic:
                self.state.structured_result = result.pydantic
                print("Successfully extracted structured result")
            elif hasattr(result, 'json_dict') and result.json_dict:
                # Fallback to json_dict if pydantic not available
                self.state.structured_result = AnalysisTaskOutput(**result.json_dict)
                print("Successfully parsed structured result from json_dict")
            
            # Aggregate token usage from crew execution
            self._aggregate_token_usage(result)
        except Exception as e:
            print(f"Warning: Could not extract structured result: {e}")
            print("Falling back to raw result only")
    
    def _aggregate_token_usage(self, crew_result):
        """Aggregate token usage from crew execution.
        
        CrewAI provides usage_metrics at the crew level after kickoff,
        which aggregates token usage across all tasks automatically.
        """
        try:
            # Access crew.usage_metrics which is populated after kickoff
            if hasattr(crew_result, 'token_usage'):
                # If result has token_usage directly
                usage = crew_result.token_usage
            else:
                # Access from the crew instance
                crew = GmailReaderCrew().crew()
                if hasattr(crew, 'usage_metrics'):
                    usage = crew.usage_metrics
                else:
                    print("Warning: No usage_metrics available from crew")
                    return
            
            # Convert to our TokenUsage model
            from briefler.models.task_outputs import TokenUsage
            self.state.total_token_usage = TokenUsage(
                total_tokens=usage.get('total_tokens', 0),
                prompt_tokens=usage.get('prompt_tokens', 0),
                completion_tokens=usage.get('completion_tokens', 0)
            )
            print(f"Total token usage: {self.state.total_token_usage.total_tokens} tokens "
                  f"(prompt: {self.state.total_token_usage.prompt_tokens}, "
                  f"completion: {self.state.total_token_usage.completion_tokens})")
        except Exception as e:
            print(f"Warning: Could not extract token usage: {e}")
```

### 5. API Response Updates

**Location**: `src/api/models/responses.py`

Add structured data to API response:

```python
from briefler.models.task_outputs import AnalysisTaskOutput

class GmailAnalysisResponse(BaseModel):
    """Response model for Gmail analysis."""
    
    analysis_id: str = Field(...)
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
    parameters: dict = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_seconds: float = Field(...)
```

**Location**: `src/api/services/flow_service.py`

Update service to include structured result:

```python
def execute_gmail_analysis(self, request: GmailAnalysisRequest) -> GmailAnalysisResponse:
    """Execute Gmail analysis flow."""
    # ... existing code ...
    
    # Prepare response
    response_data = {
        "analysis_id": analysis_id,
        "result": flow.state.result,
        "parameters": {
            "sender_emails": request.sender_emails,
            "language": request.language,
            "days": request.days
        },
        "timestamp": datetime.utcnow(),
        "execution_time_seconds": execution_time
    }
    
    # Add structured result if available
    if flow.state.structured_result:
        try:
            response_data["structured_result"] = flow.state.structured_result.model_dump()
        except Exception as e:
            logger.warning(f"Could not serialize structured result: {e}")
    
    # Add token usage if available
    if flow.state.total_token_usage:
        try:
            response_data["token_usage"] = flow.state.total_token_usage.model_dump()
        except Exception as e:
            logger.warning(f"Could not serialize token usage: {e}")
    
    return GmailAnalysisResponse(**response_data)
```

## Data Models

### Model Hierarchy

```
BaseModel (Pydantic)
│
├── TokenUsage
│   ├── total_tokens: int
│   ├── prompt_tokens: int
│   └── completion_tokens: int
│
├── CleanedEmail
│   ├── subject: str
│   ├── sender: str
│   ├── timestamp: datetime
│   ├── body: str
│   └── image_urls: List[str]
│
├── CleanupTaskOutput
│   ├── emails: List[CleanedEmail]
│   ├── total_count: int
│   └── token_usage: Optional[TokenUsage]
│
├── ExtractedImageText
│   ├── image_url: str
│   ├── extracted_text: str
│   └── has_text: bool
│
├── VisionTaskOutput
│   ├── extracted_texts: List[ExtractedImageText]
│   ├── total_images_processed: int
│   ├── images_with_text: int
│   └── token_usage: Optional[TokenUsage]
│
├── EmailSummary
│   ├── subject: str
│   ├── sender: str
│   ├── timestamp: datetime
│   ├── key_points: List[str]
│   ├── action_items: List[str]
│   └── has_deadline: bool
│
└── AnalysisTaskOutput
    ├── total_count: int
    ├── email_summaries: List[EmailSummary]
    ├── action_items: List[str]
    ├── priority_assessment: str
    ├── summary_text: str
    └── token_usage: Optional[TokenUsage]
```

### Field Validation Rules

- **Email addresses**: Validated via regex pattern in CleanedEmail and EmailSummary
- **Timestamps**: Must be valid ISO 8601 datetime strings, parsed to datetime objects
- **Lists**: Default to empty lists if not provided (using `default_factory=list`)
- **Counts**: Must be non-negative integers
- **URLs**: Must be valid URL strings (validated in ExtractedImageText)
- **Text fields**: No length limits, but should be non-empty strings where required

## Error Handling

### Validation Error Handling

```python
# In Flow
try:
    if hasattr(result, 'pydantic') and result.pydantic:
        self.state.structured_result = result.pydantic
except ValidationError as e:
    logger.error(f"Pydantic validation error: {e}")
    logger.debug(f"Raw result: {result.raw[:500]}")
    # Continue with raw result only
except Exception as e:
    logger.error(f"Unexpected error extracting structured result: {e}", exc_info=True)
```

### Fallback Strategy

1. **Primary**: Use `result.pydantic` for structured data
2. **Secondary**: Parse `result.json_dict` into Pydantic model
3. **Tertiary**: Use `result.raw` as unstructured text
4. **Logging**: Log all failures with context for debugging

### Error Scenarios

| Scenario | Handling | User Impact |
|----------|----------|-------------|
| Missing required field | Log error, use raw result | No structured data in response |
| Invalid field type | Log error, use raw result | No structured data in response |
| Malformed JSON | Log error, use raw result | No structured data in response |
| Serialization error | Log warning, omit structured_result | Only raw result in response |
| Agent doesn't follow format | Log warning, retry with enhanced prompt | May succeed on retry |

## Testing Strategy

### Unit Tests

**Location**: `tests/unit/test_task_outputs.py`

```python
def test_cleaned_email_model():
    """Test CleanedEmail model validation."""
    email = CleanedEmail(
        subject="Test Subject",
        sender="test@example.com",
        timestamp=datetime.now(),
        body="Test body",
        image_urls=["https://example.com/image.jpg"]
    )
    assert email.subject == "Test Subject"
    assert len(email.image_urls) == 1

def test_cleanup_task_output_model():
    """Test CleanupTaskOutput model validation."""
    output = CleanupTaskOutput(
        emails=[],
        total_count=0
    )
    assert output.total_count == 0
    assert len(output.emails) == 0

def test_analysis_task_output_model():
    """Test AnalysisTaskOutput model validation."""
    output = AnalysisTaskOutput(
        total_count=1,
        email_summaries=[],
        action_items=["Action 1"],
        priority_assessment="Low",
        summary_text="Summary"
    )
    assert output.total_count == 1
    assert len(output.action_items) == 1
```

### Integration Tests

**Location**: `tests/integration/test_structured_outputs.py`

```python
def test_crew_returns_structured_output():
    """Test that crew execution returns structured output."""
    crew = GmailReaderCrew().crew()
    result = crew.kickoff(inputs={
        'sender_emails': ['test@example.com'],
        'language': 'en',
        'days': 7
    })
    
    # Verify structured output is available
    assert hasattr(result, 'pydantic')
    assert isinstance(result.pydantic, AnalysisTaskOutput)
    
    # Verify fields are accessible
    assert result.pydantic.total_count >= 0
    assert isinstance(result.pydantic.email_summaries, list)

def test_flow_extracts_structured_result():
    """Test that flow extracts structured result from crew."""
    flow = GmailReadFlow()
    flow.kickoff(inputs={
        'sender_emails': ['test@example.com'],
        'language': 'en',
        'days': 7
    })
    
    # Verify structured result is stored in state
    assert flow.state.structured_result is not None
    assert isinstance(flow.state.structured_result, AnalysisTaskOutput)
```

### API Tests

**Location**: `tests/api/test_structured_responses.py`

```python
async def test_api_returns_structured_result(client: AsyncClient):
    """Test that API response includes structured result."""
    response = await client.post(
        "/api/flows/gmail-read",
        json={
            "sender_emails": ["test@example.com"],
            "language": "en",
            "days": 7
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structured_result field exists
    assert "structured_result" in data
    
    # Verify structured_result has expected fields
    if data["structured_result"]:
        assert "total_count" in data["structured_result"]
        assert "email_summaries" in data["structured_result"]
        assert "action_items" in data["structured_result"]
```

## Backward Compatibility

### Preserved Behaviors

1. **Raw Result Access**: `result.raw` continues to work as before
2. **API Response Format**: Existing `result` field remains unchanged
3. **Flow State**: `result` field in FlowState preserved
4. **Task Descriptions**: Existing descriptions enhanced, not replaced
5. **Agent Configurations**: No changes required to agent YAML

### Migration Path

1. **Phase 1**: Add Pydantic models and `output_pydantic` parameters (non-breaking)
2. **Phase 2**: Update Flow to extract structured data (non-breaking)
3. **Phase 3**: Add `structured_result` to API responses (non-breaking, optional field)
4. **Phase 4**: Update consumers to use structured data (gradual migration)
5. **Phase 5**: Deprecate raw-only access (future, not in this spec)

### Compatibility Matrix

| Component | Before | After | Breaking? |
|-----------|--------|-------|-----------|
| Task outputs | String | Pydantic + String | No |
| Flow state | result: str | result: str + structured_result | No |
| API response | result: str | result: str + structured_result | No |
| Task configs | YAML only | YAML + output_pydantic | No |

## Implementation Notes

### Agent Prompt Engineering

To ensure agents produce valid structured output, task descriptions must:

1. **Explicitly state output format**: Include JSON schema in description
2. **Provide examples**: Show sample output structure
3. **Emphasize requirements**: Use "MUST" language for critical fields
4. **Validate incrementally**: Test with simple cases first

### Performance Considerations

- **Validation overhead**: Pydantic validation adds ~1-5ms per model
- **Serialization cost**: JSON serialization adds ~2-10ms depending on size
- **Memory usage**: Structured models use ~20-30% more memory than strings
- **Overall impact**: Expected <1% increase in total execution time

### Monitoring and Observability

Add logging for:
- Successful structured output extraction
- Validation failures with error details
- Fallback to raw output events
- Serialization errors in API responses
- Token usage statistics per task and total

Example log format:
```
INFO: Successfully extracted structured result from AnalysisTask
INFO: Total token usage: 5750 tokens (prompt: 4150, completion: 1600)
WARNING: Pydantic validation failed for CleanupTask: missing field 'total_count'
ERROR: Failed to serialize structured result: datetime not JSON serializable
```

### Token Usage Tracking Benefits

1. **Cost Monitoring**: Track LLM API costs per analysis
2. **Performance Optimization**: Identify workflows with high token consumption
3. **Capacity Planning**: Estimate infrastructure needs based on usage patterns
4. **Debugging**: Correlate token usage with task failures or timeouts
5. **Billing**: Provide usage metrics for cost allocation or billing
6. **Trend Analysis**: Monitor token usage trends over time to optimize prompts
