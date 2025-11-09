# Design Document: Gmail Reader Tool

## Overview

The Gmail Reader Tool is a custom CrewAI tool that enables AI agents to read unread emails from specified senders using the Gmail API. The tool implements OAuth 2.0 authentication and provides structured email data that can be processed by CrewAI agents.

### Key Features

- OAuth 2.0 authentication via credentials.json and token.json files
- Query unread messages filtered by sender email address
- Extract message metadata (subject, sender, date) and body content
- Handle multiple email formats (plain text, HTML, multipart)
- Integrate seamlessly with CrewAI framework as a BaseTool
- Robust error handling and logging

## Architecture

### Component Structure

```
src/mailbox_briefler/tools/
├── __init__.py
└── gmail_reader_tool.py
```

### Class Hierarchy

```
BaseTool (from crewai.tools)
    └── GmailReaderTool
```

### Dependencies

- `google-api-python-client`: Gmail API client
- `google-auth-httplib2`: HTTP library for Google Auth
- `google-auth-oauthlib`: OAuth 2.0 flow implementation
- `crewai`: CrewAI framework (BaseTool)
- `python-dotenv`: Environment variable management
- `base64`: Email content decoding
- `email`: Email parsing utilities

## Components and Interfaces

### GmailReaderTool Class

**Inheritance**: `BaseTool` from `crewai.tools`

**Class Attributes**:
- `name: str = "Gmail Reader"` - Tool identifier for CrewAI
- `description: str` - Detailed description for LLM agents explaining the tool's purpose and usage

**Instance Attributes**:
- `credentials_path: str` - Path to credentials.json file
- `token_path: str` - Path to token.json file
- `service: Resource` - Gmail API service instance
- `scopes: List[str]` - Gmail API scopes (readonly)

**Methods**:

1. `__init__(self)`
   - Load configuration from environment variables
   - Validate required paths
   - Initialize Gmail service

2. `_initialize_gmail_service(self) -> Resource`
   - Load or create OAuth credentials
   - Handle token refresh and authentication flow
   - Build and return Gmail API service

3. `_run(self, sender_email: str) -> str`
   - Main execution method called by CrewAI
   - Query Gmail API for unread messages from sender
   - Process and format results
   - Return structured string output

4. `_get_unread_messages(self, sender_email: str) -> List[Dict]`
   - Query Gmail API with filter: `is:unread from:{sender_email}`
   - Retrieve message IDs
   - Fetch full message details for each ID
   - Return list of message dictionaries

5. `_extract_message_data(self, message: Dict) -> Dict`
   - Parse message payload
   - Extract headers (Subject, From, Date)
   - Extract body content
   - Handle attachments metadata
   - Return structured message data

6. `_decode_message_body(self, payload: Dict) -> str`
   - Handle plain text, HTML, and multipart messages
   - Decode base64url encoded content
   - Convert HTML to readable text if necessary
   - Return decoded body text

7. `_format_output(self, messages: List[Dict]) -> str`
   - Format message list into readable string
   - Include message count
   - Structure each message with headers and body
   - Return formatted output for agent consumption

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│ GmailReaderTool Initialization                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Load GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH from .env  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Token exists? │
                  └───────────────┘
                    │           │
                 Yes│           │No
                    │           │
                    ▼           ▼
          ┌──────────────┐  ┌──────────────────────┐
          │ Load token   │  │ Start OAuth flow     │
          │ from file    │  │ with credentials.json│
          └──────────────┘  └──────────────────────┘
                    │           │
                    │           ▼
                    │     ┌──────────────────────┐
                    │     │ User authorizes      │
                    │     │ in browser           │
                    │     └──────────────────────┘
                    │           │
                    │           ▼
                    │     ┌──────────────────────┐
                    │     │ Save token to file   │
                    │     └──────────────────────┘
                    │           │
                    └───────┬───┘
                            ▼
                  ┌──────────────────┐
                  │ Token valid?     │
                  └──────────────────┘
                    │           │
                 Yes│           │No
                    │           │
                    ▼           ▼
          ┌──────────────┐  ┌──────────────────┐
          │ Build Gmail  │  │ Refresh token    │
          │ service      │  │ and save         │
          └──────────────┘  └──────────────────┘
                    │           │
                    └───────┬───┘
                            ▼
                  ┌──────────────────┐
                  │ Service ready    │
                  └──────────────────┘
```

### Message Retrieval Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Agent calls tool with sender_email parameter                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Validate sender_email parameter                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Query Gmail API: is:unread from:{sender_email}              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Messages      │
                  │ found?        │
                  └───────────────┘
                    │           │
                 Yes│           │No
                    │           │
                    ▼           ▼
          ┌──────────────┐  ┌──────────────────────┐
          │ Fetch full   │  │ Return "No unread    │
          │ message      │  │ messages" message    │
          │ details      │  └──────────────────────┘
          └──────────────┘
                    │
                    ▼
          ┌──────────────────────┐
          │ For each message:    │
          │ - Extract headers    │
          │ - Decode body        │
          │ - Handle attachments │
          └──────────────────────┘
                    │
                    ▼
          ┌──────────────────────┐
          │ Format output string │
          └──────────────────────┘
                    │
                    ▼
          ┌──────────────────────┐
          │ Return to agent      │
          └──────────────────────┘
```

## Data Models

### Message Data Structure

```python
{
    "id": str,                    # Gmail message ID
    "thread_id": str,             # Thread ID
    "subject": str,               # Email subject
    "from": str,                  # Sender email and name
    "date": str,                  # Date sent
    "body": str,                  # Decoded message body
    "snippet": str,               # Short preview
    "attachments": [              # List of attachment metadata
        {
            "filename": str,
            "mime_type": str,
            "size": int
        }
    ]
}
```

### Tool Output Format

```
Found X unread message(s) from {sender_email}:

---
Message 1:
Subject: {subject}
From: {from}
Date: {date}

{body}

Attachments: {attachment_count} file(s)
- {filename} ({mime_type}, {size} bytes)

---
Message 2:
...
```

## Error Handling

### Error Categories and Responses

1. **Configuration Errors**
   - Missing environment variables
   - Invalid file paths
   - Action: Raise `ValueError` with descriptive message

2. **Authentication Errors**
   - Invalid credentials
   - Expired or revoked token
   - OAuth flow failure
   - Action: Raise `AuthenticationError` with guidance for re-authentication

3. **API Errors**
   - Rate limit exceeded (429)
   - Network errors
   - Invalid query
   - Action: Catch exceptions, log details, return user-friendly error message

4. **Validation Errors**
   - Empty or invalid sender_email
   - Malformed email address
   - Action: Raise `ValueError` with validation message

5. **Parsing Errors**
   - Corrupted message data
   - Unsupported encoding
   - Action: Log error, skip message, continue processing others

### Error Handling Strategy

```python
try:
    # Gmail API operation
except HttpError as e:
    if e.resp.status == 429:
        return "Rate limit exceeded. Please try again later."
    elif e.resp.status == 401:
        raise AuthenticationError("Authentication failed. Please check credentials.")
    else:
        logger.error(f"Gmail API error: {e}")
        return f"Error accessing Gmail: {str(e)}"
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return f"An unexpected error occurred: {str(e)}"
```

### Retry Logic

Implement exponential backoff for transient errors:
- Initial retry delay: 1 second
- Maximum retries: 3
- Backoff multiplier: 2
- Apply to: Network errors, 5xx server errors

## Testing Strategy

### Unit Tests

1. **Authentication Tests**
   - Test credential loading from environment
   - Test token file creation and loading
   - Mock OAuth flow
   - Test token refresh

2. **Message Retrieval Tests**
   - Test query construction
   - Test message list retrieval
   - Test empty result handling
   - Mock Gmail API responses

3. **Message Parsing Tests**
   - Test plain text extraction
   - Test HTML to text conversion
   - Test multipart message handling
   - Test header extraction
   - Test attachment metadata extraction

4. **Error Handling Tests**
   - Test missing environment variables
   - Test invalid sender email
   - Test API error responses
   - Test network failures

5. **Output Formatting Tests**
   - Test single message formatting
   - Test multiple messages formatting
   - Test empty results message

### Integration Tests

1. **End-to-End Flow**
   - Test complete authentication flow
   - Test actual Gmail API calls (with test account)
   - Test message retrieval and parsing
   - Verify output format

2. **CrewAI Integration**
   - Test tool registration with CrewAI agent
   - Test tool invocation from agent
   - Verify agent can process tool output

### Test Environment Setup

- Use test Gmail account with known messages
- Store test credentials separately
- Mock Gmail API for unit tests
- Use actual API for integration tests (with rate limiting)

## Configuration

### Environment Variables

Required in `.env` file:

```
GMAIL_CREDENTIALS_PATH=path/to/credentials.json
GMAIL_TOKEN_PATH=path/to/token.json
```

### Gmail API Scopes

```python
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
```

This scope provides read-only access to Gmail, sufficient for reading messages without modification capabilities.

### Gmail API Setup Requirements

1. Create project in Google Cloud Console
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download credentials.json
5. Place credentials.json at configured path
6. First run will trigger OAuth flow and create token.json

## Integration with CrewAI

### Tool Registration

```python
from src.mailbox_briefler.tools.gmail_reader_tool import GmailReaderTool

# In agent configuration
gmail_tool = GmailReaderTool()

agent = Agent(
    role='Email Analyst',
    goal='Analyze emails from specific senders',
    tools=[gmail_tool],
    # ... other agent config
)
```

### Agent Usage Example

```python
# Agent task
task = Task(
    description='Read all unread emails from sender@example.com and summarize',
    agent=email_analyst_agent,
    expected_output='Summary of unread emails'
)

# The agent will automatically use the Gmail Reader tool
# by calling it with the sender email address
```

### Tool Invocation by Agent

The LLM will understand to use the tool based on the description:

```
Tool: Gmail Reader
Description: Reads unread emails from a specified sender's email address. 
Input should be a valid email address. Returns formatted list of unread 
messages including subject, sender, date, and body content.
```

## Performance Considerations

1. **API Rate Limits**
   - Gmail API: 250 quota units per user per second
   - Batch requests when possible
   - Implement exponential backoff

2. **Message Size**
   - Limit body content to first 10KB for large messages
   - Truncate with indicator if exceeded
   - Avoid downloading attachment content

3. **Caching**
   - Cache credentials in memory after loading
   - Reuse Gmail service instance
   - Consider caching message IDs for short duration

4. **Concurrent Access**
   - Tool is stateless after initialization
   - Safe for concurrent use by multiple agents
   - Each agent gets own tool instance

## Security Considerations

1. **Credential Storage**
   - Never commit credentials.json or token.json to version control
   - Add to .gitignore
   - Use environment variables for paths
   - Restrict file permissions (600)

2. **Token Management**
   - Token provides read-only access
   - Tokens expire and auto-refresh
   - Revoke tokens when no longer needed

3. **Data Handling**
   - Email content may contain sensitive information
   - Log only metadata, not content
   - Sanitize output if logging

4. **API Access**
   - Use minimal required scopes
   - Monitor API usage
   - Implement rate limiting

## Future Enhancements

1. **Mark as Read**
   - Add optional parameter to mark messages as read after retrieval
   - Requires additional Gmail scope

2. **Date Filtering**
   - Add date range parameters
   - Filter messages by received date

3. **Label Filtering**
   - Support filtering by Gmail labels
   - Combine with sender filter

4. **Batch Processing**
   - Process multiple senders in single call
   - Return grouped results

5. **Attachment Download**
   - Optional attachment content retrieval
   - Save to temporary location
   - Return file paths

6. **Message Caching**
   - Cache retrieved messages
   - Avoid redundant API calls
   - Implement TTL for cache entries
