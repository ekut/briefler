from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from mailbox_briefler.tools.gmail_reader_tool import GmailReaderTool


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
    def analyze_emails(self) -> Task:
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
