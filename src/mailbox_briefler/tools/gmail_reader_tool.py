"""Gmail Reader Tool for CrewAI.

This module provides a tool for reading unread emails from Gmail using the Gmail API.
It integrates with CrewAI framework to enable AI agents to access and process email data.
"""

import os
import time
import logging
import base64
import re
import html
from typing import Type, Optional, Callable, Any

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
import json

# Set up logging
logger = logging.getLogger(__name__)


class GmailReaderToolInput(BaseModel):
    """Input schema for GmailReaderTool."""
    
    sender_email: str = Field(
        ..., 
        description="The email address of the sender to filter unread messages from."
    )


class GmailReaderTool(BaseTool):
    """Tool for reading unread emails from Gmail.
    
    This tool authenticates with Gmail API using OAuth 2.0 and retrieves
    unread messages from a specified sender. It returns formatted message
    data including subject, sender, date, and body content.
    
    Configuration:
        Requires environment variables:
        - GMAIL_CREDENTIALS_PATH: Path to credentials.json file
        - GMAIL_TOKEN_PATH: Path to token.json file
    
    Usage:
        tool = GmailReaderTool()
        result = tool._run(sender_email="example@gmail.com")
    """
    
    name: str = "Gmail Reader"
    description: str = (
        "Reads unread emails from a specified sender's email address. "
        "Input should be a valid email address. Returns formatted list of unread "
        "messages including subject, sender, date, and body content."
    )
    args_schema: Type[BaseModel] = GmailReaderToolInput
    
    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, **kwargs):
        """Initialize the Gmail Reader Tool.
        
        Loads configuration from environment variables and validates
        that required paths are set.
        
        Raises:
            ValueError: If required environment variables are not set.
        """
        super().__init__(**kwargs)
        
        # Load configuration from environment variables
        self.credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH')
        self.token_path = os.getenv('GMAIL_TOKEN_PATH')
        
        # Validate configuration
        if not self.credentials_path:
            raise ValueError(
                "GMAIL_CREDENTIALS_PATH environment variable is not set. "
                "Please set it to the path of your credentials.json file."
            )
        
        if not self.token_path:
            raise ValueError(
                "GMAIL_TOKEN_PATH environment variable is not set. "
                "Please set it to the path where token.json should be stored."
            )
        
        # Gmail service will be initialized on first use
        self.service: Optional[Resource] = None
    
    def _retry_with_backoff(
        self, 
        func: Callable, 
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_multiplier: float = 2.0
    ) -> Any:
        """Execute a function with exponential backoff retry logic.
        
        This method implements retry logic with exponential backoff for handling
        transient errors from the Gmail API. It will retry the function up to
        max_retries times, with increasing delays between attempts.
        
        Args:
            func: The function to execute (should be a callable with no arguments).
            max_retries: Maximum number of retry attempts (default: 3).
            initial_delay: Initial delay in seconds before first retry (default: 1.0).
            backoff_multiplier: Multiplier for exponential backoff (default: 2.0).
        
        Returns:
            The return value of the successful function call.
        
        Raises:
            HttpError: If all retry attempts fail or for non-retryable errors.
        """
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func()
            except HttpError as e:
                last_exception = e
                status_code = e.resp.status
                
                # Handle 401 authentication errors - don't retry
                if status_code == 401:
                    logger.error(f"Authentication error (401): {str(e)}")
                    raise RuntimeError(
                        "Authentication failed. Please check your credentials and "
                        "ensure the token is valid. You may need to delete the token "
                        "file and re-authenticate."
                    )
                
                # Handle 429 rate limit errors - retry with backoff
                if status_code == 429:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Rate limit exceeded (429). Retrying in {delay} seconds... "
                            f"(Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        delay *= backoff_multiplier
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise RuntimeError(
                            "Gmail API rate limit exceeded. Please try again later."
                        )
                
                # Handle 5xx server errors - retry with backoff
                if 500 <= status_code < 600:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Server error ({status_code}). Retrying in {delay} seconds... "
                            f"(Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        delay *= backoff_multiplier
                        continue
                    else:
                        logger.error(
                            f"Server error ({status_code}) after {max_retries} attempts: {str(e)}"
                        )
                        raise RuntimeError(
                            f"Gmail API server error ({status_code}). Please try again later."
                        )
                
                # For other HTTP errors, don't retry
                logger.error(f"Gmail API error ({status_code}): {str(e)}")
                raise RuntimeError(
                    f"Gmail API error ({status_code}): {str(e)}"
                )
            
            except Exception as e:
                # For non-HTTP errors, log and re-raise
                logger.error(f"Unexpected error during API call: {str(e)}", exc_info=True)
                raise
        
        # If we exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception
    
    def _initialize_gmail_service(self) -> Resource:
        """Initialize and return Gmail API service.
        
        This method handles the authentication flow:
        1. Checks if token.json exists at the configured path
        2. Loads credentials from token file if it exists
        3. Checks if credentials are expired and refreshes if needed
        4. If no token exists, initiates OAuth flow for new authentication
        5. Saves the generated or refreshed token to token.json file
        
        Returns:
            Gmail API service resource.
        
        Raises:
            FileNotFoundError: If credentials file is not found.
            ValueError: If credentials file is invalid or corrupted.
            RuntimeError: If OAuth flow fails or authentication cannot be completed.
        """
        creds = None
        
        # Check if token.json exists at configured path
        if os.path.exists(self.token_path):
            try:
                # Load credentials from token file
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(
                    f"Token file at {self.token_path} is corrupted or invalid. "
                    f"Please delete the file and re-authenticate. Error: {str(e)}"
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load token from {self.token_path}. "
                    f"Error: {str(e)}"
                )
        
        # Check if credentials are expired and refresh if needed
        if creds and creds.expired and creds.refresh_token:
            try:
                # Refresh credentials if expired and refresh token is available
                creds.refresh(Request())
                
                # Save refreshed token to file
                with open(self.token_path, 'w') as token_file:
                    token_file.write(creds.to_json())
            except RefreshError as e:
                raise RuntimeError(
                    f"Failed to refresh authentication token. The token may have been revoked. "
                    f"Please delete {self.token_path} and re-authenticate. Error: {str(e)}"
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to refresh or save authentication token. Error: {str(e)}"
                )
        
        # If no valid credentials exist, initiate OAuth flow
        if not creds or not creds.valid:
            # Check if credentials.json file exists
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    f"Credentials file not found at {self.credentials_path}. "
                    "Please download credentials.json from Google Cloud Console and "
                    "place it at the specified path."
                )
            
            try:
                # Load credentials.json file
                # Create InstalledAppFlow with credentials and scopes
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, 
                    self.SCOPES
                )
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(
                    f"Credentials file at {self.credentials_path} is invalid or corrupted. "
                    f"Please download a new credentials.json from Google Cloud Console. "
                    f"Error: {str(e)}"
                )
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Credentials file not found at {self.credentials_path}. "
                    "Please download credentials.json from Google Cloud Console and "
                    "place it at the specified path."
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load credentials from {self.credentials_path}. "
                    f"Error: {str(e)}"
                )
            
            try:
                # Run local server flow for user authorization
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise RuntimeError(
                    f"OAuth authentication flow failed. Please ensure you have authorized "
                    f"the application in your browser and that no firewall is blocking the connection. "
                    f"Error: {str(e)}"
                )
            
            try:
                # Save generated token to token.json file
                with open(self.token_path, 'w') as token_file:
                    token_file.write(creds.to_json())
            except (IOError, OSError) as e:
                raise RuntimeError(
                    f"Failed to save authentication token to {self.token_path}. "
                    f"Please check file permissions and disk space. Error: {str(e)}"
                )
        
        try:
            # Build and return Gmail API service using credentials
            service = build('gmail', 'v1', credentials=creds)
            return service
        except Exception as e:
            raise RuntimeError(
                f"Failed to build Gmail API service. Error: {str(e)}"
            )
    
    def _get_unread_messages(self, sender_email: str) -> list:
        """Retrieve unread messages from a specific sender.
        
        This method queries the Gmail API for unread messages from the specified
        sender email address. It handles pagination to retrieve all matching messages,
        fetches full message details for each message ID, and returns a list of
        complete message dictionaries.
        
        The method includes retry logic with exponential backoff for handling
        transient errors like rate limits and server errors.
        
        Args:
            sender_email: The email address of the sender to filter messages from.
        
        Returns:
            List of full message dictionaries with complete message data.
            Returns empty list if no unread messages are found.
        
        Raises:
            RuntimeError: If Gmail API service initialization fails or API errors occur.
        """
        try:
            # Initialize Gmail service if not already done
            if not self.service:
                self.service = self._initialize_gmail_service()
            
            # Construct Gmail API query: "is:unread from:{sender_email}"
            query = f"is:unread from:{sender_email}"
            
            logger.info(f"Querying Gmail API for unread messages from: {sender_email}")
            
            message_ids = []
            page_token = None
            
            # Handle pagination - loop until all pages are retrieved
            while True:
                # Wrap API call in retry logic
                def list_messages():
                    return self.service.users().messages().list(
                        userId='me',
                        q=query,
                        pageToken=page_token
                    ).execute()
                
                try:
                    result = self._retry_with_backoff(list_messages)
                except RuntimeError as e:
                    # Log error with context
                    logger.error(
                        f"Failed to list messages from {sender_email}: {str(e)}",
                        exc_info=True
                    )
                    raise
                
                # Extract message IDs from response
                if 'messages' in result:
                    message_ids.extend(result['messages'])
                
                # Check if there are more pages
                page_token = result.get('nextPageToken')
                
                # Break if no more pages
                if not page_token:
                    break
            
            # Check if message list is empty
            if not message_ids:
                logger.info(f"No unread messages found from {sender_email}")
                # Return empty list if no messages found
                return []
            
            logger.info(f"Found {len(message_ids)} unread message(s) from {sender_email}")
            
            # Fetch full message details for each message ID
            full_messages = []
            for idx, message_info in enumerate(message_ids, 1):
                message_id = message_info['id']
                
                # Wrap API call in retry logic
                def get_message():
                    return self.service.users().messages().get(
                        userId='me',
                        id=message_id,
                        format='full'
                    ).execute()
                
                try:
                    full_message = self._retry_with_backoff(get_message)
                    # Collect all message objects in a list
                    full_messages.append(full_message)
                    logger.debug(f"Retrieved message {idx}/{len(message_ids)}: {message_id}")
                except RuntimeError as e:
                    # Log error with context but continue processing other messages
                    logger.error(
                        f"Failed to retrieve message {message_id} ({idx}/{len(message_ids)}): {str(e)}"
                    )
                    # Continue to next message instead of failing completely
                    continue
                except Exception as e:
                    # Log unexpected errors but continue
                    logger.error(
                        f"Unexpected error retrieving message {message_id}: {str(e)}",
                        exc_info=True
                    )
                    continue
            
            logger.info(f"Successfully retrieved {len(full_messages)} message(s)")
            
            # Return list of message dictionaries
            return full_messages
            
        except Exception as e:
            # Catch any unexpected errors and log with context
            logger.error(
                f"Unexpected error in _get_unread_messages for sender {sender_email}: {str(e)}",
                exc_info=True
            )
            raise RuntimeError(
                f"Failed to retrieve messages from {sender_email}: {str(e)}"
            )
    
    def _extract_attachments(self, parts: list) -> list:
        """Extract attachment metadata from message parts.
        
        This method recursively traverses message parts to identify attachments
        and extract their metadata (filename, mimeType, size). It does not
        download the actual attachment content.
        
        Args:
            parts: List of message parts from Gmail API payload.
        
        Returns:
            List of attachment metadata dictionaries with the following structure:
            [
                {
                    "filename": str,    # Name of the attachment file
                    "mime_type": str,   # MIME type of the attachment
                    "size": int         # Size in bytes
                },
                ...
            ]
        """
        attachments = []
        
        if not parts:
            return attachments
        
        for part in parts:
            # Identify parts with filename in payload
            filename = part.get('filename', '')
            
            # If part has a filename, it's an attachment
            if filename:
                # Extract filename, mimeType, and size
                mime_type = part.get('mimeType', '')
                body = part.get('body', {})
                size = body.get('size', 0)
                
                # Add to attachments list in message data
                attachment_info = {
                    'filename': filename,
                    'mime_type': mime_type,
                    'size': size
                }
                attachments.append(attachment_info)
                
                logger.debug(f"Found attachment: {filename} ({mime_type}, {size} bytes)")
            
            # Recursively check nested parts (for multipart messages)
            nested_parts = part.get('parts', [])
            if nested_parts:
                nested_attachments = self._extract_attachments(nested_parts)
                attachments.extend(nested_attachments)
        
        return attachments
    
    def _extract_message_data(self, message: dict) -> dict:
        """Extract structured data from a Gmail message.
        
        This method parses a Gmail API message object and extracts key information
        including message ID, thread ID, snippet, headers (Subject, From, Date),
        body content, and attachment metadata. It returns a structured dictionary
        that can be easily processed by other methods.
        
        Args:
            message: Gmail API message dictionary with full format.
        
        Returns:
            Dictionary containing extracted message data with the following structure:
            {
                "id": str,              # Gmail message ID
                "thread_id": str,       # Thread ID
                "snippet": str,         # Short preview
                "subject": str,         # Email subject
                "from": str,            # Sender email and name
                "date": str,            # Date sent
                "body": str,            # Decoded message body (to be populated by _decode_message_body)
                "attachments": []       # List of attachment metadata
            }
        
        Raises:
            KeyError: If required message fields are missing.
            Exception: For other parsing errors.
        """
        try:
            # Extract message ID and thread ID
            message_id = message.get('id', '')
            thread_id = message.get('threadId', '')
            
            # Extract snippet for preview
            snippet = message.get('snippet', '')
            
            # Parse payload to get headers
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            
            # Initialize message data dictionary
            message_data = {
                'id': message_id,
                'thread_id': thread_id,
                'snippet': snippet,
                'subject': '',
                'from': '',
                'date': '',
                'body': '',
                'attachments': []
            }
            
            # Extract Subject, From, and Date headers
            for header in headers:
                header_name = header.get('name', '').lower()
                header_value = header.get('value', '')
                
                if header_name == 'subject':
                    message_data['subject'] = header_value
                elif header_name == 'from':
                    message_data['from'] = header_value
                elif header_name == 'date':
                    message_data['date'] = header_value
            
            # Extract attachment metadata from payload parts
            parts = payload.get('parts', [])
            if parts:
                message_data['attachments'] = self._extract_attachments(parts)
            
            # Note: Body will be decoded by _decode_message_body method (task 5.3-5.6)
            
            logger.debug(f"Extracted data for message {message_id}: {message_data['subject']}")
            
            # Return structured dictionary with message data
            return message_data
            
        except KeyError as e:
            logger.error(f"Missing required field in message: {str(e)}", exc_info=True)
            raise KeyError(f"Failed to extract message data: missing field {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting message data: {str(e)}", exc_info=True)
            raise Exception(f"Failed to extract message data: {str(e)}")
    
    def _decode_body_content(self, body_data: str) -> str:
        """Decode base64url encoded body content.
        
        This method handles the actual decoding of Gmail message body content:
        1. Extracts body data from the payload (passed as parameter)
        2. Decodes base64url encoded content
        3. Handles character encoding (UTF-8)
        4. Returns decoded text
        
        Gmail API returns message body content encoded in base64url format.
        This method decodes that content and handles UTF-8 character encoding
        with error replacement for any invalid characters.
        
        Args:
            body_data: Base64url encoded string from Gmail API payload body.
        
        Returns:
            Decoded text as a UTF-8 string. Returns empty string if body_data is empty.
        
        Raises:
            Exception: For decoding errors (logged but not raised to allow processing to continue).
        """
        # Check if body_data is empty
        if not body_data:
            return ''
        
        try:
            # Decode base64url encoded content
            # Gmail uses base64url encoding (URL-safe base64 without padding)
            decoded_bytes = base64.urlsafe_b64decode(body_data)
            
            # Handle character encoding (UTF-8)
            # Use 'replace' error handling to substitute invalid UTF-8 sequences
            # with the Unicode replacement character (U+FFFD)
            decoded_text = decoded_bytes.decode('utf-8', errors='replace')
            
            # Return decoded text
            return decoded_text
            
        except Exception as e:
            # Log error but return empty string to allow processing to continue
            logger.error(f"Error decoding body content: {str(e)}", exc_info=True)
            return ''
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text.
        
        This method strips HTML tags, converts common HTML entities, and preserves
        basic formatting where possible. It handles:
        - Block-level elements (p, div, br, etc.) by adding newlines
        - List items by adding bullet points
        - Links by preserving the URL
        - Common HTML entities (&nbsp;, &amp;, etc.)
        
        Args:
            html_content: HTML string to convert to plain text.
        
        Returns:
            Plain text version of the HTML content with basic formatting preserved.
        """
        if not html_content:
            return ''
        
        try:
            # Convert common HTML entities first
            text = html.unescape(html_content)
            
            # Replace <br> and <br/> tags with newlines
            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
            
            # Replace closing block-level tags with newlines to preserve paragraph structure
            block_tags = ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre']
            for tag in block_tags:
                text = re.sub(f'</{tag}>', '\n', text, flags=re.IGNORECASE)
            
            # Replace list items with bullet points
            text = re.sub(r'<li[^>]*>', '\n• ', text, flags=re.IGNORECASE)
            text = re.sub(r'</li>', '', text, flags=re.IGNORECASE)
            
            # Replace horizontal rules with a line
            text = re.sub(r'<hr[^>]*>', '\n---\n', text, flags=re.IGNORECASE)
            
            # Extract link text and preserve URLs in parentheses
            # Match <a href="url">text</a> and convert to "text (url)"
            text = re.sub(
                r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>',
                r'\2 (\1)',
                text,
                flags=re.IGNORECASE
            )
            
            # Strip all remaining HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            
            # Clean up excessive whitespace
            # Replace multiple spaces with single space
            text = re.sub(r' +', ' ', text)
            
            # Replace multiple newlines with maximum of two newlines
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            
            # Strip leading/trailing whitespace from each line
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(lines)
            
            # Strip leading/trailing whitespace from entire text
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Error converting HTML to text: {str(e)}", exc_info=True)
            # Return original content if conversion fails
            return html_content
    
    def _decode_message_body(self, payload: dict) -> str:
        """Decode message body from Gmail API payload.
        
        This method handles different message formats by checking the payload mimeType:
        - Plain text messages (text/plain): Directly decodes the body
        - HTML messages (text/html): Decodes HTML content and converts to text
        - Multipart messages (multipart/*): Recursively processes parts (handled by task 5.6)
        
        The method determines the message format and routes to the appropriate
        decoding logic based on the mimeType.
        
        Args:
            payload: Gmail API message payload dictionary containing mimeType and body/parts.
        
        Returns:
            Decoded message body as a string. Returns empty string if no body content found.
        
        Raises:
            Exception: For decoding errors or unsupported formats.
        """
        try:
            # Check payload mimeType to determine message format
            mime_type = payload.get('mimeType', '')
            
            logger.debug(f"Decoding message body with mimeType: {mime_type}")
            
            # Handle plain text messages (text/plain)
            if mime_type == 'text/plain':
                # Extract body data from payload
                body_data = payload.get('body', {}).get('data', '')
                if body_data:
                    # Decode base64url encoded content and handle UTF-8 encoding
                    decoded_text = self._decode_body_content(body_data)
                    return decoded_text
                return ''
            
            # Handle HTML messages (text/html)
            elif mime_type == 'text/html':
                # Extract body data from payload
                body_data = payload.get('body', {}).get('data', '')
                if body_data:
                    # Decode base64url encoded content and handle UTF-8 encoding
                    decoded_html = self._decode_body_content(body_data)
                    # Convert HTML to text
                    text = self._html_to_text(decoded_html)
                    return text
                return ''
            
            # Handle multipart messages (multipart/*)
            elif mime_type.startswith('multipart/'):
                # Get parts from payload
                parts = payload.get('parts', [])
                if not parts:
                    logger.debug("Multipart message has no parts")
                    return ''
                
                # Recursively traverse message parts
                # Prioritize text/plain over text/html
                plain_text_body = None
                html_body = None
                
                def extract_from_parts(parts_list):
                    """Recursively extract text from message parts."""
                    nonlocal plain_text_body, html_body
                    
                    for part in parts_list:
                        part_mime_type = part.get('mimeType', '')
                        
                        # Handle text/plain parts
                        if part_mime_type == 'text/plain':
                            body_data = part.get('body', {}).get('data', '')
                            if body_data and not plain_text_body:
                                plain_text_body = self._decode_body_content(body_data)
                        
                        # Handle text/html parts
                        elif part_mime_type == 'text/html':
                            body_data = part.get('body', {}).get('data', '')
                            if body_data and not html_body:
                                decoded_html = self._decode_body_content(body_data)
                                html_body = self._html_to_text(decoded_html)
                        
                        # Recursively handle nested multipart
                        elif part_mime_type.startswith('multipart/'):
                            nested_parts = part.get('parts', [])
                            if nested_parts:
                                extract_from_parts(nested_parts)
                
                # Extract content from all parts recursively
                extract_from_parts(parts)
                
                # Prioritize text/plain over text/html
                if plain_text_body:
                    return plain_text_body
                elif html_body:
                    return html_body
                
                return ''
            
            # Unsupported or unknown mime type
            else:
                logger.warning(f"Unsupported mimeType: {mime_type}")
                return ''
        
        except Exception as e:
            logger.error(f"Error decoding message body: {str(e)}", exc_info=True)
            # Return empty string instead of raising to allow processing to continue
            return ''
    
    def _format_output(self, messages: list, sender_email: str) -> str:
        """Format message list into readable string output.
        
        This method takes a list of processed message dictionaries and formats them
        into a human-readable string that can be consumed by CrewAI agents. It includes:
        - A header with message count and sender email
        - Individual message sections with headers and body
        - Attachment information if present
        - Appropriate message if no unread messages exist
        
        Args:
            messages: List of message dictionaries with extracted data.
            sender_email: The email address of the sender (for header).
        
        Returns:
            Formatted string containing all message information, or a message
            indicating no unread messages were found.
        """
        # Check if messages list is empty
        if not messages:
            # Return "No unread messages" message if empty
            return f"No unread messages found from {sender_email}"
        
        # Count total messages
        message_count = len(messages)
        
        # Create header with message count and sender
        output_lines = [
            f"Found {message_count} unread message{'s' if message_count != 1 else ''} from {sender_email}:",
            ""
        ]
        
        # Format individual messages
        for idx, message in enumerate(messages, 1):
            # Add separator between messages
            output_lines.append("---")
            output_lines.append(f"Message {idx}:")
            
            # Include Subject, From, Date headers
            subject = message.get('subject', '(No Subject)')
            from_header = message.get('from', '(Unknown Sender)')
            date = message.get('date', '(Unknown Date)')
            
            output_lines.append(f"Subject: {subject}")
            output_lines.append(f"From: {from_header}")
            output_lines.append(f"Date: {date}")
            output_lines.append("")
            
            # Include decoded body content
            body = message.get('body', '')
            if body:
                output_lines.append(body)
            else:
                output_lines.append("(No body content)")
            
            output_lines.append("")
            
            # Format attachment information
            attachments = message.get('attachments', [])
            if attachments:
                # Count attachments for each message
                attachment_count = len(attachments)
                output_lines.append(f"Attachments: {attachment_count} file{'s' if attachment_count != 1 else ''}")
                
                # List attachment filenames with metadata
                for attachment in attachments:
                    filename = attachment.get('filename', 'Unknown')
                    mime_type = attachment.get('mime_type', 'Unknown')
                    size = attachment.get('size', 0)
                    
                    # Include mime type and size
                    output_lines.append(f"- {filename} ({mime_type}, {size} bytes)")
                
                output_lines.append("")
        
        return "\n".join(output_lines)
    
    def _run(self, sender_email: str) -> str:
        """Execute the tool to retrieve unread messages from a sender.
        
        Args:
            sender_email: The email address of the sender to filter messages from.
        
        Returns:
            Formatted string containing unread messages or error message.
        """
        # Implementation will be added in subsequent tasks
        return f"Gmail Reader Tool initialized. Ready to read messages from {sender_email}"
