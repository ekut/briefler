---
inclusion: always
---

# Product: Briefler

AI-powered email analysis using CrewAI multi-agent framework. Fetches unread Gmail messages, analyzes content from specified senders, generates structured summaries with insights and action items.

## Core Capabilities

- Filter unread emails by sender within configurable time window (default 7 days)
- Process all email formats: plain text, HTML, multipart/nested MIME
- Generate multilingual summaries using ISO 639-1 language codes
- Extract attachment metadata without downloading content
- OAuth 2.0 authentication with automatic token refresh

## Input Parameters

- `sender_emails`: List[str] - Required. Email addresses to filter
- `language`: str - Optional. ISO 639-1 code for summary output (default: "en")
- `days`: int - Optional. Lookback period in days (default: 7)

## Design Principles

- **Read-Only**: Uses `gmail.readonly` scope, never modifies emails
- **Privacy-First**: Credentials stored locally, never committed to version control
- **Resilient**: Gracefully handles malformed emails, API errors with exponential backoff retry
- **Extensible**: Tool-based architecture enables adding new data sources and capabilities
