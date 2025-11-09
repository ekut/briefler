"""Gmail Reader Tool for CrewAI.

This module provides a tool for reading unread emails from Gmail using the Gmail API.
It integrates with CrewAI framework to enable AI agents to access and process email data.
"""

import os
from typing import Type, Optional

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from google.auth.exceptions import RefreshError
import json


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
    
    def _run(self, sender_email: str) -> str:
        """Execute the tool to retrieve unread messages from a sender.
        
        Args:
            sender_email: The email address of the sender to filter messages from.
        
        Returns:
            Formatted string containing unread messages or error message.
        """
        # Implementation will be added in subsequent tasks
        return f"Gmail Reader Tool initialized. Ready to read messages from {sender_email}"
