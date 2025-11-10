# Gmail Reader Tool Examples

This directory contains example scripts demonstrating two approaches for working with Gmail in CrewAI:

1. **Direct Tool Usage** (`gmail_reader_example.py`) - Using GmailReaderTool directly with agents
2. **Crew Structure** (`gmail_crew_example.py`) - Using the structured GmailReaderCrew with YAML configs

## Prerequisites

Before running the examples, ensure you have:

1. **Gmail API Credentials**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Gmail API
   - Create OAuth 2.0 credentials (Desktop app type)
   - Download the `credentials.json` file

2. **Environment Configuration**
   - Copy `.env.example` to `.env`
   - Set the following variables:
     ```
     GMAIL_CREDENTIALS_PATH=path/to/credentials.json
     GMAIL_TOKEN_PATH=path/to/token.json
     OPENAI_API_KEY=your_openai_api_key
     ```

3. **Dependencies**
   - Install the project dependencies:
     ```bash
     crewai install
     ```

## Running the Examples

### Crew Structure Example (Recommended)

The crew-based approach uses YAML configuration files for better maintainability:

```bash
python examples/gmail_crew_example.py
```

This demonstrates:
- Using `@CrewBase` decorator pattern
- YAML-based agent and task configuration
- Structured crew organization following project conventions

### Direct Tool Usage Example

For simpler use cases or learning purposes, use the direct tool approach:

```bash
python examples/gmail_reader_example.py
```

This demonstrates:
- Direct instantiation of GmailReaderTool
- Manual agent and task creation
- Inline configuration

**First Run**: The first time you run either example, it will open your browser for Gmail authentication. After authorizing, a `token.json` file will be created for future use.

### Additional Examples in gmail_reader_example.py

The direct tool usage script includes additional examples you can uncomment:

**Direct Tool Call** - Call the tool's `_run()` method without an agent:
```python
# direct_tool_usage_example()
```

**Multi-Sender** - Check emails from multiple senders in one execution:
```python
# multi_sender_example()
```

## Example Output

When you run the crew example, you'll see output similar to:

```
=== Gmail Reader Crew Example ===

Enter sender email address (or press Enter for default): 
Using default sender: notifications@github.com

Instantiating GmailReaderCrew...
Analyzing unread emails from notifications@github.com...

Note: First run may open browser for Gmail authentication

[Agent execution logs...]

============================================================
RESULTS
============================================================
Found 3 unread messages from notifications@github.com:

Summary:
- Total messages: 3
- Subjects:
  1. [username/repo] New issue opened (Nov 8, 10:30 AM)
  2. [username/repo] Pull request merged (Nov 8, 2:15 PM)
  3. [username/repo] New comment on issue #123 (Nov 8, 4:45 PM)

Key insights:
- Active development on repository
- One PR successfully merged
- Ongoing discussion on issue #123

Priority: Medium - Review merged PR and respond to issue comment
============================================================
```

## Customization

### For Crew Structure (gmail_crew_example.py)

Edit the YAML configuration files:
- `src/briefler/crews/gmail_reader_crew/config/agents.yaml` - Modify agent role, goal, backstory
- `src/briefler/crews/gmail_reader_crew/config/tasks.yaml` - Change task descriptions and expected output

### For Direct Tool Usage (gmail_reader_example.py)

Modify the script directly:
1. **Sender email**: Change the `sender_email` variable
2. **Agent behavior**: Update `role`, `goal`, or `backstory` in Agent constructor
3. **Task descriptions**: Modify the Task `description` and `expected_output`
4. **Additional tools**: Add more tools to the agent's `tools` list

## Troubleshooting

### Authentication Errors

If you encounter authentication errors:
- Delete the `token.json` file and re-run to re-authenticate
- Verify your `credentials.json` is valid and from a Desktop app OAuth client
- Check that the Gmail API is enabled in your Google Cloud project

### Configuration Errors

If you see "environment variable not set" errors:
- Ensure your `.env` file exists and contains the required variables
- Verify the paths in your `.env` file are correct and accessible

### Rate Limiting

If you hit Gmail API rate limits:
- The tool automatically implements retry logic with exponential backoff
- Wait a few minutes before trying again
- Consider reducing the frequency of requests

## Additional Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [CrewAI Documentation](https://docs.crewai.com/)
- [OAuth 2.0 Setup Guide](https://developers.google.com/gmail/api/quickstart/python)
