# Implementation Plan

- [x] 1. Set up project dependencies and configuration
  - Add required packages to pyproject.toml: google-api-python-client, google-auth-httplib2, google-auth-oauthlib
  - Update .env.example with GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH variables
  - Add credentials.json and token.json to .gitignore
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Create GmailReaderTool base structure
  - [x] 2.1 Create gmail_reader_tool.py file in src/mailbox_briefler/tools/
    - Define GmailReaderTool class inheriting from BaseTool
    - Set name and description class attributes
    - Define __init__ method to load environment variables
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 2.2 Implement configuration loading and validation
    - Load GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH from environment
    - Validate that paths are not empty
    - Raise ValueError with descriptive message if configuration is missing
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 3. Implement Gmail API authentication
  - [x] 3.1 Create _initialize_gmail_service method
    - Define Gmail API scopes (gmail.readonly)
    - Check if token.json exists at configured path
    - Load credentials from token file if it exists
    - _Requirements: 1.4, 1.5_
  
  - [x] 3.2 Implement OAuth flow for new authentication
    - Load credentials.json file
    - Create InstalledAppFlow with credentials and scopes
    - Run local server flow for user authorization
    - Save generated token to token.json file
    - _Requirements: 1.5_
  
  - [x] 3.3 Implement token refresh logic
    - Check if credentials are expired
    - Refresh credentials if expired and refresh token is available
    - Save refreshed token to file
    - Build and return Gmail API service using credentials
    - _Requirements: 1.4, 1.5_
  
  - [x] 3.4 Add authentication error handling
    - Catch file not found errors for credentials
    - Catch OAuth flow errors
    - Raise descriptive exceptions for authentication failures
    - _Requirements: 4.1_

- [x] 4. Implement message retrieval functionality
  - [x] 4.1 Create _get_unread_messages method
    - Construct Gmail API query: "is:unread from:{sender_email}"
    - Call users().messages().list() with query
    - Handle pagination if more than one page of results
    - Extract message IDs from response
    - _Requirements: 2.1, 2.3_
  
  - [x] 4.2 Fetch full message details
    - For each message ID, call users().messages().get() with format='full'
    - Collect all message objects in a list
    - Return list of message dictionaries
    - _Requirements: 2.2_
  
  - [x] 4.3 Implement empty results handling
    - Check if message list is empty
    - Return empty list if no messages found
    - _Requirements: 2.4_
  
  - [x] 4.4 Add API error handling and retry logic
    - Catch HttpError exceptions
    - Handle 429 rate limit errors with exponential backoff
    - Handle 401 authentication errors
    - Log errors with context
    - Implement retry logic with maximum 3 attempts
    - _Requirements: 2.5, 4.2, 4.4_

- [x] 5. Implement message parsing and data extraction
  - [x] 5.1 Create _extract_message_data method
    - Extract message ID and thread ID
    - Extract snippet for preview
    - Parse payload to get headers and body
    - Return structured dictionary with message data
    - _Requirements: 2.2_
  
  - [x] 5.2 Implement header extraction
    - Iterate through payload headers
    - Extract Subject, From, and Date headers
    - Store in message data dictionary
    - _Requirements: 2.2_
  
  - [x] 5.3 Create _decode_message_body method
    - Check payload mimeType to determine message format
    - Handle plain text messages (text/plain)
    - Handle HTML messages (text/html)
    - Handle multipart messages (multipart/*)
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 5.4 Implement body content decoding
    - Extract body data from payload
    - Decode base64url encoded content
    - Handle character encoding (UTF-8)
    - Return decoded text
    - _Requirements: 5.4_
  
  - [x] 5.5 Implement HTML to text conversion
    - For HTML content, strip HTML tags
    - Convert common HTML entities
    - Preserve basic formatting where possible
    - _Requirements: 5.2_
  
  - [x] 5.6 Handle multipart messages
    - Recursively traverse message parts
    - Prioritize text/plain over text/html
    - Extract content from appropriate part
    - _Requirements: 5.3_
  
  - [x] 5.7 Extract attachment metadata
    - Identify parts with filename in payload
    - Extract filename, mimeType, and size
    - Add to attachments list in message data
    - Do not download attachment content
    - _Requirements: 5.5_

- [x] 6. Implement output formatting
  - [x] 6.1 Create _format_output method
    - Check if messages list is empty
    - Return "No unread messages" message if empty
    - Count total messages
    - Create header with message count and sender
    - _Requirements: 2.4_
  
  - [x] 6.2 Format individual messages
    - For each message, create formatted section
    - Include Subject, From, Date headers
    - Include decoded body content
    - Add separator between messages
    - _Requirements: 2.2, 3.5_
  
  - [x] 6.3 Format attachment information
    - Count attachments for each message
    - List attachment filenames with metadata
    - Include mime type and size
    - _Requirements: 5.5_

- [x] 7. Implement main _run method
  - [x] 7.1 Add input validation
    - Check if sender_email is empty or None
    - Validate email format using basic regex
    - Raise ValueError for invalid input
    - _Requirements: 4.3_
  
  - [x] 7.2 Orchestrate message retrieval and formatting
    - Call _get_unread_messages with sender_email
    - For each message, call _extract_message_data
    - Decode message body using _decode_message_body for each message
    - Call _format_output with processed messages and sender_email
    - Return formatted string
    - _Requirements: 3.4, 3.5_
  
  - [x] 7.3 Add comprehensive error handling
    - Wrap operations in try-except block
    - Catch and handle specific exceptions
    - Return user-friendly error messages
    - Log errors with full context
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

- [x] 8. Add logging and monitoring
  - [x] 8.1 Set up logging configuration
    - Import logging module
    - Create logger instance for the module
    - Configure log level from environment or default to INFO
    - _Requirements: 4.5_
  
  - [x] 8.2 Add logging statements
    - Log tool initialization
    - Log authentication events
    - Log API calls and responses (metadata only)
    - Log errors with full stack traces
    - Do not log email content for security
    - _Requirements: 4.5_

- [x] 9. Update package initialization
  - [x] 9.1 Update src/mailbox_briefler/tools/__init__.py
    - Import GmailReaderTool
    - Add to __all__ list for public API
    - _Requirements: 3.1_

- [ ] 10. Create example usage and documentation
  - [ ] 10.1 Create example script
    - Write example showing how to instantiate the tool
    - Show how to register with CrewAI agent
    - Demonstrate agent task using the tool
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 10.2 Add docstrings
    - Add module-level docstring
    - Add class docstring with usage examples
    - Add method docstrings with parameters and returns
    - _Requirements: 3.2_
