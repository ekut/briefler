"""Shared test fixtures and configuration for pytest.

Note: sys.path configuration is handled by pythonpath setting in pyproject.toml
"""

import pytest
import os


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set test environment
    os.environ["ENVIRONMENT"] = "development"
    
    # Mock credentials paths to avoid requiring actual Gmail credentials
    os.environ.setdefault("GMAIL_CREDENTIALS_PATH", "/tmp/test_credentials.json")
    os.environ.setdefault("GMAIL_TOKEN_PATH", "/tmp/test_token.json")
    os.environ.setdefault("OPENAI_API_KEY", "test-key-123")
    
    yield
    
    # Cleanup is handled automatically by pytest
