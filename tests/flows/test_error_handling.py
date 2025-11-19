"""Error handling tests for structured outputs.

This test file verifies error handling for validation errors in flow
and serialization errors in API, ensuring the system continues to operate
gracefully when structured output processing fails.

Requirements: 8.5
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


class TestFlowValidationErrorHandling:
    """Test that flow handles validation errors gracefully.
    
    Validates: Requirements 8.5 - Validation error handling in flow
    """
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_handles_validation_error_gracefully(self, mock_crew_class):
        """Test that flow handles validation errors without crashing.
        
        Validates: Requirements 8.5 - Flow handles validation errors gracefully
        """
        # Create mock result with invalid json_dict (missing required fields)
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': 1,
            # Missing required fields: email_summaries, priority_assessment, summary_text
            'action_items': []
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
        
        # This should complete without raising an exception
        try:
            flow.kickoff(inputs={
                'sender_emails': ['test@example.com'],
                'language': 'en',
                'days': 7
            })
            validation_error_raised = False
        except ValidationError:
            validation_error_raised = True
        except Exception as e:
            pytest.fail(f"Flow raised unexpected exception: {type(e).__name__}: {e}")
        
        # Verify no validation error was raised
        assert not validation_error_raised, "Flow should not raise ValidationError"
        
        # Verify flow completed with fallback to raw result
        assert flow.state.result is not None, "Flow should have raw result"
        assert flow.state.structured_result is None, "Structured result should be None on validation error"
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_continues_execution_after_validation_error(self, mock_crew_class):
        """Test that flow continues execution after validation errors.
        
        Validates: Requirements 8.5 - Flow continues after validation errors
        """
        # Create mock result with invalid data that will cause validation error
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': 'invalid',  # Should be int, not string
            'email_summaries': [],
            'action_items': [],
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
        
        # Execute flow
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test@example.com'],
            'language': 'en',
            'days': 7
        })
        
        # Verify flow completed execution despite validation error
        assert flow.state.result is not None, "Flow should complete execution"
        assert flow.state.result == "# Email Analysis\n\nTest summary"
        assert flow.state.structured_result is None, "Structured result should be None"
        
        # Verify validation failure was tracked
        assert flow._validation_failure_count == 1, "Validation failure should be tracked"
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_tracks_repeated_validation_failures(self, mock_crew_class):
        """Test that flow tracks repeated validation failures.
        
        Validates: Requirements 8.5 - Track repeated validation failures
        """
        # Create mock result with invalid data
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': 1,
            # Missing required fields to trigger validation error
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
        assert flow._validation_failure_count == 1, "First failure should be tracked"
        
        # Second execution (reuse same flow instance)
        flow.state.sender_emails = ['test2@example.com']
        flow.analyze_emails()
        assert flow._validation_failure_count == 2, "Second failure should be tracked"
        
        # Third execution
        flow.state.sender_emails = ['test3@example.com']
        flow.analyze_emails()
        assert flow._validation_failure_count == 3, "Third failure should be tracked"
        
        # Verify flow continues to work after multiple failures
        assert flow.state.result is not None, "Flow should continue working"
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_handles_missing_required_fields(self, mock_crew_class):
        """Test that flow handles missing required fields in validation.
        
        Validates: Requirements 8.5 - Handle missing required fields
        """
        # Create mock result with missing multiple required fields
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            # Only has total_count, missing all other required fields
            'total_count': 5
        }
        mock_result.raw = "# Email Analysis\n\nFallback summary"
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
        assert flow.state.result == "# Email Analysis\n\nFallback summary"
        assert flow.state.structured_result is None
        assert flow._validation_failure_count == 1
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_handles_invalid_field_types(self, mock_crew_class):
        """Test that flow handles invalid field types in validation.
        
        Validates: Requirements 8.5 - Handle invalid field types
        """
        # Create mock result with wrong field types
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': 'not_a_number',  # Should be int
            'email_summaries': 'not_a_list',  # Should be list
            'action_items': {'not': 'a_list'},  # Should be list
            'priority_assessment': 123,  # Should be string
            'summary_text': ['not', 'a', 'string']  # Should be string
        }
        mock_result.raw = "# Email Analysis\n\nType error fallback"
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
        assert flow.state.result == "# Email Analysis\n\nType error fallback"
        assert flow.state.structured_result is None
        assert flow._validation_failure_count == 1
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_handles_nested_validation_errors(self, mock_crew_class):
        """Test that flow handles validation errors in nested objects.
        
        Validates: Requirements 8.5 - Handle nested validation errors
        """
        # Create mock result with invalid nested email summary
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': 1,
            'email_summaries': [
                {
                    'subject': 'Test',
                    'sender': 'invalid_email',  # Invalid email format
                    'timestamp': 'not_a_datetime',  # Invalid datetime
                    'key_points': 'not_a_list',  # Should be list
                    'action_items': 'not_a_list',  # Should be list
                    'has_deadline': 'not_a_bool'  # Should be bool
                }
            ],
            'action_items': [],
            'priority_assessment': 'High',
            'summary_text': 'Summary'
        }
        mock_result.raw = "# Email Analysis\n\nNested error fallback"
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
        assert flow.state.result == "# Email Analysis\n\nNested error fallback"
        assert flow.state.structured_result is None
        assert flow._validation_failure_count == 1
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_handles_exception_accessing_pydantic(self, mock_crew_class):
        """Test that flow handles exceptions when accessing pydantic attribute.
        
        Validates: Requirements 8.5 - Handle unexpected exceptions
        """
        # Create mock result that raises exception when accessing pydantic
        mock_result = MagicMock()
        # Configure pydantic to raise an exception when accessed
        type(mock_result).pydantic = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Unexpected error accessing pydantic"))
        )
        mock_result.json_dict = None
        mock_result.raw = "# Email Analysis\n\nException fallback"
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
        
        # Verify flow completed with fallback
        assert flow.state.result == "# Email Analysis\n\nException fallback"
        assert flow.state.structured_result is None
        # Note: _validation_failure_count is not incremented for non-ValidationError exceptions
