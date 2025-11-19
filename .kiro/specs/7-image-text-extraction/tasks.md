# Implementation Plan

- [x] 1. Create Image Extractor module
  - Create `src/briefler/tools/image_extractor.py` module for HTML parsing and URL extraction
  - Implement `ImageReference` Pydantic model with `message_id`, `image_index`, and `external_url` fields
  - Implement `extract_images_from_html()` method to parse HTML and find <img> tags with external URLs
  - Implement `validate_external_url()` method to validate HTTPS URLs and optional domain whitelist
  - Implement `get_domain_from_url()` helper method for domain extraction
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3_

- [x] 2. Extend GmailReaderTool with image extraction
  - Modify `_extract_message_data()` to call Image Extractor and collect image URLs
  - Add `image_urls` field to message data dictionary (list of external HTTPS URLs)
  - Modify `_format_output()` to include image URLs in formatted output with IMAGES_FOR_PROCESSING section
  - Add feature flag check using `IMAGE_PROCESSING_ENABLED` environment variable
  - _Requirements: 1.1, 1.2, 6.4, 4.5_

- [x] 3. Add Vision Agent to GmailReaderCrew
  - Add `image_text_extractor` agent configuration to `config/agents.yaml` with role, goal, and backstory
  - Implement `image_text_extractor()` agent method in `gmail_reader_crew.py` with VisionTool
  - Import VisionTool from `crewai_tools`
  - _Requirements: 1.3, 1.4, 3.1, 3.2_

- [x] 4. Add Vision Task to GmailReaderCrew
  - Add `extract_text_from_images` task configuration to `config/tasks.yaml`
  - Task description must instruct agent to process EACH image separately using VisionTool
  - Task description must emphasize extracting ONLY text content (no visual descriptions)
  - Expected output format: `[Image N: <url>]\n<extracted_text>\n\n` for each image
  - Implement `extract_text_from_images()` task method in `gmail_reader_crew.py`
  - _Requirements: 1.3, 1.4, 3.1, 3.2, 6.1, 6.2, 6.3_

- [x] 5. Update task execution order in GmailReaderCrew
  - Modify `crew()` method to conditionally include Vision Task based on image presence
  - Configure task context to pass Vision Task output to Cleanup Task using `context` parameter
  - Ensure sequential execution: Vision Task (if images) → Cleanup Task → Analysis Task
  - Update `cleanup_email_content` task in `tasks.yaml` to preserve extracted image texts
  - _Requirements: 1.5, 1.6, 6.5_

- [x] 6. Add configuration and feature flag
  - Add image processing environment variables to `.env.example`:
    - `IMAGE_PROCESSING_ENABLED` (default: false)
    - `IMAGE_MAX_SIZE_MB` (default: 10)
    - `IMAGE_PROCESSING_TIMEOUT` (default: 60)
    - `IMAGE_MAX_PER_EMAIL` (default: 5)
    - `IMAGE_ALLOWED_DOMAINS` (optional, comma-separated)
  - Implement feature flag check in GmailReaderTool `_extract_message_data()` method
  - Add configuration validation for optional IMAGE_ALLOWED_DOMAINS in Image Extractor
  - _Requirements: 4.5, 5.5_

- [x] 7. Add error handling and logging
  - Add try-except blocks in Image Extractor for HTML parsing failures
  - Add error handling in GmailReaderTool for image extraction failures (continue processing)
  - Implement logging in Image Extractor for images found, validated, and skipped
  - Add error logging with message ID and image URL context
  - Log warning when IMAGE_PROCESSING_ENABLED is false but images are present
  - _Requirements: 2.3, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Integration testing
  - Write test for Image Extractor with sample HTML containing external URLs
  - Write test for GmailReaderTool with feature flag enabled/disabled
  - Write test for Vision Agent with mock VisionTool responses
  - Test complete flow with emails containing external URL images
  - Test with emails without images
  - Test error handling when image extraction fails
  - _Requirements: All_

- [x] 9. Documentation and examples
  - Update README.md with image processing feature description
  - Add configuration examples for IMAGE_ALLOWED_DOMAINS to README.md
  - Document feature flag usage in README.md
  - Add example of email analysis with image text extraction to examples directory
  - _Requirements: N/A (documentation)_
