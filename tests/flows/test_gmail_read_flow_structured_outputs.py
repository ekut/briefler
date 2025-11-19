"""Integration tests for GmailReadFlow structured outputs.

This test file verifies that the flow correctly extracts and handles
structured outputs from crew execution, including token usage tracking
and error handling.

Requirements: 8.1, 8.2, 8.4, 8.6
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from pydantic import ValidationError

from briefler.flows.gmail_read_flow import GmailReadFlow
from briefler.models.task_outputs import (
    AnalysisTaskOutput,
    EmailSummary,
    TokenUsage
)


class TestFlowExtractsStructuredResult:
    """Test that flow extracts structured result from crew execution.
    
    Validates: Requirements 8.1, 8.2 - Flow extracts structured data from crew
    """
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_extracts_structured_result_from_crew(self, mock_crew_class):
        """Test that flow extracts structured result from crew.pydantic.
        
        Validates: Requirements 8.1 - Flow accesses structured data from crew result
        """
        # Create mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=2,
            email_summaries=[
                EmailSummary(
                    subject="Test Email 1",
                    sender="sender1@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Point 1", "Point 2"],
                    action_items=["Action 1"],
                    has_deadline=True
                ),
                EmailSummary(
                    subject="Test Email 2",
                    sender="sender2@example.com",
                    timestamp=datetime(2025, 11, 19, 11, 0, 0),
                    key_points=["Point 3"],
                    action_items=[],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="High",
            summary_text="# Email Analysis\n\nTest summary"
        )
        
        # Create mock crew result with pydantic attribute
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_result.token_usage = None
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify flow extracted structured result
        assert flow.state.structured_result is not None, \
            "Flow should extract structured result from crew"
        assert isinstance(flow.state.structured_result, AnalysisTaskOutput), \
            "Structured result should be AnalysisTaskOutput instance"
        assert flow.state.structured_result.total_count == 2, \
            "Structured result should have correct total_count"
        assert len(flow.state.structured_result.email_summaries) == 2, \
            "Structured result should have correct number of email summaries"
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_extracts_from_json_dict_fallback(self, mock_crew_class):
        """Test that flow falls back to json_dict when pydantic not available.
        
        Validates: Requirements 8.1 - Flow handles fallback to json_dict
        """
        # Create mock result with json_dict but no pydantic
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': 1,
            'email_summaries': [
                {
                    'subject': 'Test Email',
                    'sender': 'sender@example.com',
                    'timestamp': '2025-11-19T10:00:00',
                    'key_points': ['Point 1'],
                    'action_items': ['Action 1'],
                    'has_deadline': False
                }
            ],
            'action_items': ['Action 1'],
            'priority_assessment': 'Medium',
            'summary_text': '# Email Analysis\n\nTest summary'
        }
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_result.token_usage = None
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify flow extracted structured result from json_dict
        assert flow.state.structured_result is not None, \
            "Flow should extract structured result from json_dict"
        assert isinstance(flow.state.structured_result, AnalysisTaskOutput), \
            "Structured result should be AnalysisTaskOutput instance"
        assert flow.state.structured_result.total_count == 1, \
            "Structured result should have correct total_count"


class TestFlowStateStructuredResultPopulated:
    """Test that flow.state.structured_result is populated correctly.
    
    Validates: Requirements 8.2 - FlowState stores structured data
    """
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_state_structured_result_is_populated(self, mock_crew_class):
        """Test that flow.state.structured_result is populated after execution.
        
        Validates: Requirements 8.2 - FlowState structured_result field is populated
        """
        # Create mock structured result with specific data
        mock_analysis_output = AnalysisTaskOutput(
            total_count=3,
            email_summaries=[
                EmailSummary(
                    subject=f"Email {i}",
                    sender=f"sender{i}@example.com",
                    timestamp=datetime(2025, 11, 19, 10 + i, 0, 0),
                    key_points=[f"Point {i}"],
                    action_items=[f"Action {i}"] if i < 2 else [],
                    has_deadline=i == 0
                )
                for i in range(3)
            ],
            action_items=["Action 0", "Action 1"],
            priority_assessment="High",
            summary_text="# Email Analysis\n\nDetailed summary"
        )
        
        # Create mock crew result
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nDetailed summary"
        mock_result.token_usage = None
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify all structured fields are accessible from flow.state
        assert flow.state.structured_result.total_count == 3
        assert len(flow.state.structured_result.email_summaries) == 3
        assert len(flow.state.structured_result.action_items) == 2
        assert flow.state.structured_result.priority_assessment == "High"
        assert "Detailed summary" in flow.state.structured_result.summary_text
        
        # Verify nested fields are accessible
        first_email = flow.state.structured_result.email_summaries[0]
        assert first_email.subject == "Email 0"
        assert first_email.sender == "sender0@example.com"
        assert first_email.has_deadline is True
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_state_preserves_raw_result(self, mock_crew_class):
        """Test that flow.state.result (raw) is preserved for backward compatibility.
        
        Validates: Requirements 8.4 - Backward compatibility with raw result
        """
        # Create mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Test Email",
                    sender="sender@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Point 1"],
                    action_items=["Action 1"],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="Low",
            summary_text="# Email Analysis\n\nTest summary for backward compatibility"
        )
        
        # Create mock crew result with both pydantic and raw
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nTest summary for backward compatibility"
        mock_result.token_usage = None
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify both raw and structured results are available
        assert flow.state.result is not None, "Raw result should be preserved"
        assert flow.state.structured_result is not None, "Structured result should be available"
        
        # Verify raw result is a string
        assert isinstance(flow.state.result, str)
        assert "Email Analysis" in flow.state.result
        
        # Verify structured result is AnalysisTaskOutput
        assert isinstance(flow.state.structured_result, AnalysisTaskOutput)


class TestFlowTokenUsagePopulated:
    """Test that flow.state.total_token_usage is populated correctly.
    
    Validates: Requirements 8.2, 8.4 - Token usage tracking and aggregation
    """
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_state_total_token_usage_is_populated(self, mock_crew_class):
        """Test that flow.state.total_token_usage is populated after execution.
        
        Validates: Requirements 8.2 - FlowState total_token_usage field is populated
        """
        # Create mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Test Email",
                    sender="sender@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Point 1"],
                    action_items=["Action 1"],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="Medium",
            summary_text="# Email Analysis\n\nTest summary"
        )
        
        # Create mock crew result with token_usage
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_result.token_usage = {
            'total_tokens': 5750,
            'prompt_tokens': 4150,
            'completion_tokens': 1600
        }
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify token usage is populated
        assert flow.state.total_token_usage is not None, \
            "Token usage should be populated"
        assert isinstance(flow.state.total_token_usage, TokenUsage), \
            "Token usage should be TokenUsage instance"
        assert flow.state.total_token_usage.total_tokens == 5750
        assert flow.state.total_token_usage.prompt_tokens == 4150
        assert flow.state.total_token_usage.completion_tokens == 1600
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_token_usage_aggregation_from_usage_metrics(self, mock_crew_class):
        """Test that token usage is aggregated from crew.usage_metrics.
        
        Validates: Requirements 8.4 - Token usage aggregation from crew.usage_metrics
        """
        # Create mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Test Email",
                    sender="sender@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Point 1"],
                    action_items=["Action 1"],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="Medium",
            summary_text="# Email Analysis\n\nTest summary"
        )
        
        # Create mock crew result with usage_metrics (fallback)
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_result.token_usage = None
        mock_result.usage_metrics = {
            'total_tokens': 3200,
            'prompt_tokens': 2100,
            'completion_tokens': 1100
        }
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify token usage is aggregated from usage_metrics
        assert flow.state.total_token_usage is not None
        assert flow.state.total_token_usage.total_tokens == 3200
        assert flow.state.total_token_usage.prompt_tokens == 2100
        assert flow.state.total_token_usage.completion_tokens == 1100
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_token_usage_handles_missing_metrics(self, mock_crew_class):
        """Test that flow handles missing token usage metrics gracefully.
        
        Validates: Requirements 8.6 - Error handling for missing token usage
        """
        # Create mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Test Email",
                    sender="sender@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Point 1"],
                    action_items=["Action 1"],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="Medium",
            summary_text="# Email Analysis\n\nTest summary"
        )
        
        # Create mock crew result without token usage
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_result.token_usage = None
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify flow continues without token usage
        assert flow.state.total_token_usage is None, \
            "Token usage should be None when not available"
        assert flow.state.structured_result is not None, \
            "Structured result should still be available"


class TestFlowValidationErrorHandling:
    """Test that flow handles validation errors gracefully.
    
    Validates: Requirements 8.6 - Error handling for validation errors
    """
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_fallback_to_raw_result_on_validation_errors(self, mock_crew_class):
        """Test that flow falls back to raw result when validation errors occur.
        
        Validates: Requirements 8.6 - Fallback to raw result on validation errors
        """
        # Create mock result with invalid json_dict (missing required fields)
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': 1,
            # Missing required fields: email_summaries, priority_assessment, summary_text
        }
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_result.token_usage = None
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify flow falls back to raw result
        assert flow.state.structured_result is None, \
            "Structured result should be None on validation error"
        assert flow.state.result is not None, \
            "Raw result should still be available"
        assert flow.state.result == "# Email Analysis\n\nTest summary"
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_continues_execution_after_validation_error(self, mock_crew_class):
        """Test that flow continues execution after validation errors.
        
        Validates: Requirements 8.6 - Flow continues after validation errors
        """
        # Create mock result with invalid data
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': -1,  # Invalid: negative count
            'email_summaries': [],
            'priority_assessment': 'High',
            'summary_text': 'Summary'
        }
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_result.token_usage = None
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow - should not raise exception
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify flow completed execution
        assert flow.state.result is not None, "Flow should complete execution"
        assert flow.state.structured_result is None, "Structured result should be None"
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_validation_failure_count_tracking(self, mock_crew_class):
        """Test that flow tracks repeated validation failures.
        
        Validates: Requirements 8.6 - Track repeated validation failures
        """
        # Create mock result with invalid data
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': 1,
            # Missing required fields
        }
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_result.token_usage = None
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow multiple times to trigger repeated failures
        flow = GmailReadFlow()
        
        # First execution
        flow.kickoff(inputs={
            'sender_emails': ['test1@example.com'],
            'language': 'en',
            'days': 7
        })
        assert flow._validation_failure_count == 1
        
        # Second execution (reuse same flow instance)
        flow.state.sender_emails = ['test2@example.com']
        flow.analyze_emails()
        assert flow._validation_failure_count == 2
        
        # Third execution
        flow.state.sender_emails = ['test3@example.com']
        flow.analyze_emails()
        assert flow._validation_failure_count == 3
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_handles_unexpected_exceptions_gracefully(self, mock_crew_class):
        """Test that flow handles unexpected exceptions during extraction.
        
        Validates: Requirements 8.6 - Handle unexpected exceptions gracefully
        """
        # Create mock result that raises exception when accessing pydantic
        mock_result = MagicMock()
        # Configure pydantic to raise an exception when accessed
        type(mock_result).pydantic = property(lambda self: (_ for _ in ()).throw(RuntimeError("Unexpected error")))
        mock_result.json_dict = None
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_result.token_usage = None
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow - should not raise exception
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify flow completed execution with fallback
        assert flow.state.result is not None, "Flow should complete with raw result"
        assert flow.state.structured_result is None, "Structured result should be None"


class TestFlowStructuredOutputIntegration:
    """Integration tests for complete flow structured output workflow.
    
    Validates: Requirements 8.1, 8.2, 8.4, 8.6 - Complete workflow
    """
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_complete_flow_with_structured_outputs_and_token_usage(self, mock_crew_class):
        """Test complete flow execution with structured outputs and token usage.
        
        Validates: Requirements 8.1, 8.2, 8.4 - Complete structured output workflow
        """
        # Create comprehensive mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=3,
            email_summaries=[
                EmailSummary(
                    subject="Urgent: Project Deadline",
                    sender="manager@example.com",
                    timestamp=datetime(2025, 11, 19, 9, 0, 0),
                    key_points=["Project due Friday", "Need status update"],
                    action_items=["Submit status report", "Schedule meeting"],
                    has_deadline=True
                ),
                EmailSummary(
                    subject="Team Lunch",
                    sender="hr@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 30, 0),
                    key_points=["Lunch at 12pm", "Italian restaurant"],
                    action_items=["RSVP by tomorrow"],
                    has_deadline=True
                ),
                EmailSummary(
                    subject="Newsletter",
                    sender="marketing@example.com",
                    timestamp=datetime(2025, 11, 19, 11, 0, 0),
                    key_points=["New product launch", "Customer testimonials"],
                    action_items=[],
                    has_deadline=False
                )
            ],
            action_items=["Submit status report", "Schedule meeting", "RSVP by tomorrow"],
            priority_assessment="High - Multiple deadlines",
            summary_text="# Email Analysis\n\n## Summary\n3 emails analyzed with 3 action items"
        )
        
        # Create mock crew result with complete data
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\n## Summary\n3 emails analyzed with 3 action items"
        mock_result.token_usage = {
            'total_tokens': 8500,
            'prompt_tokens': 6200,
            'completion_tokens': 2300
        }
        mock_result.usage_metrics = None
        
        # Mock crew instance and kickoff
        mock_crew_instance = MagicMock()
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['manager@example.com', 'hr@example.com', 'marketing@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify complete structured output
        assert flow.state.structured_result is not None
        assert flow.state.structured_result.total_count == 3
        assert len(flow.state.structured_result.email_summaries) == 3
        assert len(flow.state.structured_result.action_items) == 3
        assert "High" in flow.state.structured_result.priority_assessment
        
        # Verify token usage
        assert flow.state.total_token_usage is not None
        assert flow.state.total_token_usage.total_tokens == 8500
        assert flow.state.total_token_usage.prompt_tokens == 6200
        assert flow.state.total_token_usage.completion_tokens == 2300
        
        # Verify backward compatibility
        assert flow.state.result is not None
        assert isinstance(flow.state.result, str)
        assert "Email Analysis" in flow.state.result
        
        # Verify all email summaries have correct structure
        for i, summary in enumerate(flow.state.structured_result.email_summaries):
            assert summary.subject is not None
            assert summary.sender is not None
            assert summary.timestamp is not None
            assert isinstance(summary.key_points, list)
            assert isinstance(summary.action_items, list)
            assert isinstance(summary.has_deadline, bool)
