#!/usr/bin/env python
"""Example script demonstrating how to use GmailReaderTool with CrewAI.

This example shows:
1. How to instantiate the GmailReaderTool
2. How to register it with a CrewAI agent
3. How to create a task that uses the tool
4. How to run the crew and process email data

Prerequisites:
- Set up Gmail API credentials (credentials.json)
- Configure environment variables in .env file:
  - GMAIL_CREDENTIALS_PATH=path/to/credentials.json
  - GMAIL_TOKEN_PATH=path/to/token.json
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

# Import the GmailReaderTool
from briefler.tools.gmail_reader_tool import GmailReaderTool


def main():
    """Main function demonstrating GmailReaderTool usage with CrewAI."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Verify required environment variables are set
    if not os.getenv('GMAIL_CREDENTIALS_PATH'):
        print("Error: GMAIL_CREDENTIALS_PATH not set in .env file")
        return
    
    if not os.getenv('GMAIL_TOKEN_PATH'):
        print("Error: GMAIL_TOKEN_PATH not set in .env file")
        return
    
    print("=== Gmail Reader Tool Example ===\n")
    
    # Step 1: Instantiate the GmailReaderTool
    print("Step 1: Instantiating GmailReaderTool...")
    gmail_tool = GmailReaderTool()
    print("✓ Tool instantiated successfully\n")
    
    # Step 2: Create a CrewAI agent with the tool
    print("Step 2: Creating CrewAI agent with GmailReaderTool...")
    email_analyst = Agent(
        role='Email Analyst',
        goal='Read and analyze unread emails from specific senders',
        backstory=(
            'You are an expert email analyst who helps users stay on top of '
            'important communications. You can read unread emails from specific '
            'senders and provide summaries and insights.'
        ),
        tools=[gmail_tool],  # Register the tool with the agent
        verbose=True,
        allow_delegation=False
    )
    print("✓ Agent created successfully\n")
    
    # Step 3: Create a task that uses the tool
    print("Step 3: Creating task for the agent...")
    
    # Get sender email from user input or use a default
    sender_email = input("Enter sender email address to check (or press Enter for default): ").strip()
    if not sender_email:
        sender_email = "notifications@github.com"  # Default example
        print(f"Using default sender: {sender_email}")
    
    analyze_emails_task = Task(
        description=(
            f'Read all unread emails from {sender_email} and provide a brief summary. '
            f'Include the number of messages, their subjects, and key points from the content.'
        ),
        agent=email_analyst,
        expected_output=(
            'A summary of unread emails including message count, subjects, '
            'and key information from each message.'
        )
    )
    print("✓ Task created successfully\n")
    
    # Step 4: Create and run the crew
    print("Step 4: Creating and running the crew...")
    print("Note: First run may open browser for Gmail authentication\n")
    
    email_crew = Crew(
        agents=[email_analyst],
        tasks=[analyze_emails_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute the crew
    print("Executing crew...\n")
    result = email_crew.kickoff()
    
    # Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(result.raw)
    print("="*60)


def direct_tool_usage_example():
    """Example of using the tool directly without CrewAI agent."""
    
    print("\n=== Direct Tool Usage Example ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Instantiate the tool
    gmail_tool = GmailReaderTool()
    
    # Use the tool directly
    sender_email = input("Enter sender email address: ").strip()
    if not sender_email:
        print("No email provided, exiting.")
        return
    
    print(f"\nFetching unread messages from {sender_email}...\n")
    
    # Call the tool's _run method directly
    result = gmail_tool._run(sender_email=sender_email)
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(result)
    print("="*60)


def multi_sender_example():
    """Example showing how to check multiple senders with a single agent."""
    
    print("\n=== Multi-Sender Example ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Instantiate the tool
    gmail_tool = GmailReaderTool()
    
    # Create agent
    email_analyst = Agent(
        role='Email Analyst',
        goal='Monitor emails from multiple important senders',
        backstory=(
            'You are an email monitoring specialist who tracks communications '
            'from multiple sources and provides consolidated reports.'
        ),
        tools=[gmail_tool],
        verbose=True,
        allow_delegation=False
    )
    
    # Define multiple senders to check
    senders = [
        "notifications@github.com",
        "noreply@google.com",
        "team@company.com"
    ]
    
    # Create tasks for each sender
    tasks = []
    for sender in senders:
        task = Task(
            description=(
                f'Check unread emails from {sender} and list the subjects. '
                f'If there are no unread messages, simply state that.'
            ),
            agent=email_analyst,
            expected_output=f'Summary of unread emails from {sender}'
        )
        tasks.append(task)
    
    # Create crew with multiple tasks
    email_crew = Crew(
        agents=[email_analyst],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    # Execute
    print("Checking multiple senders...\n")
    result = email_crew.kickoff()
    
    print("\n" + "="*60)
    print("MULTI-SENDER RESULTS")
    print("="*60)
    print(result.raw)
    print("="*60)


if __name__ == "__main__":
    # Run the main example
    main()
    
    # Uncomment to try other examples:
    # direct_tool_usage_example()
    # multi_sender_example()
