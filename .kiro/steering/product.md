---
inclusion: always
---

# Product: Briefler

AI-powered email analysis tool using CrewAI multi-agent framework. Fetches unread Gmail messages from specified senders and generates structured summaries with insights and action items.

## Core Functionality

- Filters unread emails by sender within configurable time window (default: 7 days)
- Processes all email formats: plain text, HTML, multipart/nested MIME
- Generates multilingual summaries using ISO 639-1 language codes
- Extracts attachment metadata (filename, size, type) without downloading content
- Uses OAuth 2.0 with automatic token refresh

## Input Parameters

- `sender_emails`: List[str] - Required email addresses to filter
- `language`: str - ISO 639-1 code for summary output (default: "en")
- `days`: int - Lookback period in days (default: 7)

## Critical Constraints

- Read-only access: Uses `gmail.readonly` scope, never modifies emails
- Privacy: Credentials stored locally, never committed to version control
- Error handling: Implement exponential backoff retry for API calls
- Email processing: Handle malformed emails gracefully with UTF-8 fallback
