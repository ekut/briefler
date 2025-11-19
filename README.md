# Briefler

A research project exploring the capabilities of building agentic applications using the [CrewAI](https://crewai.com) framework and Spec-Driven Development (SDD) approach. This project demonstrates multi-agent system creation, external API integration, and code organization following CrewAI best practices, while using specifications to drive feature development.

## Documentation

### Architecture and Project Structure

- [Product Overview](.kiro/steering/product.md) - product description and core functionality
- [Project Structure](.kiro/steering/structure.md) - code organization, patterns, and conventions
- [Technology Stack](.kiro/steering/tech.md) - technologies used and common commands

### Component Specifications

The `.kiro/specs/` directory contains specifications for each feature or component added to the system. Each specification follows a structured format:

- **requirements.md** - defines the problem, goals, and functional requirements
- **design.md** - describes the architectural design and implementation approach
- **tasks.md** - breaks down the implementation into actionable tasks

### Usage Examples

- [Examples README](examples/README.md) - Gmail Reader Tool usage examples

## Image Text Extraction

The Gmail Reader Crew can extract text from images embedded in emails using AI vision capabilities. This feature processes external image URLs (HTTPS) and extracts any visible text content, enriching the email analysis with information that would otherwise be missed.

### How It Works

1. **Image Detection**: The system identifies external image URLs in email HTML content
2. **Vision Processing**: A specialized Vision Agent uses AI vision models to extract text from each image
3. **Content Integration**: Extracted text is combined with email content for comprehensive analysis

### Configuration

Enable image processing by adding these environment variables to your `.env` file:

```bash
# Enable/disable image processing feature
IMAGE_PROCESSING_ENABLED=true

# Maximum image size to process (in MB)
IMAGE_MAX_SIZE_MB=10

# Timeout for processing all images in one email (seconds)
IMAGE_PROCESSING_TIMEOUT=60

# Maximum number of images to process per email
IMAGE_MAX_PER_EMAIL=5

# Optional: Restrict image processing to specific domains (comma-separated)
# If not set, all HTTPS URLs are allowed
IMAGE_ALLOWED_DOMAINS=googleusercontent.com,gstatic.com,cdn.example.com
```

### Feature Flag

The `IMAGE_PROCESSING_ENABLED` flag controls whether images are processed:

- **`true`**: Images are detected and text is extracted using AI vision
- **`false`** (default): Images are ignored, only email text is analyzed

### Security Considerations

- Only HTTPS URLs are processed (HTTP URLs are rejected for security)
- Optional domain whitelist (`IMAGE_ALLOWED_DOMAINS`) restricts which sources are trusted
- If no whitelist is configured, all HTTPS URLs are allowed
- Images exceeding size limits are automatically skipped

### Supported Image Sources

**Currently Supported (MVP):**
- External URLs (e.g., `https://cdn.example.com/image.png`)
- Common in newsletters, marketing emails, and notifications
- Covers ~95% of promotional emails with embedded images

**Future Support:**
- Gmail attachments (CID references)
- Base64 inline images

### Example Use Cases

- **Newsletters**: Extract promotional text from banner images
- **Marketing Emails**: Capture offer details embedded in graphics
- **Bank Notifications**: Extract transaction details from statement images
- **Event Invitations**: Capture event information from flyer images
- **Receipts**: Extract purchase details from receipt images

## Enhanced Input Parameters

The Gmail Reader Crew supports flexible input parameters for customized email analysis:

### Parameters

- **`sender_emails`** (required): List of sender email addresses to analyze
  - Type: `List[str]`
  - Example: `["user1@example.com", "user2@example.com"]`
  - Validation: Must contain at least one valid email address

- **`language`** (optional): ISO 639-1 language code for AI-generated summaries
  - Type: `str`
  - Default: `"en"` (English)
  - Supported codes: `en`, `ru`, `es`, `fr`, `de`, `it`, `pt`, `zh`, `ja`, `ko`, and more
  - Example: `"ru"` for Russian summaries

- **`days`** (optional): Number of days in the past to retrieve unread messages
  - Type: `int`
  - Default: `7`
  - Validation: Must be a positive integer greater than zero
  - Example: `14` for messages from the last two weeks

### Usage Examples

#### Multiple Senders with Default Settings

```python
from briefler.flows.gmail_read_flow import GmailReadFlow

flow = GmailReadFlow()
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": [
            "notifications@github.com",
            "noreply@medium.com"
        ]
    }
})
```

#### Custom Language (Russian)

```python
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["user@example.com"],
        "language": "ru"
    }
})
```

#### Custom Time Range (30 days)

```python
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["newsletter@company.com"],
        "days": 30
    }
})
```

#### All Parameters Combined

```python
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": [
            "team@company.com",
            "support@service.com",
            "alerts@monitoring.com"
        ],
        "language": "es",
        "days": 14
    }
})
```

#### Command Line with Trigger Payload

```bash
python src/briefler/main.py '{
    "sender_emails": ["user@example.com"],
    "language": "fr",
    "days": 7
}'
```

### Backward Compatibility

The system maintains full backward compatibility with existing code:

```python
# Old format (still supported)
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_email": "user@example.com"  # Automatically converted to sender_emails list
    }
})

# Equivalent new format
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["user@example.com"]
    }
})
```

When parameters are omitted, default values are applied:
- `language` defaults to `"en"`
- `days` defaults to `7`

## Quick Start

### Installation

```bash
# Install UV package manager
pip install uv

# Install project dependencies
crewai install
```

### Configuration

Create a `.env` file based on `.env.example` and add required keys:

```bash
OPENAI_API_KEY=your_openai_api_key
GMAIL_CREDENTIALS_PATH=path/to/credentials.json
GMAIL_TOKEN_PATH=path/to/token.json
```

### Running

```bash
# Run the main flow
crewai run

# Visualize flow structure
crewai plot

# Run examples
python examples/gmail_crew_example.py
```

## Structured Task Outputs

The Gmail Reader Crew uses structured task outputs powered by Pydantic models, providing type-safe, validated, and programmatically accessible data throughout the agent workflow. This replaces unstructured string outputs with deterministic data structures.

### Overview

All three tasks (CleanupTask, VisionTask, and AnalysisTask) return Pydantic models that can be accessed via:
- **`.pydantic`**: Direct Pydantic model instance with full type safety
- **`.json_dict`**: Dictionary representation for JSON serialization
- **`.raw`**: String representation (maintained for backward compatibility)

### Task Output Models

#### CleanupTaskOutput

Returned by the email cleanup task:

```python
{
  "emails": [
    {
      "subject": "Meeting Tomorrow",
      "sender": "colleague@company.com",
      "timestamp": "2025-11-19T10:30:00Z",
      "body": "Cleaned email body with boilerplate removed...",
      "image_urls": ["https://example.com/image1.jpg"]
    }
  ],
  "total_count": 5,
  "token_usage": {
    "total_tokens": 1250,
    "prompt_tokens": 950,
    "completion_tokens": 300
  }
}
```

#### VisionTaskOutput

Returned by the image text extraction task:

```python
{
  "extracted_texts": [
    {
      "image_url": "https://example.com/banner.jpg",
      "extracted_text": "Special Offer: 50% Off Today Only!",
      "has_text": true
    }
  ],
  "total_images_processed": 3,
  "images_with_text": 2,
  "token_usage": {
    "total_tokens": 850,
    "prompt_tokens": 600,
    "completion_tokens": 250
  }
}
```

#### AnalysisTaskOutput

Returned by the final analysis task:

```python
{
  "total_count": 5,
  "email_summaries": [
    {
      "subject": "Project Update",
      "sender": "manager@company.com",
      "timestamp": "2025-11-19T14:00:00Z",
      "key_points": [
        "Q4 deadline moved to December 15",
        "New team member joining next week"
      ],
      "action_items": [
        "Update project timeline",
        "Prepare onboarding materials"
      ],
      "has_deadline": true
    }
  ],
  "action_items": [
    "Update project timeline",
    "Prepare onboarding materials",
    "Review budget proposal"
  ],
  "priority_assessment": "High - Multiple time-sensitive items require immediate attention",
  "summary_text": "# Email Analysis\n\n## Summary\n...",
  "token_usage": {
    "total_tokens": 2100,
    "prompt_tokens": 1500,
    "completion_tokens": 600
  }
}
```

### TokenUsage Model

All task outputs include optional token usage statistics for cost monitoring:

```python
{
  "total_tokens": 1250,      # Total tokens used (prompt + completion)
  "prompt_tokens": 950,       # Tokens in the prompt
  "completion_tokens": 300    # Tokens in the completion
}
```

**Use Cases:**
- Monitor LLM API costs per analysis
- Identify workflows with high token consumption
- Optimize prompts based on usage patterns
- Track token usage trends over time

### Accessing Structured Data

#### In Python Code

```python
from briefler.flows.gmail_read_flow import GmailReadFlow

# Execute flow
flow = GmailReadFlow()
flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["user@example.com"],
        "language": "en",
        "days": 7
    }
})

# Access structured result
if flow.state.structured_result:
    # Type-safe access to fields
    total_emails = flow.state.structured_result.total_count
    action_items = flow.state.structured_result.action_items
    
    # Iterate through email summaries
    for summary in flow.state.structured_result.email_summaries:
        print(f"Subject: {summary.subject}")
        print(f"Sender: {summary.sender}")
        print(f"Key Points: {', '.join(summary.key_points)}")
        if summary.has_deadline:
            print("⚠️ Time-sensitive!")

# Access token usage
if flow.state.total_token_usage:
    print(f"Total tokens used: {flow.state.total_token_usage.total_tokens}")
    print(f"Prompt tokens: {flow.state.total_token_usage.prompt_tokens}")
    print(f"Completion tokens: {flow.state.total_token_usage.completion_tokens}")

# Backward compatibility - raw result still available
markdown_result = flow.state.result
```

#### Via API

When using the FastAPI backend, structured data is included in API responses:

```bash
curl -X POST http://localhost:8000/api/flows/gmail-read \
  -H "Content-Type: application/json" \
  -d '{
    "sender_emails": ["user@example.com"],
    "language": "en",
    "days": 7
  }'
```

**Response:**

```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": "# Email Analysis\n\n## Summary\n...",
  "structured_result": {
    "total_count": 5,
    "email_summaries": [
      {
        "subject": "Project Update",
        "sender": "manager@company.com",
        "timestamp": "2025-11-19T14:00:00Z",
        "key_points": ["Q4 deadline moved", "New team member"],
        "action_items": ["Update timeline", "Prepare materials"],
        "has_deadline": true
      }
    ],
    "action_items": ["Update timeline", "Prepare materials"],
    "priority_assessment": "High",
    "summary_text": "# Email Analysis..."
  },
  "token_usage": {
    "total_tokens": 4200,
    "prompt_tokens": 3050,
    "completion_tokens": 1150
  },
  "parameters": {
    "sender_emails": ["user@example.com"],
    "language": "en",
    "days": 7
  },
  "timestamp": "2025-11-19T10:30:00Z",
  "execution_time_seconds": 45.2
}
```

#### Programmatic API Access

```python
import requests

# Execute analysis
response = requests.post(
    "http://localhost:8000/api/flows/gmail-read",
    json={
        "sender_emails": ["user@example.com"],
        "language": "en",
        "days": 7
    }
)

data = response.json()

# Access structured data
if "structured_result" in data and data["structured_result"]:
    structured = data["structured_result"]
    
    # Extract specific information
    total_emails = structured["total_count"]
    all_action_items = structured["action_items"]
    priority = structured["priority_assessment"]
    
    # Process email summaries
    for email in structured["email_summaries"]:
        print(f"\n📧 {email['subject']}")
        print(f"From: {email['sender']}")
        print(f"Date: {email['timestamp']}")
        
        if email["key_points"]:
            print("\nKey Points:")
            for point in email["key_points"]:
                print(f"  • {point}")
        
        if email["action_items"]:
            print("\nAction Items:")
            for item in email["action_items"]:
                print(f"  ✓ {item}")
        
        if email["has_deadline"]:
            print("\n⚠️ Time-sensitive email!")

# Monitor token usage
if "token_usage" in data and data["token_usage"]:
    usage = data["token_usage"]
    print(f"\n💰 Token Usage:")
    print(f"  Total: {usage['total_tokens']}")
    print(f"  Prompt: {usage['prompt_tokens']}")
    print(f"  Completion: {usage['completion_tokens']}")
    
    # Calculate approximate cost (example: GPT-4 pricing)
    prompt_cost = usage['prompt_tokens'] * 0.00003  # $0.03 per 1K tokens
    completion_cost = usage['completion_tokens'] * 0.00006  # $0.06 per 1K tokens
    total_cost = prompt_cost + completion_cost
    print(f"  Estimated cost: ${total_cost:.4f}")

# Backward compatibility - markdown result still available
markdown_text = data["result"]
```

### Backward Compatibility

The structured output implementation maintains full backward compatibility:

- **`result` field**: Still contains the full markdown-formatted analysis text
- **`flow.state.result`**: Still accessible in Flow code
- **Existing tests**: Continue to pass without modification
- **API consumers**: Can continue using the `result` field without changes

New `structured_result` and `token_usage` fields are optional additions that don't break existing integrations.

### Error Handling

If structured output extraction fails (e.g., validation errors), the system gracefully falls back to raw output:

```python
# In Flow
try:
    if hasattr(result, 'pydantic') and result.pydantic:
        self.state.structured_result = result.pydantic
except Exception as e:
    logger.warning(f"Could not extract structured result: {e}")
    # Flow continues with raw result only
```

The API will still return a successful response with the `result` field populated, but `structured_result` will be `null`.

## CrewAI Resources

- [CrewAI Documentation](https://docs.crewai.com)
- [GitHub Repository](https://github.com/joaomdmoura/crewai)
- [Discord Community](https://discord.com/invite/X4JWnZnxPb)
