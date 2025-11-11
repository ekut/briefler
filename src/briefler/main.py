#!/usr/bin/env python
"""
Main entry point for Briefler Project.

This module provides standard entry points for running the Gmail Read Flow.
"""

from briefler.flows.gmail_read_flow import GmailReadFlow


def kickoff():
    """
    Standard entry point for running the flow.
    Usage: crewai run
    """
    flow = GmailReadFlow()
    flow.kickoff()


def plot():
    """
    Generate a visual plot of the flow structure.
    Usage: crewai plot
    """
    flow = GmailReadFlow()
    flow.plot()


def run_with_trigger():
    """
    Run the flow with external trigger payload.
    
    Usage:
        python src/briefler/main.py '{"sender_emails": ["user@example.com"], "language": "en", "days": 7}'
    """
    import json
    import sys

    # Get trigger payload from command line argument
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    # Create flow and kickoff with trigger payload
    flow = GmailReadFlow()

    try:
        result = flow.kickoff(inputs={"crewai_trigger_payload": trigger_payload})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}")


if __name__ == "__main__":
    import sys
    
    # If command line arguments provided, use run_with_trigger
    if len(sys.argv) > 1:
        run_with_trigger()
    else:
        kickoff()
