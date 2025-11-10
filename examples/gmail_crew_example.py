#!/usr/bin/env python
"""Example script demonstrating how to use the GmailReaderCrew.

This example shows how to use the crew-based structure for reading and
analyzing Gmail messages from a specific sender.

Prerequisites:
- Set up Gmail API credentials (credentials.json)
- Configure environment variables in .env file:
  - GMAIL_CREDENTIALS_PATH=path/to/credentials.json
  - GMAIL_TOKEN_PATH=path/to/token.json
"""

from dotenv import load_dotenv
from briefler.crews.gmail_reader_crew import GmailReaderCrew


def main():
    """Main function demonstrating GmailReaderCrew usage."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    print("=== Gmail Reader Crew Example ===\n")
    
    # Get sender email from user input
    sender_email = input("Enter sender email address (or press Enter for default): ").strip()
    if not sender_email:
        sender_email = "notifications@github.com"
        print(f"Using default sender: {sender_email}\n")
    
    # Instantiate the crew
    print("Instantiating GmailReaderCrew...")
    gmail_crew = GmailReaderCrew()
    
    # Run the crew with the sender_email parameter
    print(f"Analyzing unread emails from {sender_email}...\n")
    print("Note: First run may open browser for Gmail authentication\n")
    
    result = gmail_crew.crew().kickoff(inputs={'sender_email': sender_email})
    
    # Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(result.raw)
    print("="*60)
    
    # Display token usage for debugging
    token_usage = getattr(result, "token_usage", None)
    if token_usage:
        print(f"\nToken Usage: {token_usage}")


if __name__ == "__main__":
    main()
