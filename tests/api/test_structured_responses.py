"""Tests for structured responses in API endpoints.

This module tests the structured_result and token_usage fields in API responses,
ensuring backward compatibility and proper handling of structured data.

Requirements: 8.1, 8.2, 8.4, 8.6
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
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


class TestStructuredResponses:
    """Test suite for structured response fields in API."""
    
    def test_api_response_includes_structured_result_field(self):
        """Test that API response includes structured_result field.
        
        Requirements: 8.1, 8.2
        """
        # Create mock structured result
        mock_structured_result = AnalysisTaskOutput(
            total_count=2,
            email_summaries=[
                EmailSummary(
                    subject="Test Email 1",
                    sender="sender1@example.com",
                    timestamp=datetime.now(timezone.utc),
                    key_points=["Point 1", "Point 2"],
                    action_items=["Action 1"],
                    has_deadline=True
                ),
                EmailSummary(
                    subject="Test Email 2",
                    sender="sender2@example.com",
                    timestamp=datetime.now(timezone.utc),
                    key_points=["Point 3"],
                    action_items=[],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="High priority",
            summary_text="# Email Analysis\n\nTest summary"
        )
        
        mock_response = GmailAnalysisResponse(
            analysis_id="test-structured-123",
            result="# Email Analysis\n\nTest result",
            structured_result=mock_structured_result.model_dump(mode='json'),
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=45.2
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structured_result field exists
        assert "structured_result" in data
        assert data["structured_result"] is not None
    
    def test_api_response_includes_token_usage_field(self):
        """Test that API response includes token_usage field.
        
        Requirements: 8.1, 8.2
        """
        # Create mock token usage
        mock_token_usage = TokenUsage(
            total_tokens=5750,
            prompt_tokens=4150,
            completion_tokens=1600
        )
        
        mock_response = GmailAnalysisResponse(
            analysis_id="test-token-456",
            result="# Email Analysis\n\nTest result",
            token_usage=mock_token_usage.model_dump(mode='json'),
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=45.2
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify token_usage field exists
        assert "token_usage" in data
        assert data["token_usage"] is not None
    
    def test_structured_result_has_expected_fields(self):
        """Test that structured_result has expected fields (total_count, email_summaries, action_items).
        
        Requirements: 8.1, 8.4
        """
        # Create mock structured result with all expected fields
        mock_structured_result = AnalysisTaskOutput(
            total_count=3,
            email_summaries=[
                EmailSummary(
                    subject="Email 1",
                    sender="sender1@example.com",
                    timestamp=datetime.now(timezone.utc),
                    key_points=["Key point 1"],
                    action_items=["Action 1"],
                    has_deadline=True
                ),
                EmailSummary(
                    subject="Email 2",
                    sender="sender2@example.com",
                    timestamp=datetime.now(timezone.utc),
                    key_points=["Key point 2"],
                    action_items=["Action 2"],
                    has_deadline=False
                ),
                EmailSummary(
                    subject="Email 3",
                    sender="sender3@example.com",
                    timestamp=datetime.now(timezone.utc),
                    key_points=["Key point 3"],
                    action_items=[],
                    has_deadline=False
                )
            ],
            action_items=["Action 1", "Action 2"],
            priority_assessment="Medium priority",
            summary_text="# Email Analysis\n\nDetailed summary"
        )
        
        mock_response = GmailAnalysisResponse(
            analysis_id="test-fields-789",
            result="# Email Analysis\n\nTest result",
            structured_result=mock_structured_result.model_dump(mode='json'),
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=50.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structured_result has all expected fields
        assert "structured_result" in data
        structured = data["structured_result"]
        
        assert "total_count" in structured
        assert structured["total_count"] == 3
        
        assert "email_summaries" in structured
        assert isinstance(structured["email_summaries"], list)
        assert len(structured["email_summaries"]) == 3
        
        assert "action_items" in structured
        assert isinstance(structured["action_items"], list)
        assert len(structured["action_items"]) == 2
        
        assert "priority_assessment" in structured
        assert structured["priority_assessment"] == "Medium priority"
        
        assert "summary_text" in structured
        assert "Email Analysis" in structured["summary_text"]
    
    def test_token_usage_has_expected_fields(self):
        """Test that token_usage has expected fields (total_tokens, prompt_tokens, completion_tokens).
        
        Requirements: 8.1, 8.4
        """
        # Create mock token usage with all expected fields
        mock_token_usage = TokenUsage(
            total_tokens=8500,
            prompt_tokens=6000,
            completion_tokens=2500
        )
        
        mock_response = GmailAnalysisResponse(
            analysis_id="test-token-fields-abc",
            result="# Email Analysis\n\nTest result",
            token_usage=mock_token_usage.model_dump(mode='json'),
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=55.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify token_usage has all expected fields
        assert "token_usage" in data
        token_usage = data["token_usage"]
        
        assert "total_tokens" in token_usage
        assert token_usage["total_tokens"] == 8500
        
        assert "prompt_tokens" in token_usage
        assert token_usage["prompt_tokens"] == 6000
        
        assert "completion_tokens" in token_usage
        assert token_usage["completion_tokens"] == 2500
        
        # Verify token math is correct
        assert token_usage["total_tokens"] == (
            token_usage["prompt_tokens"] + token_usage["completion_tokens"]
        )
    
    def test_backward_compatibility_with_result_field(self):
        """Test that API maintains backward compatibility with result field.
        
        Requirements: 8.1, 8.4
        """
        # Create mock response with both structured and raw result
        mock_structured_result = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Test Email",
                    sender="sender@example.com",
                    timestamp=datetime.now(timezone.utc),
                    key_points=["Point 1"],
                    action_items=["Action 1"],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="Low priority",
            summary_text="# Email Analysis\n\nStructured summary"
        )
        
        mock_token_usage = TokenUsage(
            total_tokens=3000,
            prompt_tokens=2000,
            completion_tokens=1000
        )
        
        mock_response = GmailAnalysisResponse(
            analysis_id="test-backward-compat-xyz",
            result="# Email Analysis\n\nRaw markdown result for backward compatibility",
            structured_result=mock_structured_result.model_dump(mode='json'),
            token_usage=mock_token_usage.model_dump(mode='json'),
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=40.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify backward compatibility: result field must exist
        assert "result" in data
        assert data["result"] is not None
        assert isinstance(data["result"], str)
        assert "Email Analysis" in data["result"]
        assert "Raw markdown result" in data["result"]
        
        # Verify new fields also exist
        assert "structured_result" in data
        assert data["structured_result"] is not None
        
        assert "token_usage" in data
        assert data["token_usage"] is not None
        
        # Verify all required fields from original API contract
        assert "analysis_id" in data
        assert "parameters" in data
        assert "timestamp" in data
        assert "execution_time_seconds" in data
    
    def test_api_handles_missing_structured_result_gracefully(self):
        """Test that API handles missing structured_result gracefully.
        
        Requirements: 8.1, 8.6
        """
        # Create mock response without structured_result (backward compatibility scenario)
        mock_response = GmailAnalysisResponse(
            analysis_id="test-no-structured-def",
            result="# Email Analysis\n\nRaw result only",
            structured_result=None,  # No structured result
            token_usage=None,  # No token usage
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=35.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
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
        assert data["result"] is not None
        
        # Verify structured_result and token_usage are present but null
        assert "structured_result" in data
        assert data["structured_result"] is None
        
        assert "token_usage" in data
        assert data["token_usage"] is None
        
        # Verify other required fields are present
        assert "parameters" in data
        assert "timestamp" in data
        assert "execution_time_seconds" in data
    
    def test_streaming_endpoint_includes_structured_result(self):
        """Test that streaming endpoint includes structured_result in complete event.
        
        Requirements: 8.1, 8.2
        """
        # Create mock structured result with datetime objects
        mock_structured_result = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Streaming Test",
                    sender="stream@example.com",
                    timestamp=datetime.now(timezone.utc),
                    key_points=["Stream point"],
                    action_items=["Stream action"],
                    has_deadline=False
                )
            ],
            action_items=["Stream action"],
            priority_assessment="Normal",
            summary_text="# Streaming Analysis\n\nTest"
        )
        
        mock_token_usage = TokenUsage(
            total_tokens=4000,
            prompt_tokens=3000,
            completion_tokens=1000
        )
        
        mock_response = GmailAnalysisResponse(
            analysis_id="test-stream-structured-ghi",
            result="# Streaming Analysis\n\nTest result",
            structured_result=mock_structured_result.model_dump(mode='json'),
            token_usage=mock_token_usage.model_dump(mode='json'),
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=42.0
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
                assert response.status_code == 200
                
                # Collect all events
                events = []
                current_event = None
                for line in response.iter_lines():
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                    elif line.startswith("data:") and current_event == "complete":
                        data_str = line.split(":", 1)[1].strip()
                        import json
                        complete_data = json.loads(data_str)
                        events.append(complete_data)
                
                # Verify complete event was received
                assert len(events) > 0
                complete_event = events[0]
                
                # Verify all fields are present
                assert "analysis_id" in complete_event
                assert complete_event["analysis_id"] == "test-stream-structured-ghi"
                assert "result" in complete_event
                assert "parameters" in complete_event
                assert "timestamp" in complete_event
                assert "execution_time_seconds" in complete_event
                
                # Verify structured_result is present and has expected fields
                assert "structured_result" in complete_event
                assert complete_event["structured_result"] is not None
                assert "total_count" in complete_event["structured_result"]
                assert "email_summaries" in complete_event["structured_result"]
                assert "action_items" in complete_event["structured_result"]
                
                # Verify token_usage is present and has expected fields
                assert "token_usage" in complete_event
                assert complete_event["token_usage"] is not None
                assert "total_tokens" in complete_event["token_usage"]
                assert complete_event["token_usage"]["total_tokens"] == 4000
    
    def test_streaming_endpoint_handles_missing_structured_result(self):
        """Test that streaming endpoint handles missing structured_result gracefully.
        
        Requirements: 8.1, 8.6
        """
        # Create mock response without structured data
        mock_response = GmailAnalysisResponse(
            analysis_id="test-stream-no-struct-jkl",
            result="# Streaming Analysis\n\nRaw only",
            structured_result=None,
            token_usage=None,
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=38.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={"sender_emails": "test@example.com"}
            ) as response:
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
                
                # Verify complete event is valid without structured data
                assert complete_data is not None
                assert "analysis_id" in complete_data
                assert "result" in complete_data
                
                # structured_result and token_usage should not be in the response
                # if they are None (they are omitted in the streaming response)
                # OR they should be present but null
                # Let's verify the response is valid either way
                assert complete_data["result"] is not None
    
    def test_email_summaries_structure_in_structured_result(self):
        """Test that email_summaries in structured_result have correct structure.
        
        Requirements: 8.1, 8.4
        """
        # Create detailed mock with multiple email summaries
        mock_structured_result = AnalysisTaskOutput(
            total_count=2,
            email_summaries=[
                EmailSummary(
                    subject="First Email",
                    sender="first@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 30, 0, tzinfo=timezone.utc),
                    key_points=["Point A", "Point B", "Point C"],
                    action_items=["Action A", "Action B"],
                    has_deadline=True
                ),
                EmailSummary(
                    subject="Second Email",
                    sender="second@example.com",
                    timestamp=datetime(2025, 11, 19, 11, 45, 0, tzinfo=timezone.utc),
                    key_points=["Point X"],
                    action_items=[],
                    has_deadline=False
                )
            ],
            action_items=["Action A", "Action B"],
            priority_assessment="High",
            summary_text="# Analysis\n\nDetailed"
        )
        
        mock_response = GmailAnalysisResponse(
            analysis_id="test-email-structure-mno",
            result="# Analysis\n\nTest",
            structured_result=mock_structured_result.model_dump(mode='json'),
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.now(timezone.utc),
            execution_time_seconds=48.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            response = client.post(
                "/api/flows/gmail-read",
                json={
                    "sender_emails": ["test@example.com"],
                    "language": "en",
                    "days": 7
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify email_summaries structure
        summaries = data["structured_result"]["email_summaries"]
        assert len(summaries) == 2
        
        # Check first email summary
        first = summaries[0]
        assert first["subject"] == "First Email"
        assert first["sender"] == "first@example.com"
        assert "timestamp" in first
        assert isinstance(first["key_points"], list)
        assert len(first["key_points"]) == 3
        assert isinstance(first["action_items"], list)
        assert len(first["action_items"]) == 2
        assert first["has_deadline"] is True
        
        # Check second email summary
        second = summaries[1]
        assert second["subject"] == "Second Email"
        assert second["sender"] == "second@example.com"
        assert "timestamp" in second
        assert isinstance(second["key_points"], list)
        assert len(second["key_points"]) == 1
        assert isinstance(second["action_items"], list)
        assert len(second["action_items"]) == 0
        assert second["has_deadline"] is False
