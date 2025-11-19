# Implementation Plan

- [x] 1. Create task output models module
  - Create `src/briefler/models/__init__.py` file
  - Create `src/briefler/models/task_outputs.py` with all Pydantic models
  - Define TokenUsage model with total_tokens, prompt_tokens, completion_tokens fields
  - Define CleanedEmail model with subject, sender, timestamp, body, image_urls fields
  - Define CleanupTaskOutput model with emails list, total_count, and optional token_usage
  - Define ExtractedImageText model with image_url, extracted_text, has_text fields
  - Define VisionTaskOutput model with extracted_texts list, total_images_processed, images_with_text, and optional token_usage
  - Define EmailSummary model with subject, sender, timestamp, key_points, action_items, has_deadline fields
  - Define AnalysisTaskOutput model with total_count, email_summaries, action_items, priority_assessment, summary_text, and optional token_usage
  - Add Field descriptions and validation rules for all model fields
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 7.1_

- [x] 2. Update task configurations with output_pydantic
  - [x] 2.1 Import task output models in gmail_reader_crew.py
    - Add imports for CleanupTaskOutput, VisionTaskOutput, AnalysisTaskOutput from briefler.models.task_outputs
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 2.2 Configure cleanup_email_content task with output_pydantic
    - Add output_pydantic=CleanupTaskOutput parameter to cleanup_email_content task
    - Update task description in tasks.yaml to include JSON output format instructions
    - Add example JSON structure to expected_output field
    - _Requirements: 3.1, 3.4, 3.5_
  
  - [x] 2.3 Configure extract_text_from_images task with output_pydantic
    - Add output_pydantic=VisionTaskOutput parameter to extract_text_from_images task
    - Update task description in tasks.yaml to include JSON output format instructions
    - Add example JSON structure to expected_output field
    - _Requirements: 3.2, 3.4, 3.5_
  
  - [x] 2.4 Configure analyze_emails task with output_pydantic
    - Add output_pydantic=AnalysisTaskOutput parameter to analyze_emails task
    - Update task description in tasks.yaml to include JSON output format instructions
    - Add example JSON structure to expected_output field
    - _Requirements: 3.3, 3.4, 3.5_

- [ ] 3. Update Flow to handle structured outputs
  - [x] 3.1 Update FlowState model
    - Add structured_result field with Optional[AnalysisTaskOutput] type to FlowState
    - Add total_token_usage field with Optional[TokenUsage] type to FlowState
    - Import AnalysisTaskOutput and TokenUsage from briefler.models.task_outputs
    - _Requirements: 4.3, 7.3_
  
  - [x] 3.2 Update analyze_emails method to extract structured result
    - Add try-except block to extract result.pydantic after crew kickoff
    - Store result.pydantic in self.state.structured_result if available
    - Add fallback to parse result.json_dict if pydantic not available
    - Maintain backward compatibility by keeping result.raw storage
    - Add logging for successful extraction and fallback scenarios
    - _Requirements: 4.1, 4.2, 4.4, 4.5_
  
  - [x] 3.3 Implement token usage aggregation
    - Create _aggregate_token_usage method that accepts crew_result parameter
    - Extract token usage from crew.usage_metrics after kickoff
    - Create TokenUsage instance from usage_metrics dictionary
    - Store TokenUsage in self.state.total_token_usage
    - Add logging for token usage with prompt and completion breakdown
    - Call _aggregate_token_usage from analyze_emails after result extraction
    - _Requirements: 7.2, 7.3, 7.5_

- [ ] 4. Update API response models and services
  - [x] 4.1 Update GmailAnalysisResponse model
    - Add structured_result field with Optional[dict] type to GmailAnalysisResponse
    - Add token_usage field with Optional[dict] type to GmailAnalysisResponse
    - Update field descriptions to indicate backward compatibility for result field
    - _Requirements: 5.1, 5.3, 7.4_
  
  - [x] 4.2 Update FlowService to include structured data
    - Update execute_gmail_analysis method to serialize flow.state.structured_result using model_dump()
    - Add structured_result to response_data dictionary if available
    - Update execute_gmail_analysis method to serialize flow.state.total_token_usage using model_dump()
    - Add token_usage to response_data dictionary if available
    - Add try-except blocks for serialization with warning logs on failure
    - Ensure backward compatibility by always including result field
    - _Requirements: 5.1, 5.2, 5.4, 5.5, 7.4_

- [ ] 5. Implement error handling and validation
  - [x] 5.1 Add validation error handling in Flow
    - Wrap structured result extraction in try-except for ValidationError
    - Log validation errors with field details without exposing sensitive data
    - Implement fallback to raw result on validation errors
    - Ensure flow continues execution after validation errors
    - Add warning log for repeated validation failures
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [x] 5.2 Add serialization error handling in API service
    - Wrap model_dump() calls in try-except blocks
    - Log serialization errors with context
    - Continue response generation without structured_result on serialization failure
    - Ensure API never fails due to structured output issues
    - _Requirements: 5.5, 6.1, 6.2_

- [ ] 6. Update tests for structured outputs
  - [x] 6.1 Create unit tests for task output models
    - Write tests for TokenUsage model validation
    - Write tests for CleanedEmail model validation
    - Write tests for CleanupTaskOutput model validation
    - Write tests for ExtractedImageText model validation
    - Write tests for VisionTaskOutput model validation
    - Write tests for EmailSummary model validation
    - Write tests for AnalysisTaskOutput model validation
    - Test field validation rules and default values
    - _Requirements: 8.1, 8.3_
  
  - [x] 6.2 Create integration tests for crew structured outputs
    - Write test that verifies crew returns structured output
    - Write test that verifies result.pydantic is AnalysisTaskOutput instance
    - Write test that verifies structured fields are accessible
    - Write test that verifies dictionary-style access to result fields
    - Write test that verifies backward compatibility with result.raw
    - _Requirements: 8.1, 8.2, 8.4_
  
  - [x] 6.3 Create integration tests for flow structured outputs
    - Write test that verifies flow extracts structured result from crew
    - Write test that verifies flow.state.structured_result is populated
    - Write test that verifies flow.state.total_token_usage is populated
    - Write test that verifies token usage aggregation from crew.usage_metrics
    - Write test that verifies fallback to raw result on validation errors
    - _Requirements: 8.1, 8.2, 8.4, 8.6_
  
  - [x] 6.4 Create API tests for structured responses
    - Write test that verifies API response includes structured_result field
    - Write test that verifies API response includes token_usage field
    - Write test that verifies structured_result has expected fields (total_count, email_summaries, action_items)
    - Write test that verifies token_usage has expected fields (total_tokens, prompt_tokens, completion_tokens)
    - Write test that verifies backward compatibility with result field
    - Write test that verifies API handles missing structured_result gracefully
    - _Requirements: 8.1, 8.2, 8.4, 8.6_
  
  - [x] 6.5 Create error handling tests
    - Write test that verifies validation error handling in flow
    - Write test that verifies serialization error handling in API
    - Write test that verifies flow continues on validation errors
    - Write test that verifies API returns 200 even when structured output fails
    - _Requirements: 8.5_

- [x] 7. Update documentation
  - Update README.md with structured output examples
  - Add API documentation for structured_result and token_usage fields
  - Document TokenUsage model fields and their meanings
  - Document how to access structured data from API responses
  - Add examples of using structured data programmatically
  - _Requirements: All requirements for documentation_
