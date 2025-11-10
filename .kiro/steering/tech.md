# Technology Stack

## Build System & Package Management

- **Package Manager**: UV (modern Python package manager)
- **Build Backend**: Hatchling
- **Python Version**: >=3.10, <3.14

## Core Dependencies

- **CrewAI**: v1.2.0 - Multi-agent AI framework with tools extension
- **Google API Client**: Gmail API integration
  - `google-api-python-client` >=2.0.0
  - `google-auth-httplib2` >=0.1.0
  - `google-auth-oauthlib` >=1.0.0
- **Pydantic**: Data validation and settings management
- **Python-dotenv**: Environment variable management

## Common Commands

### Installation & Setup
```bash
# Install UV package manager
pip install uv

# Install project dependencies
crewai install
```

### Running the Project
```bash
# Run the main flow
crewai run

# Run with custom entry point
python src/briefler/main.py

# Run with trigger payload
python src/briefler/main.py '{"key": "value"}'

# Visualize flow structure
crewai plot
```

### Development
```bash
# Run example scripts
python examples/gmail_crew_example.py
python examples/gmail_reader_example.py
```

## Environment Configuration

Required environment variables (see `.env.example`):
- `OPENAI_API_KEY`: OpenAI API key for AI agents
- `GMAIL_CREDENTIALS_PATH`: Path to Gmail API credentials.json
- `GMAIL_TOKEN_PATH`: Path to store OAuth token.json

## Authentication Flow

Gmail API uses OAuth 2.0:
1. First run opens browser for user authorization
2. Token saved to configured path for subsequent runs
3. Automatic token refresh when expired
4. Supports credential path expansion with `~` for home directory
