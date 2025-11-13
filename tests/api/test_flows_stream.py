"""Tests for GET /api/flows/gmail-read/stream SSE endpoint.

This module tests the Server-Sent Events streaming endpoint including:
- SSE event format validation
- Progress event emission
- Complete event with result
- Error event handling
- Query parameter validation
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime
import json

from api.main import app
from api.models.responses import GmailAnalysisResponse


# Create test client
client = TestClient(app)


class TestStreamGmailReadEndpoint:
    """Test suite for GET /api/flows/gmail-read/stream SSE endpoint."""
    
    def test_stream_valid_parameters_success(self):
        """Test SSE endpoint with valid parameters emits progress and complete events.
        
        Requirements: 3.1, 3.2, 3.4, 3.5
        """
        # Mock the flow service to avoid actual Gmail API calls
        mock_response = GmailAnalysisResponse(
            analysis_id="test-stream-uuid-123",
            result="# Email Analysis\n\nTest streaming analysis result.",
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.utcnow(),
            execution_time_seconds=45.2
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            # Make streaming request
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
                assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
                
                # Collect all events
                events = []
                for line in response.iter_lines():
                    if line:
                        events.append(line)
                
                # Convert to string for easier parsing
                event_text = "\n".join(events)
                
                # Verify progress events are present
                assert "event: progress" in event_text
                assert "Initializing analysis" in event_text
                
                # Verify complete event is present
                assert "event: complete" in event_text
                assert "test-stream-uuid-123" in event_text
    
    def test_stream_multiple_senders(self):
        """Test SSE endpoint with multiple sender emails.
        
        Requirements: 3.1, 3.3
        """
        mock_response = GmailAnalysisResponse(
            analysis_id="test-stream-multi-456",
            result="Multi-sender streaming analysis",
            parameters={
                "sender_emails": ["user1@example.com", "user2@example.com"],
                "language": "en",
                "days": 14
            },
            timestamp=datetime.utcnow(),
            execution_time_seconds=60.5
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={
                    "sender_emails": "user1@example.com,user2@example.com",
                    "language": "en",
                    "days": 14
                }
            ) as response:
                assert response.status_code == 200
                
                # Verify streaming response
                event_text = "\n".join(response.iter_lines())
                assert "event: complete" in event_text
    
    def test_stream_progress_events_emitted(self):
        """Test that progress events are emitted during execution.
        
        Requirements: 3.2, 3.4
        """
        mock_response = GmailAnalysisResponse(
            analysis_id="test-progress-789",
            result="Analysis with progress tracking",
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.utcnow(),
            execution_time_seconds=30.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={"sender_emails": "test@example.com"}
            ) as response:
                events = []
                event_types = []
                
                current_event = None
                for line in response.iter_lines():
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                        event_types.append(current_event)
                    elif line.startswith("data:"):
                        data = line.split(":", 1)[1].strip()
                        events.append({"type": current_event, "data": data})
                
                # Verify at least one progress event
                assert "progress" in event_types
                
                # Verify complete event is last
                assert event_types[-1] == "complete"
    
    def test_stream_complete_event_contains_result(self):
        """Test that complete event contains full analysis result.
        
        Requirements: 3.5
        """
        mock_response = GmailAnalysisResponse(
            analysis_id="test-complete-abc",
            result="# Complete Analysis\n\nFull result with insights.",
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.utcnow(),
            execution_time_seconds=42.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={"sender_emails": "test@example.com"}
            ) as response:
                complete_data = None
                current_event = None
                
                for line in response.iter_lines():
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                    elif line.startswith("data:") and current_event == "complete":
                        data_str = line.split(":", 1)[1].strip()
                        complete_data = json.loads(data_str)
                        break
                
                # Verify complete event data
                assert complete_data is not None
                assert complete_data["analysis_id"] == "test-complete-abc"
                assert "Complete Analysis" in complete_data["result"]
                assert complete_data["parameters"]["language"] == "en"
                assert complete_data["execution_time_seconds"] == 42.0
    
    def test_stream_error_handling(self):
        """Test that error events are emitted when execution fails.
        
        Requirements: 3.4
        """
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.side_effect = Exception("Gmail API connection failed")
            
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={"sender_emails": "test@example.com"}
            ) as response:
                assert response.status_code == 200  # SSE always returns 200
                
                event_text = "\n".join(response.iter_lines())
                
                # Verify error event is present
                assert "event: error" in event_text
                assert "Gmail API connection failed" in event_text
    
    def test_stream_invalid_email_format(self):
        """Test SSE endpoint rejects invalid email format.
        
        Requirements: 3.3
        """
        response = client.get(
            "/api/flows/gmail-read/stream",
            params={
                "sender_emails": "not-an-email",
                "language": "en",
                "days": 7
            }
        )
        
        # Should return 400 before streaming starts
        assert response.status_code == 400
        data = response.json()
        # Global exception handler returns consistent format
        assert data["error"] == "ValidationError"
        assert "message" in data
    
    def test_stream_empty_sender_emails(self):
        """Test SSE endpoint rejects empty sender_emails.
        
        Requirements: 3.3
        """
        response = client.get(
            "/api/flows/gmail-read/stream",
            params={
                "sender_emails": "",
                "language": "en",
                "days": 7
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        # Global exception handler returns consistent format
        assert data["error"] == "ValidationError"
        assert "message" in data
    
    def test_stream_invalid_language_code(self):
        """Test SSE endpoint rejects invalid language code.
        
        Requirements: 3.3
        """
        response = client.get(
            "/api/flows/gmail-read/stream",
            params={
                "sender_emails": "test@example.com",
                "language": "invalid",
                "days": 7
            }
        )
        
        # Should fail pattern validation or Pydantic validation
        assert response.status_code in [400, 422]
    
    def test_stream_invalid_days_value(self):
        """Test SSE endpoint rejects invalid days value.
        
        Requirements: 3.3
        """
        response = client.get(
            "/api/flows/gmail-read/stream",
            params={
                "sender_emails": "test@example.com",
                "language": "en",
                "days": 0
            }
        )
        
        # API returns 400 with ValidationError format
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "ValidationError"
    
    def test_stream_days_exceeds_maximum(self):
        """Test SSE endpoint rejects days value greater than 365.
        
        Requirements: 3.3
        """
        response = client.get(
            "/api/flows/gmail-read/stream",
            params={
                "sender_emails": "test@example.com",
                "language": "en",
                "days": 366
            }
        )
        
        # API returns 400 with ValidationError format
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "ValidationError"
    
    def test_stream_default_values(self):
        """Test SSE endpoint applies default values for optional parameters.
        
        Requirements: 3.1, 3.3
        """
        mock_response = GmailAnalysisResponse(
            analysis_id="test-defaults-xyz",
            result="Analysis with defaults",
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.utcnow(),
            execution_time_seconds=35.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            # Only provide required parameter
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={"sender_emails": "test@example.com"}
            ) as response:
                assert response.status_code == 200
                
                # Verify defaults are applied in the result
                event_text = "\n".join(response.iter_lines())
                assert "event: complete" in event_text
    
    def test_stream_different_languages(self):
        """Test SSE endpoint with different language codes.
        
        Requirements: 3.1, 3.3
        """
        for lang_code in ["es", "fr", "de", "ru"]:
            mock_response = GmailAnalysisResponse(
                analysis_id=f"test-lang-{lang_code}",
                result=f"Analysis in {lang_code}",
                parameters={
                    "sender_emails": ["test@example.com"],
                    "language": lang_code,
                    "days": 7
                },
                timestamp=datetime.utcnow(),
                execution_time_seconds=40.0
            )
            
            with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
                mock_execute.return_value = mock_response
                
                with client.stream(
                    "GET",
                    "/api/flows/gmail-read/stream",
                    params={
                        "sender_emails": "test@example.com",
                        "language": lang_code
                    }
                ) as response:
                    assert response.status_code == 200
    
    def test_stream_sse_headers(self):
        """Test that SSE endpoint returns correct headers.
        
        Requirements: 3.1
        """
        mock_response = GmailAnalysisResponse(
            analysis_id="test-headers-123",
            result="Test headers",
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.utcnow(),
            execution_time_seconds=30.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={"sender_emails": "test@example.com"}
            ) as response:
                # Verify SSE-specific headers
                assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
                assert response.headers["cache-control"] == "no-cache"
                assert response.headers["connection"] == "keep-alive"
    
    def test_stream_comma_separated_emails(self):
        """Test SSE endpoint correctly parses comma-separated emails.
        
        Requirements: 3.3
        """
        mock_response = GmailAnalysisResponse(
            analysis_id="test-csv-emails",
            result="CSV email analysis",
            parameters={
                "sender_emails": ["a@example.com", "b@example.com", "c@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.utcnow(),
            execution_time_seconds=50.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={
                    "sender_emails": "a@example.com, b@example.com, c@example.com",
                    "language": "en",
                    "days": 7
                }
            ) as response:
                assert response.status_code == 200
                
                # Verify the request was processed
                event_text = "\n".join(response.iter_lines())
                assert "event: complete" in event_text
    
    def test_stream_whitespace_handling(self):
        """Test SSE endpoint handles whitespace in comma-separated emails.
        
        Requirements: 3.3
        """
        mock_response = GmailAnalysisResponse(
            analysis_id="test-whitespace",
            result="Whitespace handling test",
            parameters={
                "sender_emails": ["user1@example.com", "user2@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime.utcnow(),
            execution_time_seconds=40.0
        )
        
        with patch('api.services.flow_service.FlowService.execute_flow') as mock_execute:
            mock_execute.return_value = mock_response
            
            # Test with extra whitespace
            with client.stream(
                "GET",
                "/api/flows/gmail-read/stream",
                params={
                    "sender_emails": "  user1@example.com  ,  user2@example.com  ",
                    "language": "en",
                    "days": 7
                }
            ) as response:
                assert response.status_code == 200
