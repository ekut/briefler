"""Service for managing analysis history storage.

This module provides functionality for persisting Gmail analysis results
to JSON files and retrieving them with pagination support.
"""

import os
import json
import logging
from typing import List, Optional
from datetime import datetime

from api.models.responses import (
    GmailAnalysisResponse,
    HistoryItem,
    HistoryListResponse
)


logger = logging.getLogger(__name__)


class HistoryService:
    """Service for managing analysis history storage.
    
    Stores analysis results as JSON files in the configured storage directory.
    Provides methods for saving, retrieving, and managing analysis history
    with automatic cleanup to maintain storage limits.
    
    Attributes:
        storage_dir: Directory path for storing JSON files
        max_files: Maximum number of history files to retain
    """
    
    def __init__(
        self,
        storage_dir: str = "data/history",
        max_files: int = 100
    ):
        """Initialize the history service.
        
        Args:
            storage_dir: Directory path for storing JSON files
            max_files: Maximum number of history files to retain
        """
        self.storage_dir = storage_dir
        self.max_files = max_files
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        logger.info(f"History service initialized with storage_dir={storage_dir}")
    
    async def save(self, response: GmailAnalysisResponse) -> None:
        """Save analysis result to JSON file.
        
        Persists the analysis result to a JSON file named with the analysis ID.
        After saving, triggers cleanup to maintain the file limit.
        
        Args:
            response: The analysis response to persist
            
        Raises:
            OSError: If file write operation fails
        """
        file_path = os.path.join(
            self.storage_dir,
            f"{response.analysis_id}.json"
        )
        
        # Prepare data for JSON serialization
        data = {
            "analysis_id": response.analysis_id,
            "timestamp": response.timestamp.isoformat(),
            "parameters": response.parameters,
            "result": response.result,
            "execution_time_seconds": response.execution_time_seconds
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(
                f"Saved analysis {response.analysis_id} to {file_path}"
            )
            
            # Cleanup old files if exceeding limit
            await self._cleanup_old_files()
            
        except OSError as e:
            logger.error(
                f"Failed to save analysis {response.analysis_id}: {e}",
                exc_info=True
            )
            raise
    
    async def get_history(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> HistoryListResponse:
        """Get paginated list of past analyses.
        
        Retrieves analysis history sorted by modification time (newest first)
        with pagination support.
        
        Args:
            limit: Maximum number of items to return
            offset: Number of items to skip
            
        Returns:
            HistoryListResponse with paginated items and metadata
            
        Raises:
            OSError: If directory read or file read operations fail
        """
        try:
            # Get all JSON files sorted by modification time (newest first)
            files = sorted(
                [
                    f for f in os.listdir(self.storage_dir)
                    if f.endswith('.json')
                ],
                key=lambda x: os.path.getmtime(
                    os.path.join(self.storage_dir, x)
                ),
                reverse=True
            )
            
            total = len(files)
            paginated_files = files[offset:offset + limit]
            
            items = []
            for filename in paginated_files:
                file_path = os.path.join(self.storage_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Create preview (first 200 chars)
                    result_text = data["result"]
                    preview = (
                        result_text[:200] + "..."
                        if len(result_text) > 200
                        else result_text
                    )
                    
                    items.append(HistoryItem(
                        analysis_id=data["analysis_id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        sender_count=len(data["parameters"]["sender_emails"]),
                        language=data["parameters"]["language"],
                        days=data["parameters"]["days"],
                        preview=preview
                    ))
                    
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(
                        f"Skipping malformed history file {filename}: {e}"
                    )
                    continue
            
            logger.info(
                f"Retrieved {len(items)} history items "
                f"(total={total}, limit={limit}, offset={offset})"
            )
            
            return HistoryListResponse(
                items=items,
                total=total,
                limit=limit,
                offset=offset
            )
            
        except OSError as e:
            logger.error(
                f"Failed to retrieve history: {e}",
                exc_info=True
            )
            raise
    
    async def get_by_id(
        self,
        analysis_id: str
    ) -> Optional[GmailAnalysisResponse]:
        """Get specific analysis by ID.
        
        Retrieves a single analysis result by its unique identifier.
        
        Args:
            analysis_id: The unique identifier of the analysis
            
        Returns:
            GmailAnalysisResponse if found, None otherwise
            
        Raises:
            OSError: If file read operation fails
            json.JSONDecodeError: If JSON parsing fails
        """
        file_path = os.path.join(self.storage_dir, f"{analysis_id}.json")
        
        if not os.path.exists(file_path):
            logger.info(f"Analysis {analysis_id} not found")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Retrieved analysis {analysis_id}")
            
            return GmailAnalysisResponse(
                analysis_id=data["analysis_id"],
                result=data["result"],
                parameters=data["parameters"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                execution_time_seconds=data["execution_time_seconds"]
            )
            
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error(
                f"Failed to retrieve analysis {analysis_id}: {e}",
                exc_info=True
            )
            raise
    
    async def _cleanup_old_files(self) -> None:
        """Remove oldest files if exceeding limit.
        
        Maintains the maximum file limit by removing the oldest files
        when the total count exceeds max_files.
        
        Raises:
            OSError: If file deletion fails
        """
        try:
            # Get all JSON files sorted by modification time (newest first)
            files = sorted(
                [
                    f for f in os.listdir(self.storage_dir)
                    if f.endswith('.json')
                ],
                key=lambda x: os.path.getmtime(
                    os.path.join(self.storage_dir, x)
                ),
                reverse=True
            )
            
            # Remove files exceeding the limit
            if len(files) > self.max_files:
                files_to_remove = files[self.max_files:]
                
                for filename in files_to_remove:
                    file_path = os.path.join(self.storage_dir, filename)
                    os.remove(file_path)
                    logger.info(f"Removed old history file: {filename}")
                
                logger.info(
                    f"Cleaned up {len(files_to_remove)} old history files"
                )
                
        except OSError as e:
            logger.error(
                f"Failed to cleanup old files: {e}",
                exc_info=True
            )
            raise
