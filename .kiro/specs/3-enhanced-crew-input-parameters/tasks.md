# Implementation Plan

- [x] 1. Create GmailReadFlow module structure
  - Create directory `src/briefler/flows/gmail_read_flow/`
  - Create `__init__.py` file that exports GmailReadFlow and FlowState
  - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [x] 2. Implement FlowState model with validation
  - [x] 2.1 Create FlowState Pydantic model in `gmail_read_flow.py`
    - Define `sender_emails` field as List[str] with Field description
    - Define `language` field with default "en" and Field description
    - Define `days` field with default 7 and Field description
    - Define `result` field with default empty string
    - _Requirements: 1.1, 2.1, 3.1_
  
  - [x] 2.2 Implement sender_emails validator
    - Create `@field_validator('sender_emails')` method
    - Validate list is not empty
    - Validate each email format using regex pattern
    - Strip whitespace from each email
    - Raise ValueError with descriptive messages for invalid input
    - _Requirements: 1.2, 1.4, 5.1_
  
  - [x] 2.3 Implement language validator
    - Create `@field_validator('language')` method
    - Define set of valid ISO 639-1 language codes
    - Validate language code is in valid set
    - Convert to lowercase
    - Raise ValueError with descriptive message for invalid codes
    - _Requirements: 2.2, 2.3, 5.2_
  
  - [x] 2.4 Implement days validator
    - Create `@field_validator('days')` method
    - Validate days is an integer
    - Validate days is greater than zero
    - Raise ValueError with descriptive message for invalid values
    - _Requirements: 3.2, 3.3, 5.3_

- [x] 3. Implement GmailReadFlow class
  - [x] 3.1 Create GmailReadFlow class inheriting from Flow[FlowState]
    - Import Flow, listen, start from crewai.flow
    - Import GmailReaderCrew from briefler.crews.gmail_reader_crew
    - Define class with FlowState type parameter
    - _Requirements: 1.1, 4.1_
  
  - [x] 3.2 Implement initialize() method with @start() decorator
    - Accept crewai_trigger_payload parameter (optional dict)
    - Print initialization message
    - Handle backward compatibility for single sender_email parameter
    - Convert single sender_email to sender_emails list if needed
    - Extract sender_emails, language, and days from trigger payload
    - Update self.state with extracted values
    - Use default values when parameters not provided
    - _Requirements: 1.1, 2.1, 3.1, 4.2, 4.3_
  
  - [x] 3.3 Implement analyze_emails() method with @listen(initialize) decorator
    - Print analysis start message with sender count, language, and days
    - Prepare crew_inputs dictionary with sender_emails, language, and days
    - Instantiate GmailReaderCrew and call crew().kickoff(inputs=crew_inputs)
    - Store result.raw in self.state.result
    - _Requirements: 1.5, 2.4, 3.5_

- [x] 3.4 Export GmailReadFlow in __init__.py
  - Uncomment the import statement for GmailReadFlow in `src/briefler/flows/gmail_read_flow/__init__.py`
  - Add 'GmailReadFlow' to the __all__ list
  - _Requirements: 4.1_

- [x] 4. Update GmailReaderTool input schema and methods
  - [x] 4.1 Update GmailReaderToolInput schema
    - Change sender_email field to sender_emails as List[str]
    - Add days field with default value 7
    - Update Field descriptions for both fields
    - _Requirements: 1.1, 3.1_
  
  - [x] 4.2 Implement _calculate_date_threshold() method
    - Import datetime and timedelta from datetime module
    - Accept days parameter as integer
    - Calculate threshold_date as current date minus days
    - Format date as 'YYYY/MM/DD' string for Gmail API
    - Return formatted date string
    - _Requirements: 3.4, 3.5_
  
  - [x] 4.3 Update _get_unread_messages() method signature
    - Change sender_email parameter to sender_emails (List[str])
    - Add days parameter with default value 7
    - Update docstring to reflect new parameters
    - _Requirements: 1.3, 3.5_
  
  - [x] 4.4 Update query construction in _get_unread_messages()
    - Call _calculate_date_threshold(days) to get date string
    - Construct sender query using OR operator for multiple senders
    - Format: "(from:email1 OR from:email2)"
    - Combine with date filter: "is:unread (sender_query) after:date"
    - Update logger.info message to include sender count and days
    - _Requirements: 1.3, 3.5_
  
  - [x] 4.5 Update _format_output() method signature
    - Change sender_email parameter to sender_emails (List[str])
    - Add days parameter
    - Update docstring to reflect new parameters
    - _Requirements: 1.5_
  
  - [x] 4.6 Update output formatting in _format_output()
    - Join sender_emails with ", " for display
    - Update "No unread messages" message to include all senders and days
    - Update header message to show all senders and date range
    - Format: "Found X messages from sender1, sender2 in the last Y days:"
    - _Requirements: 1.5_
  
  - [x] 4.7 Update _run() method signature and calls
    - Change sender_email parameter to sender_emails (List[str])
    - Add days parameter with default value 7
    - Update validation to check sender_emails list is not empty
    - Update email format validation to iterate over sender_emails list
    - Update call to _get_unread_messages with new parameters
    - Update call to _format_output with new parameters
    - Update all logger messages to reflect multiple senders
    - Update error messages to be more descriptive
    - _Requirements: 1.1, 1.2, 1.4, 3.1, 3.3, 5.1, 5.3, 5.4, 5.5_

- [x] 5. Update crew configuration files
  - [x] 5.1 Update agents.yaml
    - Modify email_analyst goal to include language parameter placeholder
    - Update backstory to mention multilingual capabilities
    - Add instruction to always respond in specified language
    - Replace {sender_email} with reference to multiple senders
    - Add {language} placeholder for language parameter
    - _Requirements: 2.4, 2.5_
  
  - [x] 5.2 Update tasks.yaml
    - Update analyze_emails description to include language and days parameters
    - Add {language} and {days} placeholders
    - Add explicit instruction to write summary in specified language
    - Update expected_output to emphasize language requirement
    - Add note that entire output must be in specified language
    - _Requirements: 2.4, 2.5_

- [x] 6. Update main.py entry point
  - [x] 6.1 Replace imports and flow references
    - Remove old BrieflerFlow class and FlowState definition
    - Import GmailReadFlow from briefler.flows.gmail_read_flow
    - _Requirements: 4.1_
  
  - [x] 6.2 Update kickoff() function
    - Instantiate GmailReadFlow instead of BrieflerFlow
    - Call flow.kickoff()
    - _Requirements: 4.1_
  
  - [x] 6.3 Update plot() function
    - Instantiate GmailReadFlow instead of BrieflerFlow
    - Call flow.plot()
    - _Requirements: 4.1_
  
  - [x] 6.4 Update run_with_trigger() function
    - Instantiate GmailReadFlow instead of BrieflerFlow
    - Update docstring example to show new parameter format
    - Keep existing JSON parsing and error handling logic
    - _Requirements: 4.1, 4.2_

- [x] 7. Update example files
  - [x] 7.1 Update examples/gmail_crew_example.py
    - Import GmailReadFlow from briefler.flows.gmail_read_flow
    - Update example to use sender_emails list instead of sender_email
    - Add example with language parameter (e.g., "ru")
    - Add example with days parameter (e.g., 14)
    - Show example with multiple senders
    - Update comments to explain new parameters
    - _Requirements: 4.4_
  
  - [x] 7.2 Update examples/README.md
    - Document new input parameters (sender_emails, language, days)
    - Provide examples with different parameter combinations
    - Explain default values
    - Show backward compatibility example with single sender_email
    - Include example with multiple senders and custom language
    - _Requirements: 4.4_

- [x] 8. Update documentation
  - [x] 8.1 Update README.md
    - Add section on enhanced input parameters
    - Document sender_emails, language, and days parameters
    - Provide usage examples with new parameters
    - Explain default values and backward compatibility
    - Show example with multiple senders
    - Show example with different languages
    - Show example with custom days value
    - _Requirements: 4.4_
  
  - [x] 8.2 Update steering files if needed
    - Update structure.md to reflect new flow directory structure
    - Document GmailReadFlow location and purpose
    - Update any references to main.py structure
    - _Requirements: 4.4_
