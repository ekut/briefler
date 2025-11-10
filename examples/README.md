# Gmail Reader Tool Examples

This directory contains example scripts demonstrating how to use the GmailReaderTool with CrewAI.

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
     ```

3. **Dependencies**
   - Install the project dependencies:
     ```bash
     uv sync
     ```

## Running the Examples

### Basic Example

The main example demonstrates the complete workflow:

```bash
python examples/gmail_reader_example.py
```

This will:
1. Instantiate the GmailReaderTool
2. Create a CrewAI agent with the tool
3. Create a task to read unread emails from a sender
4. Execute the crew and display results

**First Run**: The first time you run the example, it will open your browser for Gmail authentication. After authorizing, a `token.json` file will be created for future use.

### Direct Tool Usage

To use the tool directly without a CrewAI agent, uncomment the following line in `gmail_reader_example.py`:

```python
# direct_tool_usage_example()
```

This demonstrates how to call the tool's `_run()` method directly.

### Multi-Sender Example

To check emails from multiple senders in a single crew execution, uncomment:

```python
# multi_sender_example()
```

This creates multiple tasks, each checking a different sender.

## Example Output

When you run the basic example, you'll see output similar to:

```
=== Gmail Reader Tool Example ===

Step 1: Instantiating GmailReaderTool...
✓ Tool instantiated successfully

Step 2: Creating CrewAI agent with GmailReaderTool...
✓ Agent created successfully

Step 3: Creating task for the agent...
Enter sender email address to check (or press Enter for default): 
Using default sender: notifications@github.com
✓ Task created successfully

Step 4: Creating and running the crew...
Note: First run may open browser for Gmail authentication

Executing crew...

[Agent execution logs...]

============================================================
RESULTS
============================================================
Found 3 unread messages from notifications@github.com:

---
Message 1:
Subject: [username/repo] New issue opened
From: notifications@github.com
Date: Mon, 8 Nov 2025 10:30:00 -0800

[Message body content...]

Attachments: 0 files

---
[Additional messages...]
============================================================
```

## Customization

You can customize the examples by:

1. **Changing the sender email**: Modify the `sender_email` variable
2. **Adjusting agent behavior**: Update the agent's `role`, `goal`, or `backstory`
3. **Modifying task descriptions**: Change what the agent should do with the emails
4. **Adding more tools**: Include additional tools in the agent's toolkit

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
