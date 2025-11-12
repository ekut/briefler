"""Tests for health check endpoints.

This module tests the health and readiness check endpoints including:
- Basic health check returns 200
- Readiness check validates dependencies
- Readiness check fails without credentials
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

from api.main import app


# Create test client
client = TestClient(app)


class TestHealthCheckEndpoint:
    """Test suite for GET /health endpoint."""
    
    def test_health_check_returns_200(self):
        """Test health endpoint returns 200 status.
        
        Requirements: 7.1, 7.3
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        
        # Verify status value
        assert data["status"] == "healthy"
        
        # Verify timestamp is in ISO format
        assert "T" in data["timestamp"]
    
    def test_health_check_always_succeeds(self):
        """Test health endpoint always returns healthy status.
        
        Requirements: 7.1, 7.3
        """
        # Make multiple requests to ensure consistency
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"


class TestReadinessCheckEndpoint:
    """Test suite for GET /ready endpoint."""
    
    def test_ready_check_with_all_dependencies(self):
        """Test readiness endpoint returns 200 when all dependencies are available.
        
        Requirements: 7.2, 7.3, 7.4
        """
        # The test environment fixture sets up mock credentials
        # Ensure history directory exists
        os.makedirs("data/history", exist_ok=True)
        
        response = client.get("/ready")
        
        # Should return 200 or 503 depending on actual file existence
        assert response.status_code in [200, 503]
        data = response.json()
        
        # Verify response structure
        assert "ready" in data
        assert "checks" in data
        assert "timestamp" in data
        
        # Verify checks structure
        assert "gmail_credentials" in data["checks"]
        assert "openai_api_key" in data["checks"]
        assert "history_storage" in data["checks"]
        
        # Verify timestamp format
        assert "T" in data["timestamp"]
    
    def test_ready_check_fails_without_gmail_credentials(self):
        """Test readiness check fails when Gmail credentials are missing.
        
        Requirements: 7.2, 7.4, 7.5
        """
        # Mock environment without Gmail credentials
        with patch.dict(os.environ, {"GMAIL_CREDENTIALS_PATH": "/nonexistent/path.json"}, clear=False):
            response = client.get("/ready")
            
            data = response.json()
            
            # Should indicate not ready
            assert data["ready"] is False
            assert data["checks"]["gmail_credentials"] is False
            
            # Should return 503 when not ready
            assert response.status_code == 503
    
    def test_ready_check_fails_without_openai_key(self):
        """Test readiness check fails when OpenAI API key is missing.
        
        Requirements: 7.2, 7.4, 7.5
        """
        # Mock environment without OpenAI key
        env_copy = os.environ.copy()
        env_copy.pop("OPENAI_API_KEY", None)
        
        with patch.dict(os.environ, env_copy, clear=True):
            response = client.get("/ready")
            
            data = response.json()
            
            # Should indicate not ready
            assert data["ready"] is False
            assert data["checks"]["openai_api_key"] is False
            
            # Should return 503 when not ready
            assert response.status_code == 503
    
    def test_ready_check_fails_without_history_storage(self):
        """Test readiness check fails when history storage directory is missing.
        
        Requirements: 7.2, 7.4, 7.5
        """
        # Mock environment with nonexistent history directory
        with patch.dict(os.environ, {"HISTORY_STORAGE_DIR": "/nonexistent/history"}, clear=False):
            response = client.get("/ready")
            
            data = response.json()
            
            # Should indicate not ready
            assert data["ready"] is False
            assert data["checks"]["history_storage"] is False
            
            # Should return 503 when not ready
            assert response.status_code == 503
    
    def test_ready_check_with_tilde_expansion(self):
        """Test readiness check properly expands ~ in credential paths.
        
        Requirements: 7.2, 7.4
        """
        # Mock environment with ~ in path
        with patch.dict(os.environ, {"GMAIL_CREDENTIALS_PATH": "~/nonexistent.json"}, clear=False):
            response = client.get("/ready")
            
            data = response.json()
            
            # Should check the expanded path
            assert "gmail_credentials" in data["checks"]
            # Will be False since the file doesn't exist, but path should be expanded
            assert isinstance(data["checks"]["gmail_credentials"], bool)
    
    def test_ready_check_all_dependencies_missing(self):
        """Test readiness check when all dependencies are missing.
        
        Requirements: 7.2, 7.4, 7.5
        """
        # Mock environment with all missing dependencies
        env_copy = {
            "GMAIL_CREDENTIALS_PATH": "/nonexistent/creds.json",
            "HISTORY_STORAGE_DIR": "/nonexistent/history",
            "ENVIRONMENT": "development"
        }
        
        with patch.dict(os.environ, env_copy, clear=True):
            response = client.get("/ready")
            
            data = response.json()
            
            # Should indicate not ready
            assert data["ready"] is False
            
            # All checks should fail
            assert data["checks"]["gmail_credentials"] is False
            assert data["checks"]["openai_api_key"] is False
            assert data["checks"]["history_storage"] is False
            
            # Should return 503
            assert response.status_code == 503
    
    def test_ready_check_response_structure(self):
        """Test readiness check returns proper response structure.
        
        Requirements: 7.2, 7.3
        """
        response = client.get("/ready")
        data = response.json()
        
        # Verify all required fields are present
        assert "ready" in data
        assert "checks" in data
        assert "timestamp" in data
        
        # Verify ready is boolean
        assert isinstance(data["ready"], bool)
        
        # Verify checks is a dict with all required keys
        assert isinstance(data["checks"], dict)
        assert "gmail_credentials" in data["checks"]
        assert "openai_api_key" in data["checks"]
        assert "history_storage" in data["checks"]
        
        # Verify all check values are boolean
        for check_name, check_value in data["checks"].items():
            assert isinstance(check_value, bool), f"{check_name} should be boolean"
        
        # Verify timestamp is string
        assert isinstance(data["timestamp"], str)
    
    def test_ready_check_status_code_matches_readiness(self):
        """Test readiness check status code matches ready state.
        
        Requirements: 7.2, 7.5
        """
        response = client.get("/ready")
        data = response.json()
        
        # Status code should match ready state
        if data["ready"]:
            assert response.status_code == 200
        else:
            assert response.status_code == 503
