"""Gmail Reader Tool for CrewAI.

This module provides a tool for reading unread emails from Gmail using the Gmail API.
It integrates with CrewAI framework to enable AI agents to access and process email data.
"""

import os
from typing import Type

from pydantic import BaseModel, Field
from crewai.tools import BaseTool


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
    
    def _run(self, sender_email: str) -> str:
        """Execute the tool to retrieve unread messages from a sender.
        
        Args:
            sender_email: The email address of the sender to filter messages from.
        
        Returns:
            Formatted string containing unread messages or error message.
        """
        # Implementation will be added in subsequent tasks
        return f"Gmail Reader Tool initialized. Ready to read messages from {sender_email}"
