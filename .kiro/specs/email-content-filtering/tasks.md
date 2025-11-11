# Implementation Plan

- [x] 1. Update agent configuration in YAML
  - Modify `src/briefler/crews/gmail_reader_crew/config/agents.yaml`
  - Update `email_analyst` agent backstory to reflect dual responsibility (content cleanup + analysis)
  - _Requirements: 1.1, 2.1_

- [ ] 2. Create Content Cleanup Task configuration
  - [x] 2.1 Add `cleanup_email_content` task definition to `src/briefler/crews/gmail_reader_crew/config/tasks.yaml`
    - Define task description with header boilerplate patterns
    - Define task description with footer boilerplate patterns
    - Include preservation rules for message body
    - Specify expected output format (cleaned emails with subject, sender, timestamp, body)
    - Assign to `email_analyst` agent
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3. Modify Summary Task configuration
  - [x] 3.1 Update `analyze_emails` task in `src/briefler/crews/gmail_reader_crew/config/tasks.yaml`
    - Update description to clarify it works with pre-cleaned content
    - Add `context: [cleanup_email_content]` to receive cleaned content from cleanup task
    - Remove instructions about handling footers (already done in cleanup task)
    - _Requirements: 1.3, 1.4, 4.6, 5.1, 5.2, 5.3_

- [ ] 4. Add cleanup task method to crew implementation
  - [x] 4.1 Add `cleanup_email_content()` method to `src/briefler/crews/gmail_reader_crew/gmail_reader_crew.py`
    - Use `@task` decorator
    - Load configuration from `tasks_config["cleanup_email_content"]`
    - Return Task instance
    - _Requirements: 5.4_

- [ ] 5. Verify task execution order
  - [x] 5.1 Confirm crew executes tasks sequentially
    - Verify `Process.sequential` is set in crew configuration
    - Ensure cleanup task is defined before analyze task in task list
    - _Requirements: 5.4_

- [ ] 6. Test the implementation
  - [x] 6.1 Test with email containing footer boilerplate
    - Run crew with sample email that has typical footer (contact info, legal text, unsubscribe)
    - Verify summary excludes footer information
    - _Requirements: 1.2, 2.2, 2.3, 2.4, 2.5_

  - [x] 6.2 Test with email containing header boilerplate
    - Run crew with sample email that has automated notice header
    - Verify summary excludes automated notice but includes full message body
    - _Requirements: 2.1, 4.1_

  - [x] 6.3 Test message body preservation
    - Run crew with email containing promotional offer in message body
    - Verify summary includes the promotional offer
    - _Requirements: 2.6, 4.1_

  - [x] 6.4 Test with email containing both header and footer boilerplate
    - Run crew with email that has boilerplate in both locations
    - Verify both are removed while message body is preserved
    - _Requirements: 1.2, 2.1, 2.7, 4.1_

  - [x] 6.5 Test multilingual support
    - Run crew with email containing non-English boilerplate
    - Verify boilerplate is removed and summary is in requested language
    - _Requirements: 1.2, 2.7_

  - [x] 6.6 Verify task context chain
    - Check that summary task receives cleaned content from cleanup task
    - Confirm no direct access to original uncleaned content
    - _Requirements: 5.1, 5.2, 5.3_
