# Gmail Reader Tool Examples

This directory contains example scripts demonstrating different approaches for working with Gmail in CrewAI:

1. **Direct Tool Usage** (`gmail_reader_example.py`) - Using GmailReaderTool directly with agents
2. **Crew Structure** (`gmail_crew_example.py`) - Using the structured GmailReaderCrew with YAML configs
3. **Image Text Extraction** (`gmail_image_extraction_example.py`) - Analyzing emails with image text extraction enabled

## Prerequisites

Before running the examples, ensure you have:

1. **Gmail API Credentials**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Gmail API
   - Create OAuth 2.0 credentials (Desktop app type)
   - Download the `credentials.json` file

2. **Environment Configuration**
   - Copy `.env.example` to `.env`
   - Set the following variables:
     ```
     GMAIL_CREDENTIALS_PATH=path/to/credentials.json
     GMAIL_TOKEN_PATH=path/to/token.json
     OPENAI_API_KEY=your_openai_api_key
     ```

3. **Dependencies**
   - Install the project dependencies:
     ```bash
     crewai install
     ```

## Input Parameters

The Gmail Reader Crew supports the following input parameters:

### sender_emails (required)
- **Type**: List of strings
- **Description**: Email addresses to retrieve unread messages from
- **Example**: `["user1@example.com", "user2@example.com"]`
- **Validation**: Must contain at least one valid email address

### language (optional)
- **Type**: String (ISO 639-1 code)
- **Description**: Language for AI-generated summaries
- **Default**: `"en"` (English)
- **Supported codes**: en, ru, es, fr, de, it, pt, zh, ja, ko, ar, hi, nl, pl, tr, sv, no, da, fi, cs, el, he, th, vi, id, ms, uk, ro, hu, sk
- **Example**: `"ru"` for Russian, `"es"` for Spanish

### days (optional)
- **Type**: Integer
- **Description**: Number of days in the past to retrieve unread messages from
- **Default**: `7`
- **Validation**: Must be a positive integer greater than zero
- **Example**: `14` to retrieve messages from the last 2 weeks

## Running the Examples

### Crew Structure Example (Recommended)

The crew-based approach uses YAML configuration files for better maintainability:

```bash
python examples/gmail_crew_example.py
```

This demonstrates:
- Using `@CrewBase` decorator pattern
- YAML-based agent and task configuration
- Structured crew organization following project conventions
- Enhanced input parameters (multiple senders, language, days)

### Direct Tool Usage Example

For simpler use cases or learning purposes, use the direct tool approach:

```bash
python examples/gmail_reader_example.py
```

This demonstrates:
- Direct instantiation of GmailReaderTool
- Manual agent and task creation
- Inline configuration

### Image Text Extraction Example

Demonstrates email analysis with AI-powered image text extraction:

```bash
python examples/gmail_image_extraction_example.py
```

This demonstrates:
- Configuration check for image processing settings
- Analyzing marketing emails with embedded images
- Extracting text from promotional banners and graphics
- Processing multiple senders with image content
- Custom language support with image extraction

**Prerequisites for Image Extraction**:
- Set `IMAGE_PROCESSING_ENABLED=true` in your `.env` file
- Configure optional settings like `IMAGE_ALLOWED_DOMAINS` for security
- Ensure your OpenAI API key supports vision-capable models

**First Run**: The first time you run any example, it will open your browser for Gmail authentication. After authorizing, a `token.json` file will be created for future use.

## Usage Examples

### Example 1: Basic Usage with Default Parameters

```python
from briefler.flows.gmail_read_flow import GmailReadFlow

flow = GmailReadFlow()
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["notifications@github.com"]
    }
})
```

This uses default values:
- Language: `"en"` (English)
- Days: `7` (last week)

### Example 2: Multiple Senders

```python
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": [
            "notifications@github.com",
            "noreply@medium.com",
            "team@company.com"
        ]
    }
})
```

Retrieves unread messages from all three senders in a single execution.

### Example 3: Custom Language (Russian)

```python
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["notifications@github.com"],
        "language": "ru"
    }
})
```

The AI agent will generate the summary entirely in Russian.

### Example 4: Custom Time Range

```python
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["notifications@github.com"],
        "days": 14
    }
})
```

Retrieves messages from the last 14 days instead of the default 7.

### Example 5: All Parameters Combined

```python
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": [
            "notifications@github.com",
            "noreply@medium.com"
        ],
        "language": "es",
        "days": 30
    }
})
```

Retrieves messages from two senders over the last 30 days with Spanish summary.

### Example 6: Backward Compatibility (Single Sender)

```python
# Old format still works - automatically converted to sender_emails list
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_email": "notifications@github.com"
    }
})
```

The single `sender_email` parameter is automatically converted to `sender_emails` list for backward compatibility.

### Additional Examples in gmail_reader_example.py

The direct tool usage script includes additional examples you can uncomment:

**Direct Tool Call** - Call the tool's `_run()` method without an agent:
```python
# direct_tool_usage_example()
```

**Multi-Sender** - Check emails from multiple senders in one execution:
```python
# multi_sender_example()
```

## Example Output

### Single Sender (English)

When you run with a single sender and default parameters:

```
=== Gmail Reader Crew Example ===

Initializing Gmail Read Flow...
Analyzing emails from 1 sender(s)...
Language: en, Days: 7

[Agent execution logs...]

============================================================
RESULTS
============================================================
Found 3 unread messages from notifications@github.com in the last 7 days:

Summary:
- Total messages: 3
- Subjects:
  1. [username/repo] New issue opened (Nov 8, 10:30 AM)
  2. [username/repo] Pull request merged (Nov 8, 2:15 PM)
  3. [username/repo] New comment on issue #123 (Nov 8, 4:45 PM)

Key insights:
- Active development on repository
- One PR successfully merged
- Ongoing discussion on issue #123

Priority: Medium - Review merged PR and respond to issue comment
============================================================
```

### Multiple Senders with Custom Language (Russian)

When you run with multiple senders and Russian language:

```
Initializing Gmail Read Flow...
Analyzing emails from 2 sender(s)...
Language: ru, Days: 7

[Agent execution logs...]

============================================================
RESULTS
============================================================
Найдено 5 непрочитанных сообщений от notifications@github.com, noreply@medium.com за последние 7 дней:

Резюме:
- Всего сообщений: 5
- Темы:
  1. [username/repo] Новая проблема открыта (8 ноя, 10:30)
  2. [username/repo] Pull request объединен (8 ноя, 14:15)
  3. Новая статья: "Understanding AI" (9 ноя, 09:00)
  4. [username/repo] Новый комментарий к проблеме #123 (9 ноя, 16:45)
  5. Еженедельный дайджест от Medium (10 ноя, 08:00)

Ключевые моменты:
- Активная разработка в репозитории
- Новые статьи для чтения на Medium
- Требуется ответ на комментарий в issue #123

Приоритет: Средний - Просмотреть объединенный PR и ответить на комментарий
============================================================
```

## Parameter Validation

The flow validates all input parameters before execution:

### Email Validation
```python
# ✅ Valid
sender_emails = ["user@example.com", "team@company.com"]

# ❌ Invalid - empty list
sender_emails = []  # ValueError: sender_emails must contain at least one email address

# ❌ Invalid - bad format
sender_emails = ["not-an-email"]  # ValueError: Invalid email format: 'not-an-email'
```

### Language Validation
```python
# ✅ Valid
language = "ru"  # Russian
language = "es"  # Spanish

# ❌ Invalid - unsupported code
language = "xx"  # ValueError: Invalid language code: 'xx'. Must be a valid ISO 639-1 code
```

### Days Validation
```python
# ✅ Valid
days = 14  # Last 2 weeks
days = 1   # Last 24 hours

# ❌ Invalid - must be positive
days = 0   # ValueError: days must be a positive integer greater than zero
days = -5  # ValueError: days must be a positive integer greater than zero
```

## Customization

### For Crew Structure (gmail_crew_example.py)

Edit the YAML configuration files:
- `src/briefler/crews/gmail_reader_crew/config/agents.yaml` - Modify agent role, goal, backstory
- `src/briefler/crews/gmail_reader_crew/config/tasks.yaml` - Change task descriptions and expected output

You can also customize input parameters when calling the flow:
```python
# Customize parameters in the trigger payload
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["your@email.com"],
        "language": "fr",  # French
        "days": 30         # Last month
    }
})
```

### For Direct Tool Usage (gmail_reader_example.py)

Modify the script directly:
1. **Sender emails**: Change the `sender_emails` list
2. **Language**: Set the `language` parameter
3. **Days**: Set the `days` parameter
4. **Agent behavior**: Update `role`, `goal`, or `backstory` in Agent constructor
5. **Task descriptions**: Modify the Task `description` and `expected_output`
6. **Additional tools**: Add more tools to the agent's `tools` list

## Image Text Extraction

The Gmail Reader Crew can extract text from images embedded in emails using AI vision capabilities. This is particularly useful for:

- **Marketing emails**: Extract promotional text from banner images
- **Newsletters**: Capture offer details embedded in graphics
- **Bank notifications**: Extract transaction details from statement images
- **Event invitations**: Capture event information from flyer images

### Configuration

To enable image text extraction, add these variables to your `.env` file:

```bash
# Enable image processing
IMAGE_PROCESSING_ENABLED=true

# Optional: Configure limits and security
IMAGE_MAX_SIZE_MB=10
IMAGE_PROCESSING_TIMEOUT=60
IMAGE_MAX_PER_EMAIL=5

# Optional: Restrict to trusted domains (comma-separated)
IMAGE_ALLOWED_DOMAINS=googleusercontent.com,gstatic.com,cdn.example.com
```

### How It Works

1. **Detection**: The system identifies external image URLs (HTTPS) in email HTML
2. **Extraction**: A Vision Agent uses AI vision models to extract text from each image
3. **Integration**: Extracted text is combined with email content for comprehensive analysis

### Security

- Only HTTPS URLs are processed (HTTP rejected for security)
- Optional domain whitelist restricts which sources are trusted
- Images exceeding size limits are automatically skipped
- If no whitelist is set, all HTTPS URLs are allowed

### Example Usage

```python
from briefler.flows.gmail_read_flow import GmailReadFlow

# Ensure IMAGE_PROCESSING_ENABLED=true in .env
flow = GmailReadFlow()

# Analyze marketing emails (likely to contain images)
result = flow.kickoff({
    "crewai_trigger_payload": {
        "sender_emails": ["newsletter@company.com"],
        "language": "en",
        "days": 7
    }
})
```

The analysis result will include text extracted from any images found in the emails, providing a more complete understanding of the email content.

### Supported Image Sources

**Currently Supported (MVP)**:
- External URLs (e.g., `https://cdn.example.com/image.png`)
- Common in newsletters, marketing emails, and notifications
- Covers ~95% of promotional emails with embedded images

**Future Support**:
- Gmail attachments (CID references)
- Base64 inline images

### Configuration Check

Run the image extraction example to verify your configuration:

```bash
python examples/gmail_image_extraction_example.py
```

The script will check your environment variables and show which settings are configured before running the examples.

## Troubleshooting

### Authentication Errors

If you encounter authentication errors:
- Delete the `token.json` file and re-run to re-authenticate
- Verify your `credentials.json` is valid and from a Desktop app OAuth client
- Check that the Gmail API is enabled in your Google Cloud project

### Configuration Errors

If you see "environment variable not set" errors:
- Ensure your `.env` file exists and contains the required variables
- Verify the paths in your `.env` file are correct and accessible

### Rate Limiting

If you hit Gmail API rate limits:
- The tool automatically implements retry logic with exponential backoff
- Wait a few minutes before trying again
- Consider reducing the frequency of requests

## Additional Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [CrewAI Documentation](https://docs.crewai.com/)
- [OAuth 2.0 Setup Guide](https://developers.google.com/gmail/api/quickstart/python)
