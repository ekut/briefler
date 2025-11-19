"""API error handling tests for structured outputs.

This test file verifies that the API handles serialization errors gracefully
and returns 200 status codes even when structured output processing fails.

Requirements: 8.5
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone

from api.main import app
from api.models.responses import GmailAnalysisResponse
from briefler.models.task_outputs import (
    AnalysisTaskOutput,
    EmailSummary,
    TokenUsage
)


# Create test client
client = TestClient(app)


class TestAPISerializationErrorHandling:
    """Test that API handles serialization errors gracefully.
    
    Validates: Requirements 8.5 - Serialization error handling in API
    """
    
    def test_api_handles_structured_result_serialization_error(self):
        """Test that API handles serialization errors for structured_result.
        
        Validates: Requirements 8.5 - API handles serialization errors
        """
        # Create a mock flow with structured_result that raises error on model_dump
        mock_flow = MagicMock()
        mock_flow.state.result = "# Email Analysis\n\nTest result"
        
        # Create a mock structured_result that raises TypeError on model_dump
        mock_structured_result = MagicMock()
        mock_structured_result.model_dump.side_effect = TypeError("Cannot serialize datetime")
        mock_flow.state.structured_result = mock_structured_result
        mock_flow.state.total_token_usage = None
        
        with patch('api.services.flow_service.GmailReadFlow') as mock_flow_class:
            mock_flow_class.return_value = mock_flow
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        # API should return 200 even with serialization error
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has required fields
        assert "analysis_id" in data
        assert "result" in data
        assert data["result"] is not None
        
        # structured_result should not be in response due to serialization error
        # OR it should be None/null
        if "structured_result" in data:
            assert data["structured_result"] is None
    
    def test_api_handles_token_usage_serialization_error(self):
        """Test that API handles serialization errors for token_usage.
        
        Validates: Requirements 8.5 - API handles token_usage serialization errors
        """
        # Create a mock flow with token_usage that raises error on model_dump
        mock_flow = MagicMock()
        mock_flow.state.result = "# Email Analysis\n\nTest result"
        mock_flow.state.structured_result = None
        
        # Create a mock token_usage that raises AttributeError on model_dump
        mock_token_usage = MagicMock()
        mock_token_usage.model_dump.side_effect = AttributeError("Object has no attribute 'model_dump'")
        mock_flow.state.total_token_usage = mock_token_usage
        
        with patch('api.services.flow_service.GmailReadFlow') as mock_flow_class:
            mock_flow_class.return_value = mock_flow
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        # API should return 200 even with serialization error
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has required fields
        assert "analysis_id" in data
        assert "result" in data
        assert data["result"] is not None
        
        # token_usage should not be in response due to serialization error
        # OR it should be None/null
        if "token_usage" in data:
            assert data["token_usage"] is None
    
    def test_api_returns_200_when_structured_output_fails(self):
        """Test that API returns 200 even when structured output processing fails.
        
        Validates: Requirements 8.5 - API returns 200 on structured output failure
        """
        # Create a mock flow with no structured data (validation failed in flow)
        mock_flow = MagicMock()
        mock_flow.state.result = "# Email Analysis\n\nRaw result only"
        mock_flow.state.structured_result = None
        mock_flow.state.total_token_usage = None
        
        with patch('api.services.flow_service.GmailReadFlow') as mock_flow_class:
            mock_flow_class.return_value = mock_flow
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        # API should return 200 even without structured data
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is valid
        assert "analysis_id" in data
        assert "result" in data
        assert data["result"] == "# Email Analysis\n\nRaw result only"
        assert "parameters" in data
        assert "timestamp" in data
        assert "execution_time_seconds" in data
        
        # Verify structured fields are absent or null
        if "structured_result" in data:
            assert data["structured_result"] is None
        if "token_usage" in data:
            assert data["token_usage"] is None
    
    def test_api_handles_both_serialization_errors(self):
        """Test that API handles serialization errors for both structured_result and token_usage.
        
        Validates: Requirements 8.5 - API handles multiple serialization errors
        """
        # Create a mock flow with both fields raising errors
        mock_flow = MagicMock()
        mock_flow.state.result = "# Email Analysis\n\nTest result"
        
        # Both raise serialization errors
        mock_structured_result = MagicMock()
        mock_structured_result.model_dump.side_effect = Exception("Unexpected serialization error")
        mock_flow.state.structured_result = mock_structured_result
        
        mock_token_usage = MagicMock()
        mock_token_usage.model_dump.side_effect = Exception("Unexpected serialization error")
        mock_flow.state.total_token_usage = mock_token_usage
        
        with patch('api.services.flow_service.GmailReadFlow') as mock_flow_class:
            mock_flow_class.return_value = mock_flow
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        # API should return 200 even with both serialization errors
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has required fields
        assert "analysis_id" in data
        assert "result" in data
        assert data["result"] is not None
        
        # Both structured fields should be absent or null
        if "structured_result" in data:
            assert data["structured_result"] is None
        if "token_usage" in data:
            assert data["token_usage"] is None
    
    def test_api_continues_response_generation_after_serialization_failure(self):
        """Test that API continues generating response after serialization failure.
        
        Validates: Requirements 8.5 - API continues after serialization failure
        """
        # Create a mock flow where structured_result fails but token_usage succeeds
        mock_flow = MagicMock()
        mock_flow.state.result = "# Email Analysis\n\nTest result"
        
        # structured_result raises error
        mock_structured_result = MagicMock()
        mock_structured_result.model_dump.side_effect = TypeError("Serialization failed")
        mock_flow.state.structured_result = mock_structured_result
        
        # token_usage succeeds
        mock_token_usage = TokenUsage(
            total_tokens=5000,
            prompt_tokens=3500,
            completion_tokens=1500
        )
        mock_flow.state.total_token_usage = mock_token_usage
        
        with patch('api.services.flow_service.GmailReadFlow') as mock_flow_class:
            mock_flow_class.return_value = mock_flow
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        # API should return 200
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has required fields
        assert "analysis_id" in data
        assert "result" in data
        
        # token_usage should be present since it succeeded
        assert "token_usage" in data
        assert data["token_usage"] is not None
        assert data["token_usage"]["total_tokens"] == 5000
        
        # structured_result should be absent or null due to error
        if "structured_result" in data:
            assert data["structured_result"] is None
    
    def test_streaming_api_handles_serialization_errors(self):
        """Test that streaming API handles serialization errors gracefully.
        
        Validates: Requirements 8.5 - Streaming API handles serialization errors
        """
        # Create a mock response with serialization issues
        mock_response = GmailAnalysisResponse(
            analysis_id="test-stream-error-123",
            result="# Email Analysis\n\nTest result",
            structured_result=None,  # Simulating serialization failure
            token_usage=None,  # Simulating serialization failure
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=45.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={
                    "sender_emails": "test@example.com",
                    "language": "en",
                    "days": 7
                }
            ) as response:
                # Streaming should return 200 even with serialization errors
                assert response.status_code == 200
                
                # Collect complete event
                complete_data = None
                current_event = None
                for line in response.iter_lines():
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                    elif line.startswith("data:") and current_event == "complete":
                        data_str = line.split(":", 1)[1].strip()
                        import json
                        complete_data = json.loads(data_str)
                        break
                
                # Verify complete event is valid
                assert complete_data is not None
                assert "analysis_id" in complete_data
                assert "result" in complete_data
                assert complete_data["result"] is not None
    
    def test_api_never_fails_due_to_structured_output_issues(self):
        """Test that API never fails due to structured output issues.
        
        Validates: Requirements 8.5 - API never fails due to structured output
        """
        # Create various scenarios that could cause issues
        test_scenarios = [
            # Scenario 1: Both fields are None
            {
                'structured_result': None,
                'token_usage': None
            },
            # Scenario 2: structured_result raises TypeError
            {
                'structured_result': MagicMock(model_dump=MagicMock(side_effect=TypeError("Type error"))),
                'token_usage': None
            },
            # Scenario 3: token_usage raises AttributeError
            {
                'structured_result': None,
                'token_usage': MagicMock(model_dump=MagicMock(side_effect=AttributeError("Attr error")))
            },
            # Scenario 4: Both raise different exceptions
            {
                'structured_result': MagicMock(model_dump=MagicMock(side_effect=ValueError("Value error"))),
                'token_usage': MagicMock(model_dump=MagicMock(side_effect=RuntimeError("Runtime error")))
            }
        ]
        
        for i, scenario in enumerate(test_scenarios):
            mock_flow = MagicMock()
            mock_flow.state.result = f"# Email Analysis\n\nScenario {i+1}"
            mock_flow.state.structured_result = scenario['structured_result']
            mock_flow.state.total_token_usage = scenario['token_usage']
            
            with patch('api.services.flow_service.GmailReadFlow') as mock_flow_class:
                mock_flow_class.return_value = mock_flow
                
                response = client.post(
                    "/api/flows/gmail-read",
                    json={
                        "sender_emails": ["test@example.com"],
                        "language": "en",
                        "days": 7
                    }
                )
            
            # All scenarios should return 200
            assert response.status_code == 200, f"Scenario {i+1} failed"
            data = response.json()
            
            # All scenarios should have valid response
            assert "analysis_id" in data, f"Scenario {i+1} missing analysis_id"
            assert "result" in data, f"Scenario {i+1} missing result"
            assert data["result"] is not None, f"Scenario {i+1} has null result"


class TestFlowContinuesOnValidationErrors:
    """Test that flow continues execution after validation errors.
    
    Validates: Requirements 8.5 - Flow continues on validation errors
    """
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_completes_with_validation_error(self, mock_crew_class):
        """Test that flow completes execution even with validation errors.
        
        Validates: Requirements 8.5 - Flow completes with validation error
        """
        from briefler.flows.gmail_read_flow import GmailReadFlow
        
        # Create mock result with invalid data
        mock_result = MagicMock()
        mock_result.pydantic = None
        mock_result.json_dict = {
            'total_count': -1,  # Invalid: negative count
            'email_summaries': [],
            'priority_assessment': 'High',
            'summary_text': 'Summary'
        }
        mock_result.raw = "# Email Analysis\n\nCompleted despite error"
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
        
        # Verify flow completed
        assert flow.state.result is not None
        assert flow.state.result == "# Email Analysis\n\nCompleted despite error"
        assert flow.state.structured_result is None
        
        # Verify flow is in a valid state for subsequent operations
        assert flow.state.sender_emails == ['test@example.com']
        assert flow.state.language == 'en'
        assert flow.state.days == 7
    
    @patch('briefler.flows.gmail_read_flow.gmail_read_flow.GmailReaderCrew')
    def test_flow_can_be_reused_after_validation_error(self, mock_crew_class):
        """Test that flow can be reused after validation errors.
        
        Validates: Requirements 8.5 - Flow can be reused after errors
        """
        from briefler.flows.gmail_read_flow import GmailReadFlow
        
        # First execution with validation error
        mock_result_error = MagicMock()
        mock_result_error.pydantic = None
        mock_result_error.json_dict = {'invalid': 'data'}
        mock_result_error.raw = "# First execution with error"
        mock_result_error.token_usage = None
        mock_result_error.usage_metrics = None
        
        # Second execution with valid data
        mock_result_success = MagicMock()
        mock_result_success.pydantic = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Test",
                    sender="test@example.com",
                    timestamp=datetime.now(timezone.utc),
                    key_points=["Point"],
                    action_items=["Action"],
                    has_deadline=False
                )
            ],
            action_items=["Action"],
            priority_assessment="Low",
            summary_text="# Second execution success"
        )
        mock_result_success.raw = "# Second execution success"
        mock_result_success.token_usage = None
        mock_result_success.usage_metrics = None
        
        # Mock crew instance
        mock_crew_instance = MagicMock()
        mock_crew_class.return_value = mock_crew_instance
        
        # First execution with error
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result_error
        flow = GmailReadFlow()
        flow.kickoff(inputs={
            'sender_emails': ['test1@example.com'],
            'language': 'en',
            'days': 7
        })
        
        assert flow.state.structured_result is None
        assert flow._validation_failure_count == 1
        
        # Second execution with success
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result_success
        flow.state.sender_emails = ['test2@example.com']
        flow.analyze_emails()
        
        # Verify flow recovered and processed valid data
        assert flow.state.structured_result is not None
        assert isinstance(flow.state.structured_result, AnalysisTaskOutput)
        assert flow.state.structured_result.total_count == 1
        # Validation failure count should still be 1 (no new failures)
        assert flow._validation_failure_count == 1
