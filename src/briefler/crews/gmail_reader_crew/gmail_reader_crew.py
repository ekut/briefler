from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from briefler.tools.gmail_reader_tool import GmailReaderTool


@CrewBase
class GmailReaderCrew:
    """Gmail Reader Crew for analyzing unread emails"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def email_analyst(self) -> Agent:
        gmail_tool = GmailReaderTool()
        return Agent(
            config=self.agents_config["email_analyst"],  # type: ignore[index]
            tools=[gmail_tool],
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
        """Creates the Gmail Reader Crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
