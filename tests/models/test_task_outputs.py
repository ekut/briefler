"""Unit tests for task output Pydantic models.

Tests validation rules, default values, and field constraints for all
task output models used in the Gmail Reader Crew workflow.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.briefler.models.task_outputs import (
    TokenUsage,
    CleanedEmail,
    CleanupTaskOutput,
    ExtractedImageText,
    VisionTaskOutput,
    EmailSummary,
    AnalysisTaskOutput,
)


class TestTokenUsage:
    """Tests for TokenUsage model validation."""
    
    def test_token_usage_valid(self):
        """Test TokenUsage with valid data."""
        usage = TokenUsage(
            total_tokens=100,
            prompt_tokens=60,
            completion_tokens=40
        )
        assert usage.total_tokens == 100
        assert usage.prompt_tokens == 60
        assert usage.completion_tokens == 40
    
    def test_token_usage_defaults(self):
        """Test TokenUsage default values."""
        usage = TokenUsage()
        assert usage.total_tokens == 0
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
    
    def test_token_usage_negative_values_rejected(self):
        """Test that negative token values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TokenUsage(total_tokens=-10)
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_token_usage_partial_defaults(self):
        """Test TokenUsage with partial data uses defaults."""
        usage = TokenUsage(total_tokens=100)
        assert usage.total_tokens == 100
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0


class TestCleanedEmail:
    """Tests for CleanedEmail model validation."""
    
    def test_cleaned_email_valid(self):
        """Test CleanedEmail with valid data."""
        email = CleanedEmail(
            subject="Test Subject",
            sender="test@example.com",
            timestamp=datetime(2025, 11, 19, 10, 30, 0),
            body="Test email body content",
            image_urls=["https://example.com/image1.jpg", "https://example.com/image2.png"]
        )
        assert email.subject == "Test Subject"
        assert email.sender == "test@example.com"
        assert email.timestamp == datetime(2025, 11, 19, 10, 30, 0)
        assert email.body == "Test email body content"
        assert len(email.image_urls) == 2
    
    def test_cleaned_email_empty_image_urls_default(self):
        """Test CleanedEmail with no image_urls uses empty list default."""
        email = CleanedEmail(
            subject="Test",
            sender="test@example.com",
            timestamp=datetime.now(),
            body="Body"
        )
        assert email.image_urls == []
    
    def test_cleaned_email_empty_subject_rejected(self):
        """Test that empty subject is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CleanedEmail(
                subject="",
                sender="test@example.com",
                timestamp=datetime.now(),
                body="Body"
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_cleaned_email_empty_sender_rejected(self):
        """Test that empty sender is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CleanedEmail(
                subject="Test",
                sender="",
                timestamp=datetime.now(),
                body="Body"
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_cleaned_email_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CleanedEmail(subject="Test")
        errors = exc_info.value.errors()
        error_fields = {error['loc'][0] for error in errors}
        assert 'sender' in error_fields
        assert 'timestamp' in error_fields
        assert 'body' in error_fields


class TestCleanupTaskOutput:
    """Tests for CleanupTaskOutput model validation."""
    
    def test_cleanup_task_output_valid(self):
        """Test CleanupTaskOutput with valid data."""
        email = CleanedEmail(
            subject="Test",
            sender="test@example.com",
            timestamp=datetime.now(),
            body="Body"
        )
        output = CleanupTaskOutput(
            emails=[email],
            total_count=1,
            token_usage=TokenUsage(total_tokens=50)
        )
        assert len(output.emails) == 1
        assert output.total_count == 1
        assert output.token_usage.total_tokens == 50
    
    def test_cleanup_task_output_empty_emails(self):
        """Test CleanupTaskOutput with empty emails list."""
        output = CleanupTaskOutput(
            emails=[],
            total_count=0
        )
        assert output.emails == []
        assert output.total_count == 0
        assert output.token_usage is None
    
    def test_cleanup_task_output_negative_count_rejected(self):
        """Test that negative total_count is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CleanupTaskOutput(
                emails=[],
                total_count=-1
            )
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_cleanup_task_output_optional_token_usage(self):
        """Test that token_usage is optional."""
        output = CleanupTaskOutput(
            emails=[],
            total_count=0
        )
        assert output.token_usage is None


class TestExtractedImageText:
    """Tests for ExtractedImageText model validation."""
    
    def test_extracted_image_text_valid(self):
        """Test ExtractedImageText with valid data."""
        extracted = ExtractedImageText(
            image_url="https://example.com/image.jpg",
            extracted_text="Sample text from image",
            has_text=True
        )
        assert extracted.image_url == "https://example.com/image.jpg"
        assert extracted.extracted_text == "Sample text from image"
        assert extracted.has_text is True
    
    def test_extracted_image_text_no_text_found(self):
        """Test ExtractedImageText when no text is found."""
        extracted = ExtractedImageText(
            image_url="https://example.com/image.jpg",
            extracted_text="No text found",
            has_text=False
        )
        assert extracted.extracted_text == "No text found"
        assert extracted.has_text is False
    
    def test_extracted_image_text_empty_url_rejected(self):
        """Test that empty image_url is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExtractedImageText(
                image_url="",
                extracted_text="Text",
                has_text=True
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_extracted_image_text_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExtractedImageText(image_url="https://example.com/image.jpg")
        errors = exc_info.value.errors()
        error_fields = {error['loc'][0] for error in errors}
        assert 'extracted_text' in error_fields
        assert 'has_text' in error_fields


class TestVisionTaskOutput:
    """Tests for VisionTaskOutput model validation."""
    
    def test_vision_task_output_valid(self):
        """Test VisionTaskOutput with valid data."""
        extracted = ExtractedImageText(
            image_url="https://example.com/image.jpg",
            extracted_text="Text",
            has_text=True
        )
        output = VisionTaskOutput(
            extracted_texts=[extracted],
            total_images_processed=1,
            images_with_text=1,
            token_usage=TokenUsage(total_tokens=100)
        )
        assert len(output.extracted_texts) == 1
        assert output.total_images_processed == 1
        assert output.images_with_text == 1
        assert output.token_usage.total_tokens == 100
    
    def test_vision_task_output_empty_extracted_texts_default(self):
        """Test VisionTaskOutput with no extracted_texts uses empty list default."""
        output = VisionTaskOutput(
            total_images_processed=0,
            images_with_text=0
        )
        assert output.extracted_texts == []
        assert output.token_usage is None
    
    def test_vision_task_output_negative_counts_rejected(self):
        """Test that negative counts are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            VisionTaskOutput(
                total_images_processed=-1,
                images_with_text=0
            )
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_vision_task_output_multiple_extractions(self):
        """Test VisionTaskOutput with multiple extracted texts."""
        extractions = [
            ExtractedImageText(
                image_url=f"https://example.com/image{i}.jpg",
                extracted_text=f"Text {i}",
                has_text=True
            )
            for i in range(3)
        ]
        output = VisionTaskOutput(
            extracted_texts=extractions,
            total_images_processed=3,
            images_with_text=3
        )
        assert len(output.extracted_texts) == 3
        assert output.total_images_processed == 3


class TestEmailSummary:
    """Tests for EmailSummary model validation."""
    
    def test_email_summary_valid(self):
        """Test EmailSummary with valid data."""
        summary = EmailSummary(
            subject="Meeting Tomorrow",
            sender="boss@example.com",
            timestamp=datetime(2025, 11, 20, 9, 0, 0),
            key_points=["Discuss Q4 results", "Review budget"],
            action_items=["Prepare slides", "Send agenda"],
            has_deadline=True
        )
        assert summary.subject == "Meeting Tomorrow"
        assert summary.sender == "boss@example.com"
        assert len(summary.key_points) == 2
        assert len(summary.action_items) == 2
        assert summary.has_deadline is True
    
    def test_email_summary_defaults(self):
        """Test EmailSummary default values."""
        summary = EmailSummary(
            subject="Test",
            sender="test@example.com",
            timestamp=datetime.now()
        )
        assert summary.key_points == []
        assert summary.action_items == []
        assert summary.has_deadline is False
    
    def test_email_summary_empty_subject_rejected(self):
        """Test that empty subject is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EmailSummary(
                subject="",
                sender="test@example.com",
                timestamp=datetime.now()
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_email_summary_empty_sender_rejected(self):
        """Test that empty sender is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EmailSummary(
                subject="Test",
                sender="",
                timestamp=datetime.now()
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_email_summary_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EmailSummary(subject="Test")
        errors = exc_info.value.errors()
        error_fields = {error['loc'][0] for error in errors}
        assert 'sender' in error_fields
        assert 'timestamp' in error_fields


class TestAnalysisTaskOutput:
    """Tests for AnalysisTaskOutput model validation."""
    
    def test_analysis_task_output_valid(self):
        """Test AnalysisTaskOutput with valid data."""
        summary = EmailSummary(
            subject="Test",
            sender="test@example.com",
            timestamp=datetime.now()
        )
        output = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[summary],
            action_items=["Action 1", "Action 2"],
            priority_assessment="High",
            summary_text="# Email Summary\n\nDetailed summary here",
            token_usage=TokenUsage(total_tokens=200)
        )
        assert output.total_count == 1
        assert len(output.email_summaries) == 1
        assert len(output.action_items) == 2
        assert output.priority_assessment == "High"
        assert "Email Summary" in output.summary_text
        assert output.token_usage.total_tokens == 200
    
    def test_analysis_task_output_empty_lists_default(self):
        """Test AnalysisTaskOutput with default empty lists."""
        output = AnalysisTaskOutput(
            total_count=0,
            email_summaries=[],
            priority_assessment="Low",
            summary_text="No emails to analyze"
        )
        assert output.action_items == []
        assert output.token_usage is None
    
    def test_analysis_task_output_negative_count_rejected(self):
        """Test that negative total_count is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisTaskOutput(
                total_count=-1,
                email_summaries=[],
                priority_assessment="Low",
                summary_text="Summary"
            )
        assert "greater than or equal to 0" in str(exc_info.value)
    
    def test_analysis_task_output_empty_priority_rejected(self):
        """Test that empty priority_assessment is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisTaskOutput(
                total_count=0,
                email_summaries=[],
                priority_assessment="",
                summary_text="Summary"
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_analysis_task_output_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisTaskOutput(total_count=0)
        errors = exc_info.value.errors()
        error_fields = {error['loc'][0] for error in errors}
        assert 'email_summaries' in error_fields
        assert 'priority_assessment' in error_fields
        assert 'summary_text' in error_fields
    
    def test_analysis_task_output_multiple_summaries(self):
        """Test AnalysisTaskOutput with multiple email summaries."""
        summaries = [
            EmailSummary(
                subject=f"Email {i}",
                sender=f"sender{i}@example.com",
                timestamp=datetime.now()
            )
            for i in range(5)
        ]
        output = AnalysisTaskOutput(
            total_count=5,
            email_summaries=summaries,
            action_items=["Action 1", "Action 2", "Action 3"],
            priority_assessment="Medium",
            summary_text="Summary of 5 emails"
        )
        assert len(output.email_summaries) == 5
        assert output.total_count == 5
        assert len(output.action_items) == 3
