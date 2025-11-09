"""Gmail Reader Tool for CrewAI.

This module provides a tool for reading unread emails from Gmail using the Gmail API.
It integrates with CrewAI framework to enable AI agents to access and process email data.
"""

import os
import time
import logging
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
    
    def _run(self, sender_email: str) -> str:
        """Execute the tool to retrieve unread messages from a sender.
        
        Args:
            sender_email: The email address of the sender to filter messages from.
        
        Returns:
            Formatted string containing unread messages or error message.
        """
        # Implementation will be added in subsequent tasks
        return f"Gmail Reader Tool initialized. Ready to read messages from {sender_email}"
