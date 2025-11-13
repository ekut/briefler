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

## CrewAI Resources

- [CrewAI Documentation](https://docs.crewai.com)
- [GitHub Repository](https://github.com/joaomdmoura/crewai)
- [Discord Community](https://discord.com/invite/X4JWnZnxPb)
