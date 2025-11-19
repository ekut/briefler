# Requirements Document

## Introduction

This specification defines the implementation of structured task outputs using CrewAI's `output_pydantic` feature for the Briefler email analysis system. Currently, task outputs are unstructured strings that require manual parsing and are prone to inconsistencies. By implementing Pydantic models for task outputs, the system will enforce deterministic, type-safe, and validated data structures throughout the agent workflow, improving reliability and enabling programmatic access to task results.

## Glossary

- **System**: The Briefler email analysis application
- **Task**: A CrewAI Task object that defines work for an agent to complete
- **Agent**: A CrewAI Agent that executes tasks
- **Pydantic Model**: A Python class inheriting from `pydantic.BaseModel` that defines structured data with validation
- **output_pydantic**: A CrewAI Task parameter that enforces structured output using a Pydantic model
- **CleanupTask**: The task responsible for removing boilerplate from email content
- **VisionTask**: The task responsible for extracting text from images in emails
- **AnalysisTask**: The task responsible for generating the final email summary
- **TaskOutput**: The result object returned by a CrewAI task execution
- **FlowState**: The Pydantic model representing state in GmailReadFlow

## Requirements

### Requirement 1

**User Story:** As a developer, I want task outputs to be structured using Pydantic models, so that I can reliably access specific fields without parsing unstructured text

#### Acceptance Criteria

1. WHEN THE System executes CleanupTask, THE System SHALL return a Pydantic model containing a list of cleaned email objects with subject, sender, timestamp, body, and image URLs fields
2. WHEN THE System executes VisionTask, THE System SHALL return a Pydantic model containing a list of extracted text objects with image URL and extracted text fields
3. WHEN THE System executes AnalysisTask, THE System SHALL return a Pydantic model containing total count, email summaries list, action items list, and priority assessment fields
4. WHEN THE System receives a task result, THE System SHALL provide access to structured data via dictionary-style indexing and direct Pydantic model attribute access
5. WHEN THE System validates task output, THE System SHALL enforce field types and required fields according to the Pydantic model schema

### Requirement 2

**User Story:** As a developer, I want Pydantic models defined in a dedicated module, so that they can be reused across tasks, flows, and API responses

#### Acceptance Criteria

1. THE System SHALL define all task output Pydantic models in a module at `src/briefler/models/task_outputs.py`
2. THE System SHALL define models for CleanedEmail, CleanupTaskOutput, ExtractedImageText, VisionTaskOutput, EmailSummary, and AnalysisTaskOutput
3. THE System SHALL include Field descriptions and validation rules for all model fields
4. THE System SHALL use typing annotations for all fields including List, Optional, and datetime types
5. THE System SHALL export all models from the module for import by other components

### Requirement 3

**User Story:** As a developer, I want tasks configured with output_pydantic parameter, so that CrewAI enforces structured output during task execution

#### Acceptance Criteria

1. WHEN THE System creates CleanupTask, THE System SHALL assign CleanupTaskOutput to the output_pydantic parameter
2. WHEN THE System creates VisionTask, THE System SHALL assign VisionTaskOutput to the output_pydantic parameter
3. WHEN THE System creates AnalysisTask, THE System SHALL assign AnalysisTaskOutput to the output_pydantic parameter
4. THE System SHALL maintain backward compatibility by preserving existing task descriptions and expected_output fields
5. THE System SHALL configure tasks to return structured data without requiring changes to agent configurations

### Requirement 4

**User Story:** As a developer, I want the flow to access structured task results, so that I can extract specific data fields for API responses and further processing

#### Acceptance Criteria

1. WHEN THE System completes crew execution, THE System SHALL access the final task result via the pydantic attribute
2. WHEN THE System processes AnalysisTask output, THE System SHALL extract structured fields including total_count, email_summaries, action_items, and priority_assessment
3. THE System SHALL store structured data in FlowState for access by downstream components
4. THE System SHALL maintain the existing result.raw field for backward compatibility
5. WHEN THE System encounters a task without output_pydantic, THE System SHALL handle the result as unstructured text without errors

### Requirement 5

**User Story:** As a developer, I want API responses to include structured task data, so that API consumers can programmatically access email analysis results

#### Acceptance Criteria

1. WHEN THE System returns an API response, THE System SHALL include structured fields from AnalysisTaskOutput in the response body
2. THE System SHALL serialize Pydantic models to JSON for API responses using model_dump or model_dump_json methods
3. THE System SHALL maintain backward compatibility by preserving the existing result field as markdown text
4. THE System SHALL add optional structured_result field to API responses containing the Pydantic model as JSON
5. WHEN THE System encounters serialization errors, THE System SHALL log the error and return the raw result without failing the request

### Requirement 6

**User Story:** As a developer, I want validation errors handled gracefully, so that the system provides clear feedback when task outputs don't match the expected schema

#### Acceptance Criteria

1. WHEN THE System receives invalid task output, THE System SHALL log the validation error with details about missing or incorrect fields
2. WHEN THE System encounters a Pydantic validation error, THE System SHALL fall back to using the raw task output
3. THE System SHALL include error details in logs without exposing sensitive email content
4. THE System SHALL continue flow execution after validation errors without terminating the entire workflow
5. WHEN THE System detects repeated validation failures, THE System SHALL log a warning indicating potential schema mismatch

### Requirement 7

**User Story:** As a developer, I want token usage tracked from crew execution, so that I can monitor LLM API costs and optimize performance

#### Acceptance Criteria

1. THE System SHALL define a TokenUsage Pydantic model with total_tokens, prompt_tokens, and completion_tokens fields matching CrewAI's usage_metrics structure
2. WHEN THE System completes crew execution, THE System SHALL extract token usage from crew.usage_metrics
3. THE System SHALL store aggregated token usage in FlowState after crew kickoff completes
4. THE System SHALL include token usage in API responses for cost monitoring
5. THE System SHALL log token usage statistics with prompt and completion token breakdown for observability

### Requirement 8

**User Story:** As a developer, I want existing tests updated to validate structured outputs, so that I can verify the implementation works correctly

#### Acceptance Criteria

1. WHEN THE System runs tests for GmailReaderCrew, THE System SHALL verify that task outputs conform to their respective Pydantic models
2. THE System SHALL include tests that access structured data via dictionary-style indexing and pydantic attribute access
3. THE System SHALL include tests that validate required fields are present in task outputs
4. THE System SHALL include tests that verify backward compatibility with raw output access
5. THE System SHALL include tests that validate error handling for malformed task outputs
6. THE System SHALL include tests that verify token usage tracking and aggregation
