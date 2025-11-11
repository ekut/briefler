# Design Document: Email Content Filtering

## Overview

This design implements a two-task workflow for email analysis that separates content cleanup from summarization. A single Email Analysis Agent executes both tasks sequentially, with the Content Cleanup Task removing template boilerplate from email headers and footers while preserving the complete message body before the Summary Task generates the final output. This approach follows CrewAI best practices of "Single Purpose, Single Output" while maintaining simplicity through a single agent.

## Architecture

### Current State

The existing `GmailReaderCrew` has:
- One agent: `email_analyst`
- One task: `analyze_emails`
- Sequential process execution
- GmailReaderTool for fetching emails

### Proposed Changes

Modify `GmailReaderCrew` to include:
- One agent: `email_analyst` (existing, no changes to agent definition)
- Two tasks:
  1. `cleanup_email_content` - removes boilerplate content
  2. `analyze_emails` - generates summary from cleaned content (modified to use context)
- Sequential process execution (unchanged)
- Task context chain: `cleanup_email_content` → `analyze_emails`

### Design Rationale

**Why one agent instead of two?**
- Both tasks require understanding email structure and content
- Reduces complexity and token usage
- Follows CrewAI examples where single agents handle multi-step workflows
- Agent's backstory already covers both analysis and information extraction

**Why two tasks instead of one?**
- Follows CrewAI "Single Purpose, Single Output" principle
- Makes workflow transparent and debuggable
- Enables future extensibility (e.g., adding OCR task between cleanup and summary)
- Allows independent modification of cleanup logic vs summary logic

**Why LLM-based cleanup instead of Python regex?**
- Email headers and footers vary significantly across senders
- Impossible to predict all template formats in advance
- LLM can understand context and distinguish message body from header/footer boilerplate
- Graceful degradation: if some boilerplate remains, it's not critical
- Preserves message body integrity without risk of over-filtering

## Components and Interfaces

### 1. Email Analysis Agent (Modified)

**File:** `src/briefler/crews/gmail_reader_crew/config/agents.yaml`

**Changes:** Update backstory to reflect dual responsibility

```yaml
email_analyst:
  role: >
    Email Content Analyst
  goal: >
    Clean email content by removing boilerplate and analyze emails to provide 
    comprehensive summaries in {language} language with key insights
  backstory: >
    You are an expert email analyst who helps users stay on top of 
    important communications. You excel at identifying and removing 
    repetitive boilerplate content (footers, legal disclaimers, unsubscribe 
    links) while preserving message-specific information. You then analyze 
    the cleaned content to provide summaries and insights in the user's 
    preferred language. You have years of experience in information extraction, 
    content filtering, and multilingual communication. You always respond 
    in the language specified by the user ({language}).
```

### 2. Content Cleanup Task (New)

**File:** `src/briefler/crews/gmail_reader_crew/config/tasks.yaml`

**Purpose:** Remove template boilerplate from email headers and footers while preserving the complete message body

**Key Instructions:**
- Identify and remove header boilerplate (automated notices, browser viewing suggestions, do-not-reply warnings)
- Identify and remove footer boilerplate (separators, multiple blank lines, footer markers)
- Remove repetitive contact information from footers (phone, email, address, social media)
- Remove legal text from footers (copyright, disclaimers, regulatory notices, terms of service)
- Remove unsubscribe mechanisms from footers (links, preference centers)
- **PRESERVE the complete message body** including all promotional content, offers, and announcements
- Preserve action items and deadlines from the message body

**Output:** Complete message body with cleaned headers and footers

```yaml
cleanup_email_content:
  description: >
    Read all unread emails from these senders: {sender_emails} received in the last 
    {days} days and clean the content by removing template boilerplate from email 
    HEADERS and FOOTERS only. The message body must be preserved completely.
    
    For each email, identify and remove:
    
    HEADER BOILERPLATE (remove these):
    - Automated message notices ("This is an automated message, please do not reply")
    - Browser viewing suggestions ("For best viewing, open this email in your browser")
    - Do-not-reply warnings ("Do not reply to this email address")
    - Standard header banners with generic messaging
    
    FOOTER BOILERPLATE (remove these):
    - Email footers (typically after horizontal lines, multiple blank lines, or footer markers)
    - Repetitive contact information (phone numbers, email addresses, physical addresses, social media links)
    - Legal text (copyright notices, confidentiality statements, regulatory disclosures, 
      terms of service links, privacy policy links)
    - Unsubscribe mechanisms (unsubscribe links, preference center links, opt-out instructions)
    - Company information that appears in every email (company name, address, registration details)
    - "Follow us on social media" blocks in footers
    
    CRITICAL PRESERVATION RULES:
    - **PRESERVE THE COMPLETE MESSAGE BODY** - do not remove any content from the main message
    - Preserve ALL promotional content, offers, and announcements from the message body
    - Preserve ALL action items, deadlines, and important details from the message body
    - Only remove template elements from headers (before message body) and footers (after message body)
    - If uncertain whether content is header/footer or message body, preserve it
    - The message body is the primary content between any header boilerplate and footer boilerplate
    
    EXAMPLES OF BOILERPLATE TO REMOVE (from headers/footers only):
    - "This is an automated message. Please do not reply to this email."
    - "View this email in your browser | Forward to a friend"
    - "PT Bank OCBC NISP Tbk, OCBC Tower, Jl. Prof. Dr. Satrio Kav 25, Jakarta..."
    - "You are receiving this email because you registered your email with our service..."
    - "Unsubscribe | Privacy Policy | Terms & Conditions"
    - "© 2024 Company Name. All rights reserved."
    - "This email and any attachments are confidential..."
    - "Follow us: [Facebook] [Twitter] [Instagram]" (only in footers)
    
    Output the cleaned content for each email with:
    - Email subject
    - Sender
    - Timestamp
    - Cleaned message body (boilerplate removed)
  expected_output: >
    A structured list of emails with cleaned content:
    - Subject line
    - Sender email address
    - Timestamp
    - Message body with boilerplate content removed
    
    The output should contain only message-specific information without 
    footers, legal disclaimers, or repetitive organizational metadata.
  agent: email_analyst
```

### 3. Summary Task (Modified)

**File:** `src/briefler/crews/gmail_reader_crew/config/tasks.yaml`

**Changes:**
- Add `context: [cleanup_email_content]` to receive cleaned content
- Update description to clarify it works with pre-cleaned content
- Remove instructions about handling footers (already done in cleanup task)

```yaml
analyze_emails:
  description: >
    Based on the cleaned email content provided, create a comprehensive summary 
    in {language} language.
    
    The content has already been cleaned to remove footers and boilerplate.
    Focus on extracting and organizing:
    - Key information and main points from each message
    - Action items and requests
    - Deadlines and time-sensitive information
    - Overall priority assessment
    
    Organize the information in a clear and readable format.
    
    IMPORTANT: You MUST write your entire summary in {language} language. 
    All text, headings, and descriptions must be in {language}.
  expected_output: >
    A structured summary of emails in {language} language including:
    - Total message count
    - List of subjects with timestamps
    - Key information and action items from each message
    - Overall priority assessment
    
    The entire output must be written in {language} language.
  agent: email_analyst
  context: [cleanup_email_content]
```

### 4. Crew Implementation (Modified)

**File:** `src/briefler/crews/gmail_reader_crew/gmail_reader_crew.py`

**Changes:** Add new task method for cleanup

```python
from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from briefler.tools.gmail_reader_tool import GmailReaderTool


@CrewBase
class GmailReaderCrew:
    """Gmail Reader Crew for analyzing unread emails"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def email_analyst(self) -> Agent:
        gmail_tool = GmailReaderTool()
        return Agent(
            config=self.agents_config["email_analyst"],  # type: ignore[index]
            tools=[gmail_tool],
        )

    @task
    def cleanup_email_content(self) -> Task:
        """Task to clean email content by removing boilerplate"""
        return Task(
            config=self.tasks_config["cleanup_email_content"],  # type: ignore[index]
        )

    @task
    def analyze_emails(self) -> Task:
        """Task to analyze cleaned email content and generate summary"""
        return Task(
            config=self.tasks_config["analyze_emails"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Gmail Reader Crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
```

## Data Models

### Task Input (Unchanged)

```python
{
    "sender_emails": ["user@example.com"],
    "days": 7,
    "language": "en"
}
```

### Cleanup Task Output (Internal)

```
Email 1:
Subject: Monthly Account Statement
Sender: notifications@bank.com
Timestamp: 2024-01-15 10:30:00
Body: Your account statement for December 2024 is now available. 
Total balance: $5,432.10. You had 12 transactions this month.

Email 2:
Subject: Payment Confirmation
Sender: billing@service.com
Timestamp: 2024-01-16 14:22:00
Body: Your payment of $29.99 has been processed successfully. 
Transaction ID: TXN-2024-001234. Next billing date: February 16, 2024.
```

### Summary Task Output (Final)

```markdown
# Email Summary (2 messages)

## 1. Monthly Account Statement
**From:** notifications@bank.com  
**Date:** January 15, 2024 10:30 AM

- Account statement for December 2024 available
- Current balance: $5,432.10
- 12 transactions during the month

## 2. Payment Confirmation
**From:** billing@service.com  
**Date:** January 16, 2024 2:22 PM

- Payment of $29.99 processed successfully
- Transaction ID: TXN-2024-001234
- Next billing: February 16, 2024

**Priority:** Low - Informational updates, no action required
```

## Error Handling

### Scenario 1: Email with No Boilerplate

**Handling:** Cleanup task passes through content unchanged. Summary task proceeds normally.

### Scenario 2: Email with Minimal Message Body

**Handling:** Cleanup task removes header/footer boilerplate, preserves whatever message body exists. Summary task works with available content.

### Scenario 3: Ambiguous Header/Footer Boundary

**Handling:** Cleanup task errs on side of preservation. If unclear whether content is part of message body or footer, treat it as message body. Better to include some footer content than lose message information.

### Scenario 4: Non-English Boilerplate

**Handling:** LLM can identify boilerplate patterns regardless of language. Instructions focus on structural patterns (footers, disclaimers) rather than specific text.

## Testing Strategy

### Unit Testing

Not applicable - this is a prompt-based solution without testable Python logic changes.

### Integration Testing

**Test 1: Footer Boilerplate Removal**
- Input: Email with typical footer (contact info, legal text, unsubscribe)
- Expected: Summary contains no footer information

**Test 2: Header Boilerplate Removal**
- Input: Email with automated notice header ("This is an automated message...")
- Expected: Summary excludes automated notice, includes full message body

**Test 3: Message Body Preservation**
- Input: Email with promotional offer in message body
- Expected: Summary includes the promotional offer

**Test 4: Contact Info in Message Body**
- Input: Email with contact info in message body (not footer)
- Expected: Summary includes the contact info from message body

**Test 5: Multilingual Support**
- Input: Email with non-English boilerplate in various locations
- Expected: Boilerplate removed, summary in requested language

**Test 6: Minimal Content**
- Input: Email with mostly boilerplate
- Expected: Summary notes minimal content, doesn't fail

**Test 7: Header and Footer Boilerplate**
- Input: Email with boilerplate in both header and footer
- Expected: Header and footer boilerplate removed, complete message body preserved

**Test 8: Task Context Chain**
- Verification: Summary task receives cleaned content from cleanup task
- Expected: No direct access to original uncleaned content

### Manual Testing

1. Run with real emails from various senders (banks, services, newsletters)
2. Verify footers are removed consistently
3. Verify important information is preserved
4. Compare output quality before/after implementation

## Performance Considerations

### Token Usage

- **Increase:** Two LLM calls instead of one (cleanup + summary)
- **Mitigation:** Cleanup task reduces token count for summary task by removing boilerplate
- **Net Impact:** Approximately 20-30% increase in total tokens, but improved output quality

### Latency

- **Increase:** Sequential execution adds latency of cleanup task
- **Typical Impact:** +2-5 seconds per email batch
- **Acceptable:** User experience not significantly affected for async email analysis

### Cost

- **Increase:** Proportional to token usage increase (~20-30%)
- **Justification:** Improved summary quality reduces user time reviewing irrelevant information

## Future Extensibility

This design enables future enhancements:

1. **OCR for Images:** Add task between cleanup and summary
   ```
   cleanup_email_content → extract_image_text → analyze_emails
   ```

2. **Attachment Analysis:** Add parallel task for attachment metadata
   ```
   cleanup_email_content → analyze_emails
                         ↘ analyze_attachments ↗
   ```

3. **Memory-Based Learning:** Add CrewAI memory system to learn boilerplate patterns over time
   ```python
   crew = Crew(memory=True, ...)  # Enables pattern learning
   ```

4. **Feedback Loop:** Add task to collect user feedback on cleanup quality
   ```
   analyze_emails → collect_feedback → improve_cleanup_instructions
   ```

## Migration Path

### Phase 1: Implementation (This Spec)
- Add cleanup task to YAML configs
- Update agent backstory
- Modify analyze_emails task to use context
- Add cleanup_email_content method to crew.py

### Phase 2: Validation
- Test with diverse email samples
- Gather user feedback
- Tune cleanup task instructions if needed

### Phase 3: Optimization (Future)
- Monitor token usage and latency
- Consider caching common boilerplate patterns
- Evaluate hybrid approach (regex + LLM) if needed

## Configuration Examples

### Example 1: Conservative Cleanup (Preserve More)

```yaml
cleanup_email_content:
  description: >
    ... (standard description) ...
    
    CONSERVATIVE MODE: When in doubt, preserve content.
    Only remove content that clearly matches common boilerplate patterns.
```

### Example 2: Aggressive Cleanup (Remove More)

```yaml
cleanup_email_content:
  description: >
    ... (standard description) ...
    
    AGGRESSIVE MODE: Remove all repetitive organizational content.
    Focus on preserving only unique message-specific information.
```

## Rollback Plan

If the two-task approach causes issues:

1. **Quick Rollback:** Revert to single `analyze_emails` task
2. **Partial Rollback:** Keep two tasks but merge descriptions
3. **Configuration Toggle:** Add flag to enable/disable cleanup task

```python
# In crew.py
@crew
def crew(self) -> Crew:
    tasks = [self.cleanup_email_content(), self.analyze_emails()] if self.enable_cleanup else [self.analyze_emails()]
    return Crew(agents=self.agents, tasks=tasks, process=Process.sequential, verbose=True)
```
