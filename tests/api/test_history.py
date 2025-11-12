"""Tests for history API endpoints.

This module tests the history endpoints including:
- GET /api/history with pagination
- GET /api/history/{analysis_id}
- 404 handling for non-existent analyses
- History limit enforcement
"""

import pytest
import os
import json
import tempfile
import shutil
from fastapi.testclient import TestClient
from datetime import datetime
from pathlib import Path

from api.main import app
from api.models.responses import GmailAnalysisResponse
from api.services.history_service import HistoryService


# Create test client
client = TestClient(app)


class TestHistoryEndpoints:
    """Test suite for history API endpoints."""
    
    @pytest.fixture
    def temp_history_dir(self):
        """Create a temporary directory for history storage."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def history_service_with_temp_dir(self, temp_history_dir):
        """Create a history service with temporary storage."""
        return HistoryService(storage_dir=temp_history_dir, max_files=100)
    
    @pytest.fixture
    async def sample_analyses(self, history_service_with_temp_dir):
        """Create sample analysis files for testing."""
        analyses = []
        
        for i in range(5):
            response = GmailAnalysisResponse(
                analysis_id=f"test-uuid-{i}",
                result=f"Analysis result {i} with some content that is longer than 200 characters to test the preview functionality. " * 3,
                parameters={
                    "sender_emails": [f"user{i}@example.com"],
                    "language": "en",
                    "days": 7 + i
                },
                timestamp=datetime(2025, 11, 12, 10, i, 0),
                execution_time_seconds=40.0 + i
            )
            await history_service_with_temp_dir.save(response)
            analyses.append(response)
        
        return analyses, history_service_with_temp_dir
    
    def test_get_history_empty(self, temp_history_dir, monkeypatch):
        """Test GET /api/history returns empty list when no history exists.
        
        Requirements: 6.2
        """
        # Patch the history service to use temp directory
        monkeypatch.setattr(
            'api.routes.history.history_service.storage_dir',
            temp_history_dir
        )
        
        response = client.get("/api/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 20
        assert data["offset"] == 0
    
    @pytest.mark.asyncio
    async def test_get_history_with_items(self, sample_analyses):
        """Test GET /api/history returns list of analyses.
        
        Requirements: 6.2
        """
        analyses, service = sample_analyses
        
        # Get history from service directly
        result = await service.get_history(limit=20, offset=0)
        
        assert result.total == 5
        assert len(result.items) == 5
        assert result.limit == 20
        assert result.offset == 0
        
        # Verify items are sorted by timestamp (newest first)
        for i in range(len(result.items) - 1):
            assert result.items[i].timestamp >= result.items[i + 1].timestamp
        
        # Verify item structure
        first_item = result.items[0]
        assert hasattr(first_item, 'analysis_id')
        assert hasattr(first_item, 'timestamp')
        assert hasattr(first_item, 'sender_count')
        assert hasattr(first_item, 'language')
        assert hasattr(first_item, 'days')
        assert hasattr(first_item, 'preview')
        
        # Verify preview is truncated
        assert len(first_item.preview) <= 203  # 200 chars + "..."
    
    @pytest.mark.asyncio
    async def test_get_history_pagination_limit(self, sample_analyses):
        """Test GET /api/history respects limit parameter.
        
        Requirements: 6.2
        """
        analyses, service = sample_analyses
        
        # Request only 2 items
        result = await service.get_history(limit=2, offset=0)
        
        assert result.total == 5
        assert len(result.items) == 2
        assert result.limit == 2
        assert result.offset == 0
    
    @pytest.mark.asyncio
    async def test_get_history_pagination_offset(self, sample_analyses):
        """Test GET /api/history respects offset parameter.
        
        Requirements: 6.2
        """
        analyses, service = sample_analyses
        
        # Get first page
        page1 = await service.get_history(limit=2, offset=0)
        # Get second page
        page2 = await service.get_history(limit=2, offset=2)
        
        assert page1.total == 5
        assert page2.total == 5
        assert len(page1.items) == 2
        assert len(page2.items) == 2
        
        # Verify different items
        assert page1.items[0].analysis_id != page2.items[0].analysis_id
    
    @pytest.mark.asyncio
    async def test_get_history_pagination_beyond_total(self, sample_analyses):
        """Test GET /api/history with offset beyond total returns empty.
        
        Requirements: 6.2
        """
        analyses, service = sample_analyses
        
        # Request items beyond available
        result = await service.get_history(limit=10, offset=10)
        
        assert result.total == 5
        assert len(result.items) == 0
        assert result.limit == 10
        assert result.offset == 10
    
    def test_get_history_default_pagination(self, temp_history_dir, monkeypatch):
        """Test GET /api/history uses default pagination values.
        
        Requirements: 6.2
        """
        monkeypatch.setattr(
            'api.routes.history.history_service.storage_dir',
            temp_history_dir
        )
        
        response = client.get("/api/history")
        
        assert response.status_code == 200
        data = response.json()
        
        # Default values
        assert data["limit"] == 20
        assert data["offset"] == 0
    
    def test_get_history_custom_pagination(self, temp_history_dir, monkeypatch):
        """Test GET /api/history with custom pagination parameters.
        
        Requirements: 6.2
        """
        monkeypatch.setattr(
            'api.routes.history.history_service.storage_dir',
            temp_history_dir
        )
        
        response = client.get("/api/history?limit=5&offset=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 5
        assert data["offset"] == 10
    
    def test_get_history_invalid_limit_negative(self):
        """Test GET /api/history rejects negative limit.
        
        Requirements: 6.2
        """
        response = client.get("/api/history?limit=-1")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_history_invalid_limit_zero(self):
        """Test GET /api/history rejects zero limit.
        
        Requirements: 6.2
        """
        response = client.get("/api/history?limit=0")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_history_invalid_limit_exceeds_max(self):
        """Test GET /api/history rejects limit > 100.
        
        Requirements: 6.2
        """
        response = client.get("/api/history?limit=101")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_history_invalid_offset_negative(self):
        """Test GET /api/history rejects negative offset.
        
        Requirements: 6.2
        """
        response = client.get("/api/history?offset=-1")
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_get_analysis_by_id_success(self, sample_analyses):
        """Test GET /api/history/{analysis_id} returns specific analysis.
        
        Requirements: 6.3
        """
        analyses, service = sample_analyses
        
        # Get first analysis
        analysis_id = analyses[0].analysis_id
        result = await service.get_by_id(analysis_id)
        
        assert result is not None
        assert result.analysis_id == analysis_id
        assert result.result == analyses[0].result
        assert result.parameters == analyses[0].parameters
        assert result.execution_time_seconds == analyses[0].execution_time_seconds
    
    @pytest.mark.asyncio
    async def test_get_analysis_by_id_not_found(self, sample_analyses):
        """Test GET /api/history/{analysis_id} returns None for non-existent ID.
        
        Requirements: 6.3
        """
        analyses, service = sample_analyses
        
        # Try to get non-existent analysis
        result = await service.get_by_id("non-existent-uuid")
        
        assert result is None
    
    def test_get_analysis_by_id_endpoint_not_found(self, temp_history_dir, monkeypatch):
        """Test GET /api/history/{analysis_id} endpoint returns 404.
        
        Requirements: 6.3
        """
        monkeypatch.setattr(
            'api.routes.history.history_service.storage_dir',
            temp_history_dir
        )
        
        response = client.get("/api/history/non-existent-uuid")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_analysis_by_id_full_content(self, sample_analyses):
        """Test GET /api/history/{analysis_id} returns full result text.
        
        Requirements: 6.3
        """
        analyses, service = sample_analyses
        
        analysis_id = analyses[0].analysis_id
        result = await service.get_by_id(analysis_id)
        
        # Verify full content is returned (not truncated like preview)
        assert len(result.result) > 200
        assert result.result == analyses[0].result
    
    @pytest.mark.asyncio
    async def test_history_limit_enforcement(self, temp_history_dir):
        """Test history service enforces 100 file limit.
        
        Requirements: 6.5
        """
        # Create service with low limit for testing
        service = HistoryService(storage_dir=temp_history_dir, max_files=10)
        
        # Create 15 analyses
        for i in range(15):
            response = GmailAnalysisResponse(
                analysis_id=f"test-uuid-{i}",
                result=f"Analysis result {i}",
                parameters={
                    "sender_emails": [f"user{i}@example.com"],
                    "language": "en",
                    "days": 7
                },
                timestamp=datetime(2025, 11, 12, 10, i, 0),
                execution_time_seconds=40.0
            )
            await service.save(response)
        
        # Verify only 10 files remain
        files = [f for f in os.listdir(temp_history_dir) if f.endswith('.json')]
        assert len(files) == 10
        
        # Verify oldest files were removed (0-4 should be gone, 5-14 should remain)
        remaining_ids = [f.replace('.json', '') for f in files]
        for i in range(5):
            assert f"test-uuid-{i}" not in remaining_ids
        for i in range(5, 15):
            assert f"test-uuid-{i}" in remaining_ids
    
    @pytest.mark.asyncio
    async def test_history_limit_default_100(self, temp_history_dir):
        """Test history service uses default limit of 100.
        
        Requirements: 6.5
        """
        service = HistoryService(storage_dir=temp_history_dir)
        
        assert service.max_files == 100
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_cycle(self, temp_history_dir):
        """Test complete save and retrieve cycle.
        
        Requirements: 6.1, 6.2, 6.3
        """
        service = HistoryService(storage_dir=temp_history_dir)
        
        # Save an analysis
        response = GmailAnalysisResponse(
            analysis_id="test-cycle-uuid",
            result="Test analysis result for save/retrieve cycle",
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime(2025, 11, 12, 10, 30, 0),
            execution_time_seconds=45.5
        )
        await service.save(response)
        
        # Retrieve via get_history
        history = await service.get_history(limit=10, offset=0)
        assert history.total == 1
        assert len(history.items) == 1
        assert history.items[0].analysis_id == "test-cycle-uuid"
        
        # Retrieve via get_by_id
        retrieved = await service.get_by_id("test-cycle-uuid")
        assert retrieved is not None
        assert retrieved.analysis_id == "test-cycle-uuid"
        assert retrieved.result == response.result
        assert retrieved.parameters == response.parameters
    
    @pytest.mark.asyncio
    async def test_history_metadata_accuracy(self, sample_analyses):
        """Test history items contain accurate metadata.
        
        Requirements: 6.2
        """
        analyses, service = sample_analyses
        
        result = await service.get_history(limit=20, offset=0)
        
        for item in result.items:
            # Find corresponding original analysis
            original = next(
                (a for a in analyses if a.analysis_id == item.analysis_id),
                None
            )
            assert original is not None
            
            # Verify metadata
            assert item.sender_count == len(original.parameters["sender_emails"])
            assert item.language == original.parameters["language"]
            assert item.days == original.parameters["days"]
            assert item.timestamp == original.timestamp
    
    @pytest.mark.asyncio
    async def test_preview_truncation(self, temp_history_dir):
        """Test preview is truncated to 200 characters.
        
        Requirements: 6.2
        """
        service = HistoryService(storage_dir=temp_history_dir)
        
        # Create analysis with long result
        long_result = "A" * 500
        response = GmailAnalysisResponse(
            analysis_id="test-preview-uuid",
            result=long_result,
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime(2025, 11, 12, 10, 30, 0),
            execution_time_seconds=40.0
        )
        await service.save(response)
        
        # Get history
        history = await service.get_history(limit=10, offset=0)
        
        assert len(history.items) == 1
        preview = history.items[0].preview
        
        # Preview should be 200 chars + "..."
        assert len(preview) == 203
        assert preview.endswith("...")
        assert preview[:200] == "A" * 200
    
    @pytest.mark.asyncio
    async def test_preview_no_truncation_short_text(self, temp_history_dir):
        """Test preview is not truncated for short text.
        
        Requirements: 6.2
        """
        service = HistoryService(storage_dir=temp_history_dir)
        
        # Create analysis with short result
        short_result = "Short analysis result"
        response = GmailAnalysisResponse(
            analysis_id="test-short-uuid",
            result=short_result,
            parameters={
                "sender_emails": ["test@example.com"],
                "language": "en",
                "days": 7
            },
            timestamp=datetime(2025, 11, 12, 10, 30, 0),
            execution_time_seconds=40.0
        )
        await service.save(response)
        
        # Get history
        history = await service.get_history(limit=10, offset=0)
        
        assert len(history.items) == 1
        preview = history.items[0].preview
        
        # Preview should be the full text without "..."
        assert preview == short_result
        assert not preview.endswith("...")
