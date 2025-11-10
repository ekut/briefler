# Requirements Document

## Introduction

This document specifies the requirements for converting the existing gmail_reader_example.py script into a standard CrewAI project structure. The conversion will transform the procedural example code into a modular, configuration-driven crew using CrewAI's @CrewBase decorator pattern with YAML configuration files for agents and tasks.

## Glossary

- **GmailReaderCrew**: The CrewAI crew class that will be created to replace the example script
- **Email Analyst Agent**: The CrewAI agent responsible for reading and analyzing Gmail messages
- **YAML Configuration**: Configuration files (agents.yaml and tasks.yaml) that define agent and task properties
- **CrewBase Decorator**: The @CrewBase class decorator that marks a class as a CrewAI crew
- **Agent Decorator**: The @agent method decorator that defines an agent factory method
- **Task Decorator**: The @task method decorator that defines a task factory method
- **Crew Decorator**: The @crew method decorator that defines the crew assembly method

## Requirements

### Requirement 1

**User Story:** As a developer, I want to organize the Gmail reader functionality into a standard CrewAI crew structure, so that it follows the same pattern as other crews in the project

#### Acceptance Criteria

1. THE GmailReaderCrew SHALL be created as a class decorated with @CrewBase in the file src/briefler/crews/gmail_reader_crew/gmail_reader_crew.py
2. THE GmailReaderCrew SHALL define agents_config pointing to "config/agents.yaml"
3. THE GmailReaderCrew SHALL define tasks_config pointing to "config/tasks.yaml"
4. THE GmailReaderCrew SHALL include a method decorated with @agent that returns the Email Analyst Agent
5. THE GmailReaderCrew SHALL include a method decorated with @task that returns the email analysis task

### Requirement 2

**User Story:** As a developer, I want agent configuration externalized to YAML files, so that I can easily modify agent properties without changing code

#### Acceptance Criteria

1. THE GmailReaderCrew SHALL create a config/agents.yaml file defining the email_analyst agent
2. THE agents.yaml file SHALL specify the role as "Email Analyst"
3. THE agents.yaml file SHALL specify a goal related to reading and analyzing unread emails
4. THE agents.yaml file SHALL specify a backstory describing the agent's expertise
5. THE agents.yaml file SHALL support a {sender_email} parameter for dynamic sender specification

### Requirement 3

**User Story:** As a developer, I want task configuration externalized to YAML files, so that I can easily modify task descriptions and expected outputs without changing code

#### Acceptance Criteria

1. THE GmailReaderCrew SHALL create a config/tasks.yaml file defining the analyze_emails task
2. THE tasks.yaml file SHALL specify a description that includes reading unread emails from a sender
3. THE tasks.yaml file SHALL specify an expected_output describing the summary format
4. THE tasks.yaml file SHALL reference the email_analyst agent
5. THE tasks.yaml file SHALL support a {sender_email} parameter for dynamic sender specification

### Requirement 4

**User Story:** As a developer, I want the GmailReaderTool properly integrated with the agent, so that the agent can access Gmail functionality

#### Acceptance Criteria

1. THE email_analyst agent method SHALL instantiate the GmailReaderTool
2. THE email_analyst agent method SHALL pass the GmailReaderTool instance to the Agent constructor via the tools parameter
3. THE GmailReaderTool SHALL be imported from mailbox_briefler.tools.gmail_reader_tool
4. THE agent configuration SHALL load from the agents.yaml file using config parameter
5. THE agent method SHALL return an Agent instance with the tool properly registered

### Requirement 5

**User Story:** As a developer, I want a crew method that assembles the complete crew, so that I can execute the Gmail reading workflow

#### Acceptance Criteria

1. THE GmailReaderCrew SHALL include a method decorated with @crew that returns a Crew instance
2. THE crew method SHALL use self.agents to automatically include all agents defined by @agent decorators
3. THE crew method SHALL use self.tasks to automatically include all tasks defined by @task decorators
4. THE crew method SHALL set process to Process.sequential
5. THE crew method SHALL set verbose to True

### Requirement 6

**User Story:** As a developer, I want the crew to be executable with dynamic parameters, so that I can specify different sender emails at runtime

#### Acceptance Criteria

1. THE GmailReaderCrew SHALL support kickoff with inputs parameter containing sender_email
2. THE sender_email parameter SHALL be interpolated into agent goal and backstory
3. THE sender_email parameter SHALL be interpolated into task description and expected_output
4. THE crew execution SHALL accept sender_email as a string value
5. THE crew SHALL execute successfully when provided with a valid sender_email parameter

### Requirement 7

**User Story:** As a developer, I want proper module initialization files, so that the crew can be imported from other parts of the application

#### Acceptance Criteria

1. THE GmailReaderCrew SHALL create an __init__.py file in src/briefler/crews/gmail_reader_crew/
2. THE __init__.py file SHALL export the GmailReaderCrew class
3. THE __init__.py file SHALL allow importing GmailReaderCrew using "from briefler.crews.gmail_reader_crew import GmailReaderCrew"
4. THE config directory SHALL contain an __init__.py file if required by the project structure
5. THE crew SHALL be importable without errors after installation

### Requirement 8

**User Story:** As a developer, I want a simple example script that demonstrates how to use the new crew structure, so that I can understand how to execute it

#### Acceptance Criteria

1. THE project SHALL create an example script at examples/gmail_crew_example.py
2. THE example script SHALL import GmailReaderCrew from the crews module
3. THE example script SHALL demonstrate instantiating the crew
4. THE example script SHALL demonstrate calling kickoff with sender_email parameter
5. THE example script SHALL display the crew execution results
