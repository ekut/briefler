# Briefler

A research project exploring the capabilities of building agentic applications using the [CrewAI](https://crewai.com) framework. This project demonstrates multi-agent system creation, external API integration, and code organization following CrewAI best practices.

## Documentation

### Architecture and Project Structure

- [Product Overview](.kiro/steering/product.md) - product description and core functionality
- [Project Structure](.kiro/steering/structure.md) - code organization, patterns, and conventions
- [Technology Stack](.kiro/steering/tech.md) - technologies used and common commands

### Component Specifications

#### Gmail Reader Tool
- [Requirements](.kiro/specs/gmail-reader-tool/requirements.md) - Gmail reader tool requirements
- [Design](.kiro/specs/gmail-reader-tool/design.md) - architectural design
- [Tasks](.kiro/specs/gmail-reader-tool/tasks.md) - implementation tasks

#### CrewAI Structure Conversion
- [Requirements](.kiro/specs/crewai-structure-conversion/requirements.md) - crew structure conversion requirements
- [Design](.kiro/specs/crewai-structure-conversion/design.md) - crew architecture design
- [Tasks](.kiro/specs/crewai-structure-conversion/tasks.md) - conversion tasks

### Usage Examples

- [Examples README](examples/README.md) - Gmail Reader Tool usage examples

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
