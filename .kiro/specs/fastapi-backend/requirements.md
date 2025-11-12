# Requirements Document

## Introduction

This document defines the requirements for adding a FastAPI-based REST API backend to the Briefler application. The API Server will expose the Gmail analysis CrewAI Flow functionality via HTTP endpoints, enabling programmatic access and future frontend integration. This specification focuses solely on the backend API layer and does not include frontend implementation.

## Glossary

- **Briefler Application**: The existing Python-based CrewAI application that analyzes Gmail messages
- **API Server**: A FastAPI-based REST API backend that exposes Briefler functionality via HTTP endpoints
- **Gmail Read Flow**: The CrewAI Flow that orchestrates email fetching and analysis
- **Analysis Result**: The structured output containing email summaries, insights, and action items
- **Flow State**: The Pydantic-based state object that tracks Flow execution progress and results
- **FastAPI**: Modern Python web framework for building APIs with automatic OpenAPI documentation and async support
- **SSE**: Server-Sent Events, a standard for server-to-client streaming over HTTP
- **Uvicorn**: ASGI server for running FastAPI applications

## Requirements

### Requirement 1

**User Story:** As a developer, I want a REST API that exposes Briefler functionality, so that clients can interact with the CrewAI Flow programmatically via HTTP

#### Acceptance Criteria

1. THE API Server SHALL expose an HTTP endpoint at `/api/flows/gmail-read` that accepts POST requests
2. THE API Server SHALL accept JSON request bodies containing `sender_emails`, `language`, and `days` parameters
3. WHEN the API Server receives a valid request, THE API Server SHALL initialize and execute the Gmail Read Flow
4. THE API Server SHALL return HTTP status code 200 with the Analysis Result in JSON format upon successful completion
5. IF the Gmail Read Flow raises an exception, THEN THE API Server SHALL return HTTP status code 500 with an error message in JSON format

### Requirement 2

**User Story:** As a developer, I want the API Server to validate input parameters, so that invalid requests are rejected before Flow execution

#### Acceptance Criteria

1. THE API Server SHALL validate that `sender_emails` is a non-empty list of valid email addresses
2. THE API Server SHALL validate that `language` is a valid ISO 639-1 language code
3. THE API Server SHALL validate that `days` is a positive integer between 1 and 365
4. WHEN the API Server receives invalid parameters, THE API Server SHALL return HTTP status code 400 with validation error details
5. THE API Server SHALL sanitize all input parameters to prevent injection attacks

### Requirement 3

**User Story:** As a developer, I want the API to support real-time progress updates during analysis, so that clients can display status information to users

#### Acceptance Criteria

1. THE API Server SHALL support Server-Sent Events (SSE) for streaming progress updates
2. WHILE the Gmail Read Flow is executing, THE API Server SHALL emit progress events with status messages
3. THE API Server SHALL expose an SSE endpoint at `/api/flows/gmail-read/stream` that accepts query parameters
4. THE API Server SHALL emit events with type `progress`, `complete`, or `error`
5. WHEN the Flow completes, THE API Server SHALL emit a final event with the complete Analysis Result

### Requirement 4

**User Story:** As a developer, I want the API Server to be accessible without authentication during local development, so that I can iterate quickly without managing credentials

#### Acceptance Criteria

1. THE API Server SHALL allow unauthenticated access to all endpoints when running in development mode
2. THE API Server SHALL log all API requests with timestamp and endpoint path for debugging purposes
3. THE API Server SHALL include CORS headers to allow requests from localhost origins
4. THE API Server SHALL provide clear logging output to the console for request/response debugging
5. WHERE the API Server is configured for production mode, THE API Server SHALL require authentication for all endpoints except health checks

### Requirement 5

**User Story:** As a developer, I want the API Server code organized in a dedicated directory under `src/`, so that it is logically separated from the existing CrewAI application code while maintaining consistent project structure

#### Acceptance Criteria

1. THE API Server SHALL be located in `src/api/` directory within the repository
2. THE API Server SHALL be a standalone FastAPI application that can be run independently via `uvicorn api.main:app`
3. THE API Server SHALL import and use the existing `GmailReadFlow` from `briefler.flows.gmail_read_flow`
4. THE API Server SHALL support Cross-Origin Resource Sharing (CORS) for requests from localhost during development
5. THE API Server SHALL be configurable via environment variables for API host, port, and CORS origins

### Requirement 6

**User Story:** As a developer, I want the API to persist and retrieve analysis history, so that clients can access previous analysis results

#### Acceptance Criteria

1. THE API Server SHALL persist Analysis Results to JSON file storage with unique identifiers
2. THE API Server SHALL expose an HTTP endpoint at `/api/history` that returns a list of past analyses with pagination
3. THE API Server SHALL expose an HTTP endpoint at `/api/history/{analysis_id}` that returns a specific analysis by ID
4. THE API Server SHALL store analysis metadata including timestamp, parameters, and execution time
5. THE API Server SHALL limit history retention to the most recent 100 analyses to manage storage

### Requirement 7

**User Story:** As a developer, I want health check endpoints for monitoring, so that I can verify the API Server is running and ready to accept requests

#### Acceptance Criteria

1. THE API Server SHALL expose an HTTP endpoint at `/health` that returns server status
2. THE API Server SHALL expose an HTTP endpoint at `/ready` that checks dependencies availability
3. THE `/health` endpoint SHALL return HTTP status code 200 with a JSON response containing status and timestamp
4. THE `/ready` endpoint SHALL verify Gmail credentials and environment variables are configured
5. WHEN dependencies are not available, THE `/ready` endpoint SHALL return HTTP status code 503 with details
