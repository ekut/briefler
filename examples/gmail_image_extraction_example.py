#!/usr/bin/env python3
"""
Example: Gmail Analysis with Image Text Extraction

This example demonstrates how to use the Gmail Reader Crew with image text
extraction enabled. The system will:
1. Fetch unread emails from specified senders
2. Detect external image URLs in email HTML
3. Extract text from images using AI vision
4. Analyze complete content including image texts

Prerequisites:
- Set IMAGE_PROCESSING_ENABLED=true in .env
- Configure OPENAI_API_KEY with a vision-capable model
- Set up Gmail OAuth credentials
"""

import os
from dotenv import load_dotenv
from briefler.flows.gmail_read_flow import GmailReadFlow

# Load environment variables
load_dotenv()


def main():
    """Run Gmail analysis with image text extraction."""
    
    # Verify image processing is enabled
    image_processing = os.getenv('IMAGE_PROCESSING_ENABLED', 'false').lower()
    if image_processing != 'true':
        print("⚠️  IMAGE_PROCESSING_ENABLED is not set to 'true' in .env")
        print("   Image text extraction will be skipped.")
        print()
    
    # Example 1: Analyze marketing emails (likely to contain images)
    print("=" * 60)
    print("Example 1: Marketing Emails with Images")
    print("=" * 60)
    print()
    
    flow = GmailReadFlow()
    result = flow.kickoff({
        "crewai_trigger_payload": {
            "sender_emails": [
                "newsletter@company.com",
                "promotions@store.com"
            ],
            "language": "en",
            "days": 7
        }
    })
    
    print("Analysis Result:")
    print("-" * 60)
    print(result)
    print()
    
    # Example 2: Bank notifications (may contain transaction images)
    print("=" * 60)
    print("Example 2: Bank Notifications")
    print("=" * 60)
    print()
    
    result = flow.kickoff({
        "crewai_trigger_payload": {
            "sender_emails": ["notifications@bank.com"],
            "language": "en",
            "days": 14
        }
    })
    
    print("Analysis Result:")
    print("-" * 60)
    print(result)
    print()
    
    # Example 3: Multiple senders with custom language
    print("=" * 60)
    print("Example 3: Multiple Senders (Spanish)")
    print("=" * 60)
    print()
    
    result = flow.kickoff({
        "crewai_trigger_payload": {
            "sender_emails": [
                "noreply@github.com",
                "team@company.com",
                "alerts@service.com"
            ],
            "language": "es",
            "days": 7
        }
    })
    
    print("Analysis Result:")
    print("-" * 60)
    print(result)
    print()


def check_configuration():
    """Check if image processing is properly configured."""
    print("=" * 60)
    print("Image Processing Configuration Check")
    print("=" * 60)
    print()
    
    config_vars = {
        'IMAGE_PROCESSING_ENABLED': os.getenv('IMAGE_PROCESSING_ENABLED', 'not set'),
        'IMAGE_MAX_SIZE_MB': os.getenv('IMAGE_MAX_SIZE_MB', 'not set (default: 10)'),
        'IMAGE_PROCESSING_TIMEOUT': os.getenv('IMAGE_PROCESSING_TIMEOUT', 'not set (default: 60)'),
        'IMAGE_MAX_PER_EMAIL': os.getenv('IMAGE_MAX_PER_EMAIL', 'not set (default: 5)'),
        'IMAGE_ALLOWED_DOMAINS': os.getenv('IMAGE_ALLOWED_DOMAINS', 'not set (all HTTPS URLs allowed)')
    }
    
    for key, value in config_vars.items():
        status = "✓" if value != 'not set' and not value.startswith('not set') else "○"
        print(f"{status} {key}: {value}")
    
    print()
    
    if config_vars['IMAGE_PROCESSING_ENABLED'].lower() == 'true':
        print("✓ Image processing is ENABLED")
    else:
        print("○ Image processing is DISABLED")
        print("  Set IMAGE_PROCESSING_ENABLED=true in .env to enable")
    
    print()


if __name__ == "__main__":
    # First check configuration
    check_configuration()
    
    # Ask user to proceed
    response = input("Proceed with examples? (y/n): ")
    if response.lower() == 'y':
        main()
    else:
        print("Exiting. Update your .env file and try again.")
