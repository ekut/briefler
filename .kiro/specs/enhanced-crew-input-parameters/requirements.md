# Requirements Document

## Introduction

This feature extends the Gmail Reader Crew's input parameters to support multiple sender emails, configurable language for summaries, and time-based filtering of unread messages. The enhancement enables more flexible email analysis workflows by allowing users to process emails from multiple senders simultaneously, receive summaries in their preferred language, and control the time window for email retrieval.

## Glossary

- **Gmail Reader Crew**: The CrewAI-based system that reads and analyzes Gmail messages
- **FlowState**: The Pydantic model that defines state passed between flow steps in CrewAI
- **Sender Email**: An email address from which messages should be retrieved and analyzed
- **ISO Language Code**: A two-letter language code following ISO 639-1 standard (e.g., "en", "ru", "es")
- **Days Parameter**: The number of days in the past from which to retrieve unread messages
- **Summary**: The AI-generated analysis output of email content

## Requirements

### Requirement 1

**User Story:** As a user, I want to specify multiple sender email addresses, so that I can analyze emails from several important contacts in a single execution

#### Acceptance Criteria

1. THE Gmail Reader Crew SHALL accept a list of sender email addresses as input
2. WHEN no sender emails are provided, THE Gmail Reader Crew SHALL raise a validation error with a descriptive message
3. WHEN multiple sender emails are provided, THE Gmail Reader Crew SHALL retrieve unread messages from all specified senders
4. THE Gmail Reader Crew SHALL validate that each sender email follows valid email address format
5. THE Gmail Reader Crew SHALL process messages from all senders within a single crew execution

### Requirement 2

**User Story:** As a user, I want to specify the language for email summaries using ISO standard codes, so that I can receive analysis in my preferred language

#### Acceptance Criteria

1. THE Gmail Reader Crew SHALL accept a language parameter using ISO 639-1 two-letter codes
2. WHEN no language parameter is provided, THE Gmail Reader Crew SHALL default to "en" (English)
3. THE Gmail Reader Crew SHALL validate that the language parameter is a valid ISO 639-1 code
4. THE Gmail Reader Crew SHALL include the language parameter in the crew inputs dictionary provided to AI agents
5. THE Gmail Reader Crew SHALL generate all summaries and analysis outputs in the specified language

### Requirement 3

**User Story:** As a user, I want to specify how many days back to retrieve unread emails, so that I can control the time window for email analysis

#### Acceptance Criteria

1. THE Gmail Reader Crew SHALL accept a days parameter as a positive integer
2. WHEN no days parameter is provided, THE Gmail Reader Crew SHALL default to 7 days
3. THE Gmail Reader Crew SHALL validate that the days parameter is a positive integer greater than zero
4. WHEN retrieving messages, THE Gmail Reader Crew SHALL filter messages to only include those received within the specified number of days
5. THE Gmail Reader Crew SHALL calculate the date threshold based on the current date minus the specified number of days

### Requirement 4

**User Story:** As a developer, I want backward compatibility with existing code, so that current implementations continue to work without modification

#### Acceptance Criteria

1. WHERE existing code provides a single sender_email parameter, THE Gmail Reader Crew SHALL accept it as a single-item list
2. THE Gmail Reader Crew SHALL maintain the same output structure for crew results
3. THE Gmail Reader Crew SHALL preserve existing error handling behavior for authentication and API errors
4. THE Gmail Reader Crew SHALL maintain compatibility with existing example scripts
5. WHEN new parameters are not provided, THE Gmail Reader Crew SHALL use documented default values

### Requirement 5

**User Story:** As a user, I want clear error messages when input parameters are invalid, so that I can quickly correct configuration issues

#### Acceptance Criteria

1. WHEN an invalid email format is provided, THE Gmail Reader Crew SHALL raise a ValueError containing the specific invalid email address
2. WHEN an invalid language code is provided, THE Gmail Reader Crew SHALL raise a ValueError containing the invalid code and the text "Must be a valid ISO 639-1 code"
3. WHEN an invalid days parameter is provided, THE Gmail Reader Crew SHALL raise a ValueError containing the text "must be a positive integer greater than zero"
4. WHEN required parameters are missing, THE Gmail Reader Crew SHALL raise a ValueError containing all missing required parameter names
5. THE Gmail Reader Crew SHALL log all validation errors at ERROR level with the parameter name and invalid value
