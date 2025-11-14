from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import VisionTool

from briefler.tools.gmail_reader_tool import GmailReaderTool


@CrewBase
class GmailReaderCrew:
    """Gmail Reader Crew for analyzing unread emails"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def image_text_extractor(self) -> Agent:
        """Agent for extracting text from images in emails"""
        vision_tool = VisionTool()
        return Agent(
            config=self.agents_config["image_text_extractor"],  # type: ignore[index]
            tools=[vision_tool],
        )

    @agent
    def email_analyst(self) -> Agent:
        gmail_tool = GmailReaderTool()
        return Agent(
            config=self.agents_config["email_analyst"],  # type: ignore[index]
            tools=[gmail_tool],
        )

    @task
    def extract_text_from_images(self) -> Task:
        """Task to extract text from images in emails"""
        return Task(
            config=self.tasks_config["extract_text_from_images"],  # type: ignore[index]
        )

    @task
    def cleanup_email_content(self) -> Task:
        """Task to clean email content by removing boilerplate"""
        return Task(
            config=self.tasks_config["cleanup_email_content"],  # type: ignore[index]
        )

    @task
    def analyze_emails(self) -> Task:
        """Task to analyze cleaned email content and generate summary"""
        return Task(
            config=self.tasks_config["analyze_emails"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Gmail Reader Crew with conditional image processing.
        
        Task execution order:
        - If images are present: Cleanup Task → Vision Task → Analysis Task
        - If no images: Cleanup Task → Analysis Task
        
        The Cleanup Task output (with IMAGES_FOR_PROCESSING section) is passed to Vision Task.
        Both Cleanup and Vision outputs are passed to Analysis Task.
        """
        # Get all tasks
        vision_task = self.extract_text_from_images()
        cleanup_task = self.cleanup_email_content()
        analysis_task = self.analyze_emails()
        
        # Check if image processing is enabled
        import os
        image_processing_enabled = os.getenv('IMAGE_PROCESSING_ENABLED', 'false').lower() == 'true'
        
        # Configure task list and context based on image processing
        if image_processing_enabled:
            # Vision Task receives Cleanup Task output (which contains IMAGES_FOR_PROCESSING)
            vision_task.context = [cleanup_task]
            # Analysis Task receives both Cleanup and Vision outputs
            analysis_task.context = [cleanup_task, vision_task]
            tasks = [cleanup_task, vision_task, analysis_task]
        else:
            # Skip Vision Task if image processing is disabled
            # Analysis Task only receives Cleanup output
            analysis_task.context = [cleanup_task]
            tasks = [cleanup_task, analysis_task]
        
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=tasks,  # Conditionally includes Vision Task
            process=Process.sequential,
            verbose=True,
        )
