---
inclusion: always
---

# Product: Briefler

AI-powered email analysis using CrewAI. Fetches unread Gmail from specified senders and generates structured summaries with insights and action items.

## Core Behavior

**Email Processing:**
- Filter unread emails by sender list within time window (default: 7 days)
- Process MIME: text/plain, text/html, multipart/nested
- Base64url decode with UTF-8 fallback
- Extract attachment metadata only (filename, size, type) - never download
- Strip HTML, preserve text formatting

**Output:**
- Multilingual summaries using ISO 639-1 codes
- Structured with insights and action items
- Default language: English ("en")

## API Contract

**Input:**
- `sender_emails`: List[str] - Required
- `language`: str - Optional, ISO 639-1 (default: "en")
- `days`: int - Optional, lookback period (default: 7)

**Legacy:**
- `sender_email` (singular) supported but deprecated - convert to `sender_emails` list

## Security

- Use `gmail.readonly` scope only - never modify emails
- Store credentials locally - never commit `.env`, `credentials.json`, `token.json`
- OAuth: first run opens browser, token auto-refreshes
- Exponential backoff for HTTP 429
- Handle malformed emails gracefully
