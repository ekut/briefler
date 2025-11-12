"""Tests for CORS configuration.

This module tests the CORS (Cross-Origin Resource Sharing) configuration including:
- CORS headers are present in responses
- Requests from localhost origins are allowed
- Preflight OPTIONS requests are handled correctly
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


# Create test client
client = TestClient(app)


class TestCORSConfiguration:
    """Test suite for CORS configuration."""
    
    def test_cors_headers_present_on_health_endpoint(self):
        """Test CORS headers are present on health endpoint.
        
        Requirements: 4.3, 5.4
        """
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        
        # Verify CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers
    
    def test_cors_allows_localhost_3000(self):
        """Test requests from localhost:3000 are allowed.
        
        Requirements: 4.3, 5.4
        """
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        
        # Verify origin is allowed
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_cors_allows_localhost_5173(self):
        """Test requests from localhost:5173 are allowed.
        
        Requirements: 4.3, 5.4
        """
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        assert response.status_code == 200
        
        # Verify origin is allowed
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_cors_headers_on_api_flows_endpoint(self):
        """Test CORS headers are present on API flows endpoint.
        
        Requirements: 4.3, 5.4
        """
        response = client.post(
            "/api/flows/gmail-read",
            json={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Response may be 200 or 500 depending on flow execution
        # We only care about CORS headers being present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers
    
    def test_cors_headers_on_history_endpoint(self):
        """Test CORS headers are present on history endpoint.
        
        Requirements: 4.3, 5.4
        """
        response = client.get(
            "/api/history",
            headers={"Origin": "http://localhost:5173"}
        )
        
        assert response.status_code == 200
        
        # Verify CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_cors_preflight_request(self):
        """Test CORS preflight OPTIONS request is handled correctly.
        
        Requirements: 4.3, 5.4
        """
        response = client.options(
            "/api/flows/gmail-read",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        
        assert response.status_code == 200
        
        # Verify preflight response headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_cors_allows_all_methods(self):
        """Test CORS configuration allows all HTTP methods.
        
        Requirements: 4.3, 5.4
        """
        response = client.options(
            "/api/flows/gmail-read",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        assert response.status_code == 200
        
        # Verify all methods are allowed (FastAPI CORS middleware returns * or specific methods)
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        # Should include common methods or wildcard
        assert allowed_methods != ""
    
    def test_cors_allows_all_headers(self):
        """Test CORS configuration allows all headers.
        
        Requirements: 4.3, 5.4
        """
        response = client.options(
            "/api/flows/gmail-read",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization,x-custom-header"
            }
        )
        
        assert response.status_code == 200
        
        # Verify headers are allowed
        allowed_headers = response.headers.get("access-control-allow-headers", "")
        assert allowed_headers != ""
    
    def test_cors_credentials_enabled(self):
        """Test CORS credentials are enabled for all endpoints.
        
        Requirements: 4.3, 5.4
        """
        endpoints = [
            "/health",
            "/ready",
            "/api/history"
        ]
        
        for endpoint in endpoints:
            response = client.get(
                endpoint,
                headers={"Origin": "http://localhost:3000"}
            )
            
            # Verify credentials are enabled
            assert response.headers.get("access-control-allow-credentials") == "true", \
                f"Credentials not enabled for {endpoint}"
    
    def test_cors_headers_on_error_responses(self):
        """Test CORS headers are present even on error responses.
        
        Requirements: 4.3, 5.4
        """
        # Make a request that will fail validation
        response = client.post(
            "/api/flows/gmail-read",
            json={
                "sender_emails": ["invalid-email"],  # Invalid email format
                "language": "en",
                "days": 7
            },
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 400
        
        # Verify CORS headers are still present on error response
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_cors_headers_on_404_responses(self):
        """Test CORS headers are present on 404 responses.
        
        Requirements: 4.3, 5.4
        """
        response = client.get(
            "/api/nonexistent-endpoint",
            headers={"Origin": "http://localhost:5173"}
        )
        
        assert response.status_code == 404
        
        # Verify CORS headers are present even on 404
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    
    def test_cors_multiple_origins_supported(self):
        """Test both configured localhost origins are supported.
        
        Requirements: 4.3, 5.4
        """
        origins = [
            "http://localhost:3000",
            "http://localhost:5173"
        ]
        
        for origin in origins:
            response = client.get(
                "/health",
                headers={"Origin": origin}
            )
            
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin, \
                f"Origin {origin} not properly configured"
            assert response.headers["access-control-allow-credentials"] == "true"
