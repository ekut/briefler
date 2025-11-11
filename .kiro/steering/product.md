---
inclusion: always
---

# Product: Briefler

AI-powered email analysis using CrewAI multi-agent framework. Fetches unread Gmail messages via OAuth 2.0, analyzes content from specified senders, generates structured summaries with insights and action items.

## Capabilities

Fetch unread emails from specific senders within time window (default 7 days). Process plain text, HTML, multipart/nested formats. Generate multilingual summaries (ISO 639-1 codes). Extract attachment metadata without downloading.

## Flow Parameters

- `sender_emails`: List[str] - Email addresses to filter (required)
- `language`: str - ISO 639-1 code for output (default: "en")
- `days`: int - Lookback period (default: 7)

## Principles

**Read-Only**: Gmail readonly scope, never modifies emails

**Privacy**: Local credential storage, never committed

**Resilience**: Handles malformed emails, API errors with retry logic

**Extensibility**: Tool-based architecture for new sources/capabilities
