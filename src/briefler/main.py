#!/usr/bin/env python
"""
Flow Template for Briefler Project

This is a skeleton template for creating new CrewAI flows.
Copy and modify this template when creating new flows.

Example usage:
    1. Define your state model (FlowState)
    2. Create flow steps using @start() and @listen() decorators
    3. Integrate your crews and tools
    4. Implement kickoff(), plot(), and run_with_trigger() functions
"""

from pydantic import BaseModel
from crewai.flow import Flow, listen, start


class FlowState(BaseModel):
    """
    Define the state model for your flow.
    Add fields that will be passed between flow steps.
    """
    # Example fields:
    # input_data: str = ""
    # result: str = ""
    pass


class BrieflerFlow(Flow[FlowState]):
    """
    Main flow class for orchestrating crew execution.
    
    Flow steps are defined using decorators:
    - @start(): Entry point of the flow
    - @listen(method_name): Triggered after specified method completes
    """

    @start()
    def initialize(self, crewai_trigger_payload: dict = None):
        """
        Entry point of the flow.
        
        Args:
            crewai_trigger_payload: Optional trigger data from external sources
        """
        print("Initializing flow...")
        
        # Use trigger payload if available
        if crewai_trigger_payload:
            print(f"Using trigger payload: {crewai_trigger_payload}")
            # Process trigger payload and update state
            # self.state.input_data = crewai_trigger_payload.get('key', 'default')
        
        # Initialize your flow state here
        pass

    # Add more flow steps using @listen() decorator
    # Example:
    # @listen(initialize)
    # def process_data(self):
    #     """Process data using a crew."""
    #     print("Processing data...")
    #     
    #     # Instantiate and run your crew
    #     # result = YourCrew().crew().kickoff(inputs={...})
    #     # self.state.result = result.raw
    #     pass


def kickoff():
    """
    Standard entry point for running the flow.
    Usage: crewai run
    """
    flow = BrieflerFlow()
    flow.kickoff()


def plot():
    """
    Generate a visual plot of the flow structure.
    Usage: crewai plot
    """
    flow = BrieflerFlow()
    flow.plot()


def run_with_trigger():
    """
    Run the flow with external trigger payload.
    
    Usage:
        python src/briefler/main.py '{"key": "value"}'
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
    flow = BrieflerFlow()

    try:
        result = flow.kickoff({"crewai_trigger_payload": trigger_payload})
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the flow with trigger: {e}")


if __name__ == "__main__":
    kickoff()
