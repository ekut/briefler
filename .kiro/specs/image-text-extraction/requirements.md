# Requirements Document

## Introduction

This feature enables the Briefler system to extract text content from images embedded in HTML emails before analysis. Currently, the system only processes text directly available in HTML, missing valuable information contained in images. This enhancement will allow the AI analyzer to access complete email content including text from images, improving analysis quality and completeness.

## Glossary

- **Email Processor**: The component responsible for fetching and processing Gmail messages
- **Image Extractor**: The component that identifies and downloads images from email content
- **Vision Agent**: A CrewAI agent that uses Vision Tool to extract text from images via LLM
- **Vision Task**: A CrewAI task assigned to Vision Agent for processing images
- **Vision Tool**: CrewAI's built-in tool for image analysis using LLM vision capabilities
- **Content Aggregator**: The component that combines extracted text with original email content
- **Analysis Pipeline**: The complete workflow from email retrieval to final analysis output

## Requirements

### Requirement 1

**User Story:** As a user analyzing emails, I want text from embedded images to be extracted and included in the analysis, so that I receive complete insights from all email content.

#### Acceptance Criteria

1. WHEN the Email Processor retrieves an unread email with embedded images, THE Image Extractor SHALL identify all image references in the HTML content
2. WHEN an image is identified in email content, THE Image Extractor SHALL download the image data from Gmail API
3. WHEN an image is downloaded, THE Vision Agent SHALL execute the Vision Task with the image
4. WHEN the Vision Task executes, THE Vision Tool SHALL extract text content from the image using LLM vision capabilities
5. WHEN text extraction completes, THE Content Aggregator SHALL combine extracted text with original email text
6. WHEN all content is aggregated, THE Analysis Pipeline SHALL pass the complete content to the AI analyzer

### Requirement 2

**User Story:** As a system administrator, I want the image processing to handle various image formats and sizes, so that the system works reliably with different email sources.

#### Acceptance Criteria

1. THE Image Extractor SHALL support JPEG, PNG, GIF, and WebP image formats
2. WHEN an image exceeds 10 MB in size, THE Image Extractor SHALL skip processing and log a warning
3. IF an image download fails, THEN THE Email Processor SHALL continue processing without blocking the analysis
4. WHEN multiple images exist in one email, THE Vision Agent SHALL process all images sequentially through separate Vision Task executions
5. THE Vision Tool SHALL handle images with resolution between 72 DPI and 600 DPI

### Requirement 3

**User Story:** As a user, I want only text to be extracted from images without descriptions of visual elements, so that the analysis focuses on written content.

#### Acceptance Criteria

1. THE Vision Agent SHALL be instructed to extract only text characters from images
2. THE Vision Agent SHALL NOT generate descriptions of people, objects, or composition
3. WHEN no text is detected in an image, THE Vision Task SHALL return an empty string
4. THE Content Aggregator SHALL label extracted text with source image identifier
5. THE Vision Agent SHALL use a prompt that explicitly requests text extraction only without visual descriptions

### Requirement 4

**User Story:** As a developer, I want the system to use efficient vision processing, so that processing time remains acceptable for users.

#### Acceptance Criteria

1. THE Vision Agent SHALL complete text extraction from a single image within 10 seconds
2. WHEN processing multiple images, THE Email Processor SHALL limit total vision processing time to 60 seconds per email
3. IF vision processing exceeds time limits, THEN THE Email Processor SHALL proceed with partial results
4. THE Vision Tool SHALL use the configured LLM provider with vision capabilities
5. THE Email Processor SHALL cache vision results for 24 hours to avoid reprocessing identical images

### Requirement 5

**User Story:** As a system administrator, I want proper error handling and logging for image processing, so that I can troubleshoot issues effectively.

#### Acceptance Criteria

1. WHEN an image processing error occurs, THE Email Processor SHALL log the error with email ID and image reference
2. IF the Vision Agent fails to process an image, THEN THE Email Processor SHALL continue with text-only analysis
3. THE Email Processor SHALL track metrics for images processed, text extracted, and errors encountered
4. WHEN the Vision Task fails for an image, THE Email Processor SHALL retry once before skipping
5. THE Email Processor SHALL include image processing status in the analysis metadata

### Requirement 6

**User Story:** As a user, I want the extracted text to be properly formatted and integrated, so that the analysis reads naturally.

#### Acceptance Criteria

1. THE Content Aggregator SHALL preserve line breaks and paragraph structure from extracted text
2. WHEN multiple text blocks are extracted from one image, THE Content Aggregator SHALL maintain their spatial order
3. THE Content Aggregator SHALL insert extracted text after the corresponding image reference in email content
4. THE Content Aggregator SHALL prefix extracted text with a marker indicating image source
5. WHEN extracted text contains special characters, THE Content Aggregator SHALL encode them properly for analysis
