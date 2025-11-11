#!/usr/bin/env python
"""Example script demonstrating how to use the GmailReadFlow.

This example shows how to use the flow-based structure for reading and
analyzing Gmail messages from one or more senders with enhanced parameters.

Enhanced Parameters:
- sender_emails: List of sender email addresses (required)
- language: ISO 639-1 language code for summaries (optional, default: "en")
- days: Number of days in the past to retrieve messages (optional, default: 7)

Prerequisites:
- Set up Gmail API credentials (credentials.json)
- Configure environment variables in .env file:
  - GMAIL_CREDENTIALS_PATH=path/to/credentials.json
  - GMAIL_TOKEN_PATH=path/to/token.json
"""

from dotenv import load_dotenv
from briefler.flows.gmail_read_flow import GmailReadFlow


def example_basic():
    """Example 1: Basic usage with single sender (backward compatible)."""
    print("\n=== Example 1: Basic Usage (Single Sender) ===\n")
    
    # Single sender with default parameters (language="en", days=7)
    flow = GmailReadFlow()
    result = flow.kickoff({
        "crewai_trigger_payload": {
            "sender_emails": ["notifications@github.com"]
        }
    })
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(result.get("result", "No result"))
    print("="*60)


def example_multiple_senders():
    """Example 2: Multiple senders with default parameters."""
    print("\n=== Example 2: Multiple Senders ===\n")
    
    # Multiple senders - analyze emails from several sources at once
    flow = GmailReadFlow()
    result = flow.kickoff({
        "crewai_trigger_payload": {
            "sender_emails": [
                "notifications@github.com",
                "noreply@medium.com",
                "newsletter@example.com"
            ]
        }
    })
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(result.get("result", "No result"))
    print("="*60)


def example_custom_language():
    """Example 3: Custom language parameter (Russian)."""
    print("\n=== Example 3: Custom Language (Russian) ===\n")
    
    # Request summary in Russian language
    # Supported languages: en, ru, es, fr, de, it, pt, zh, ja, ko, etc.
    flow = GmailReadFlow()
    result = flow.kickoff({
        "crewai_trigger_payload": {
            "sender_emails": ["notifications@github.com"],
            "language": "ru"  # ISO 639-1 language code
        }
    })
    
    print("\n" + "="*60)
    print("RESULTS (in Russian)")
    print("="*60)
    print(result.get("result", "No result"))
    print("="*60)


def example_custom_days():
    """Example 4: Custom days parameter (14 days)."""
    print("\n=== Example 4: Custom Time Range (14 days) ===\n")
    
    # Retrieve emails from the last 14 days instead of default 7
    flow = GmailReadFlow()
    result = flow.kickoff({
        "crewai_trigger_payload": {
            "sender_emails": ["notifications@github.com"],
            "days": 14  # Look back 14 days
        }
    })
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(result.get("result", "No result"))
    print("="*60)


def example_all_parameters():
    """Example 5: All parameters combined."""
    print("\n=== Example 5: All Parameters Combined ===\n")
    
    # Multiple senders, custom language, and custom time range
    flow = GmailReadFlow()
    result = flow.kickoff({
        "crewai_trigger_payload": {
            "sender_emails": [
                "notifications@github.com",
                "noreply@medium.com"
            ],
            "language": "es",  # Spanish summary
            "days": 30  # Last 30 days
        }
    })
    
    print("\n" + "="*60)
    print("RESULTS (in Spanish, last 30 days)")
    print("="*60)
    print(result.get("result", "No result"))
    print("="*60)


def example_backward_compatible():
    """Example 6: Backward compatibility with old sender_email parameter."""
    print("\n=== Example 6: Backward Compatibility ===\n")
    
    # Old parameter name still works (automatically converted to sender_emails list)
    flow = GmailReadFlow()
    result = flow.kickoff({
        "crewai_trigger_payload": {
            "sender_email": "notifications@github.com"  # Old parameter name
        }
    })
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(result.get("result", "No result"))
    print("="*60)


def main():
    """Main function demonstrating GmailReadFlow usage with various examples."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    print("=== Gmail Read Flow Examples ===")
    print("\nNote: First run may open browser for Gmail authentication")
    print("\nAvailable examples:")
    print("1. Basic usage (single sender)")
    print("2. Multiple senders")
    print("3. Custom language (Russian)")
    print("4. Custom time range (14 days)")
    print("5. All parameters combined")
    print("6. Backward compatibility")
    print("0. Run all examples")
    
    choice = input("\nSelect example to run (0-6): ").strip()
    
    examples = {
        "1": example_basic,
        "2": example_multiple_senders,
        "3": example_custom_language,
        "4": example_custom_days,
        "5": example_all_parameters,
        "6": example_backward_compatible,
    }
    
    if choice == "0":
        # Run all examples
        for example_func in examples.values():
            example_func()
    elif choice in examples:
        examples[choice]()
    else:
        print("Invalid choice. Running basic example...")
        example_basic()


if __name__ == "__main__":
    main()
