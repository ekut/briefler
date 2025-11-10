# Design Document

## Overview

This design document outlines the conversion of the gmail_reader_example.py script into a standard CrewAI crew structure following the project's established patterns. The new structure will use the @CrewBase decorator pattern with YAML configuration files, making the Gmail reader functionality consistent with other crews in the project (e.g., poem_crew).

The conversion will create a modular, configuration-driven crew that separates concerns between code (crew logic) and configuration (agent/task definitions), improving maintainability and reusability.

## Architecture

### Directory Structure

```
src/briefler/crews/gmail_reader_crew/
├── __init__.py
├── gmail_reader_crew.py
└── config/
    ├── agents.yaml
    └── tasks.yaml

examples/
└── gmail_crew_example.py
```

### Component Hierarchy

```
GmailReaderCrew (@CrewBase)
├── email_analyst() -> Agent (@agent decorator)
│   └── GmailReaderTool
├── analyze_emails() -> Task (@task decorator)
└── crew() -> Crew (@crew decorator)
```

## Components and Interfaces

### 1. GmailReaderCrew Class

**File:** `src/briefler/crews/gmail_reader_crew/gmail_reader_crew.py`

**Purpose:** Main crew class that orchestrates the Gmail reading workflow

**Structure:**
```python
from typing import List
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from mailbox_briefler.tools.gmail_reader_tool import GmailReaderTool

@CrewBase
class GmailReaderCrew:
    """Gmail Reader Crew for analyzing unread emails"""
    
    agents: List[BaseAgent]
    tasks: List[Task]
    
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    @agent
    def email_analyst(self) -> Agent:
        # Instantiate and configure agent with GmailReaderTool
        pass
    
    @task
    def analyze_emails(self) -> Task:
        # Configure email analysis task
        pass
    
    @crew
    def crew(self) -> Crew:
        # Assemble and return the crew
        pass
```

**Key Design Decisions:**
- Uses @CrewBase decorator to enable CrewAI's automatic agent/task discovery
- Follows the same pattern as poem_crew for consistency
- Separates configuration from implementation

### 2. Agent Configuration (agents.yaml)

**File:** `src/briefler/crews/gmail_reader_crew/config/agents.yaml`

**Purpose:** Defines the Email Analyst agent's properties

**Structure:**
```yaml
email_analyst:
  role: >
    Email Analyst
  goal: >
    Read and analyze unread emails from {sender_email} and provide 
    comprehensive summaries with key insights
  backstory: >
    You are an expert email analyst who helps users stay on top of 
    important communications. You can read unread emails from specific 
    senders and provide summaries and insights. You have years of 
    experience in information extraction and summarization.
```

**Parameters:**
- `{sender_email}`: Dynamic parameter passed at runtime via kickoff inputs

**Design Rationale:**
- Externalizing configuration allows non-developers to modify agent behavior
- Template parameters enable runtime customization
- Follows YAML structure established by poem_crew

### 3. Task Configuration (tasks.yaml)

**File:** `src/briefler/crews/gmail_reader_crew/config/tasks.yaml`

**Purpose:** Defines the email analysis task

**Structure:**
```yaml
analyze_emails:
  description: >
    Read all unread emails from {sender_email} and provide a comprehensive summary.
    Include the number of messages, their subjects, timestamps, and key points 
    from the content. Organize the information in a clear and readable format.
  expected_output: >
    A structured summary of unread emails including:
    - Total message count
    - List of subjects with timestamps
    - Key information and action items from each message
    - Overall priority assessment
  agent: email_analyst
```

**Parameters:**
- `{sender_email}`: Dynamic parameter passed at runtime

**Design Rationale:**
- Clear description guides the agent's behavior
- Explicit expected_output ensures consistent results
- Agent reference links task to the email_analyst

### 4. Module Initialization

**File:** `src/briefler/crews/gmail_reader_crew/__init__.py`

**Purpose:** Exports the crew class for external use

**Structure:**
```python
from briefler.crews.gmail_reader_crew.gmail_reader_crew import GmailReaderCrew

__all__ = ['GmailReaderCrew']
```

### 5. Example Script

**File:** `examples/gmail_crew_example.py`

**Purpose:** Demonstrates how to use the new crew structure

**Structure:**
```python
#!/usr/bin/env python
from dotenv import load_dotenv
from briefler.crews.gmail_reader_crew import GmailReaderCrew

def main():
    load_dotenv()
    
    # Get sender email from user
    sender_email = input("Enter sender email: ").strip()
    if not sender_email:
        sender_email = "notifications@github.com"
    
    # Instantiate and run crew
    crew = GmailReaderCrew()
    result = crew.crew().kickoff(inputs={'sender_email': sender_email})
    
    print(result.raw)
    
    # Display token usage for debugging
    token_usage = getattr(result, "token_usage", None)
    print(f"Token Usage: {token_usage}")

if __name__ == "__main__":
    main()
```

## Data Models

### Input Data Model

```python
{
    'sender_email': str  # Email address to filter messages by
}
```

**Validation:**
- Must be a valid email format
- Required parameter for crew execution

### Output Data Model

The crew returns a CrewOutput object with:
```python
CrewOutput(
    raw: str,           # Raw text output from the task
    pydantic: None,     # Not using structured output
    json_dict: None,    # Not using JSON output
    tasks_output: List[TaskOutput]  # Individual task outputs
)
```

## Error Handling

### 1. Missing Environment Variables

**Scenario:** GMAIL_CREDENTIALS_PATH or GMAIL_TOKEN_PATH not set

**Handling:**
- GmailReaderTool will raise an exception during initialization
- Error will propagate to crew execution
- User should see clear error message about missing configuration

**Mitigation:**
- Example script should check environment variables before crew instantiation
- Provide helpful error messages pointing to .env.example

### 2. Gmail API Authentication Failure

**Scenario:** Invalid credentials or token expired

**Handling:**
- GmailReaderTool handles authentication flow
- May trigger browser-based OAuth flow
- Errors logged and propagated to crew

**Mitigation:**
- Tool already implements authentication handling
- No additional error handling needed in crew

### 3. Invalid Sender Email

**Scenario:** User provides malformed email address

**Handling:**
- Gmail API will return no results or error
- Agent will report no messages found
- Crew execution completes normally

**Mitigation:**
- Could add email validation in example script
- Not critical for MVP

### 4. No Unread Messages

**Scenario:** No unread messages from specified sender

**Handling:**
- GmailReaderTool returns empty result
- Agent reports no unread messages
- Crew execution completes successfully

**Mitigation:**
- This is expected behavior, not an error
- Agent should clearly communicate the result

## Testing Strategy

### Unit Testing

**Not required for this conversion** - The crew structure is primarily configuration and integration code. The GmailReaderTool already has its own testing.

### Integration Testing

**Manual testing approach:**

1. **Test basic crew execution:**
   - Run example script with valid sender email
   - Verify crew executes without errors
   - Verify output contains expected summary format

2. **Test parameter interpolation:**
   - Verify {sender_email} is correctly replaced in agent goal
   - Verify {sender_email} is correctly replaced in task description
   - Check agent logs to confirm correct configuration

3. **Test with different senders:**
   - Test with sender that has unread messages
   - Test with sender that has no unread messages
   - Test with invalid email format

4. **Test environment configuration:**
   - Verify crew works with credentials from .env
   - Test authentication flow on first run
   - Verify token persistence for subsequent runs

### Validation Checklist

- [ ] Crew can be imported: `from briefler.crews.gmail_reader_crew import GmailReaderCrew`
- [ ] Crew instantiates without errors
- [ ] kickoff() accepts sender_email parameter
- [ ] Agent receives GmailReaderTool correctly
- [ ] YAML configurations load properly
- [ ] Parameter interpolation works
- [ ] Output format matches expected_output specification
- [ ] Example script runs successfully

## Implementation Notes

### Configuration Loading

CrewAI's @CrewBase decorator automatically:
- Loads YAML files specified in agents_config and tasks_config
- Makes configurations available via self.agents_config and self.tasks_config
- Handles parameter interpolation when kickoff(inputs={...}) is called

### Tool Integration

The GmailReaderTool must be instantiated in the @agent method and passed to the Agent constructor:

```python
@agent
def email_analyst(self) -> Agent:
    gmail_tool = GmailReaderTool()
    return Agent(
        config=self.agents_config["email_analyst"],
        tools=[gmail_tool]
    )
```

### Crew Execution Flow

1. User calls `crew.crew().kickoff(inputs={'sender_email': 'example@email.com'})`
2. CrewAI interpolates {sender_email} in YAML configurations
3. Agents and tasks are instantiated with interpolated values
4. Crew executes tasks sequentially
5. Agent uses GmailReaderTool to fetch emails
6. Agent processes and summarizes results
7. CrewOutput is returned to caller

## Migration Path

### Deprecation of Old Example

The old gmail_reader_example.py can be:
- **Option 1:** Kept for reference showing direct tool usage
- **Option 2:** Replaced entirely with new crew-based example
- **Option 3:** Updated to show both approaches

**Recommendation:** Keep both examples with clear documentation about when to use each approach.

### Backward Compatibility

This is a new crew structure, not a modification of existing code, so there are no backward compatibility concerns.

## Future Enhancements

### Potential Improvements (Out of Scope)

1. **Multi-sender support:** Extend crew to handle multiple senders in one execution
2. **Structured output:** Use Pydantic models for typed output
3. **Email filtering:** Add date range, subject filters, etc.
4. **Batch processing:** Process emails in batches for better performance
5. **Caching:** Cache email summaries to avoid re-processing
6. **Flow integration:** Convert to CrewAI Flow for more complex workflows

These enhancements can be considered in future iterations based on user needs.
