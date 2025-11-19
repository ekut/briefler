"""Service for managing CrewAI Flow execution.

This module provides functionality for orchestrating the GmailReadFlow
execution, capturing metrics, and persisting results to history.
"""

import uuid
import time
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator
import json

from api.models.requests import GmailAnalysisRequest
from api.models.responses import GmailAnalysisResponse
from briefler.flows.gmail_read_flow import GmailReadFlow
from api.services.history_service import HistoryService


logger = logging.getLogger(__name__)

# Thread pool for running synchronous CrewAI code
_executor = ThreadPoolExecutor(max_workers=4)


class FlowService:
    """Service for managing CrewAI Flow execution.
    
    Orchestrates the execution of GmailReadFlow, handles state management,
    captures execution metrics, and persists results to history storage.
    
    Attributes:
        history_service: Service for persisting analysis results
    """
    
    def __init__(self, history_service: HistoryService = None):
        """Initialize the flow service.
        
        Args:
            history_service: Optional history service instance.
                           If not provided, creates a new instance.
        """
        self.history_service = history_service or HistoryService()
        logger.info("Flow service initialized")
    
    @staticmethod
    def _execute_flow_sync(trigger_payload: dict) -> GmailReadFlow:
        """Execute CrewAI flow synchronously in a separate thread.
        
        This method runs in a thread pool to avoid conflicts with FastAPI's
        async event loop, since CrewAI uses asyncio.run() internally.
        
        Args:
            trigger_payload: Flow input parameters
            
        Returns:
            The flow instance with populated state after execution
        """
        flow = GmailReadFlow()
        flow.kickoff(inputs={"crewai_trigger_payload": trigger_payload})
        return flow
    
    async def execute_flow(
        self,
        request: GmailAnalysisRequest
    ) -> GmailAnalysisResponse:
        """Execute Gmail Read Flow synchronously.
        
        Orchestrates the complete flow execution including:
        - Generating unique analysis ID
        - Preparing trigger payload
        - Executing the flow
        - Capturing execution metrics
        - Persisting results to history
        
        Args:
            request: The analysis request with sender emails, language, and days
            
        Returns:
            GmailAnalysisResponse with analysis results and metadata
            
        Raises:
            ValueError: If flow execution fails due to invalid parameters
            Exception: If flow execution encounters unexpected errors
        """
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        logger.info(
            f"Starting flow execution {analysis_id} for "
            f"{len(request.sender_emails)} sender(s)"
        )
        
        # Capture start time for metrics
        start_time = time.time()
        
        try:
            # Prepare trigger payload for flow
            trigger_payload = {
                "sender_emails": request.sender_emails,
                "language": request.language,
                "days": request.days
            }
            
            logger.debug(f"Trigger payload: {trigger_payload}")
            
            # Execute flow in thread pool to avoid event loop conflicts
            # CrewAI uses asyncio.run() internally which conflicts with FastAPI's event loop
            flow = await asyncio.get_event_loop().run_in_executor(
                _executor,
                self._execute_flow_sync,
                trigger_payload
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            logger.info(
                f"Flow execution {analysis_id} completed in "
                f"{execution_time:.2f} seconds"
            )
            
            # Prepare response data dictionary
            response_data = {
                "analysis_id": analysis_id,
                "result": flow.state.result,
                "parameters": trigger_payload,
                "execution_time_seconds": round(execution_time, 2)
            }
            
            # Add structured_result if available
            if flow.state.structured_result:
                try:
                    # Use mode='json' to properly serialize datetime objects
                    response_data["structured_result"] = flow.state.structured_result.model_dump(mode='json')
                    logger.debug("Successfully serialized structured_result")
                except TypeError as e:
                    logger.warning(
                        f"Type error serializing structured_result for analysis {analysis_id}: {e}. "
                        f"Model type: {type(flow.state.structured_result).__name__}",
                        exc_info=False
                    )
                except AttributeError as e:
                    logger.warning(
                        f"Attribute error serializing structured_result for analysis {analysis_id}: {e}. "
                        f"Object may not be a Pydantic model",
                        exc_info=False
                    )
                except Exception as e:
                    logger.warning(
                        f"Unexpected error serializing structured_result for analysis {analysis_id}: {e}",
                        exc_info=True
                    )
            
            # Add token_usage if available
            if flow.state.total_token_usage:
                try:
                    # Use mode='json' for consistency
                    response_data["token_usage"] = flow.state.total_token_usage.model_dump(mode='json')
                    logger.debug("Successfully serialized token_usage")
                except TypeError as e:
                    logger.warning(
                        f"Type error serializing token_usage for analysis {analysis_id}: {e}. "
                        f"Model type: {type(flow.state.total_token_usage).__name__}",
                        exc_info=False
                    )
                except AttributeError as e:
                    logger.warning(
                        f"Attribute error serializing token_usage for analysis {analysis_id}: {e}. "
                        f"Object may not be a Pydantic model",
                        exc_info=False
                    )
                except Exception as e:
                    logger.warning(
                        f"Unexpected error serializing token_usage for analysis {analysis_id}: {e}",
                        exc_info=True
                    )
            
            # Create response object
            response = GmailAnalysisResponse(**response_data)
            
            # Save to history
            await self.history_service.save(response)
            
            return response
            
        except ValueError as e:
            logger.error(
                f"Flow execution {analysis_id} failed with validation error: {e}",
                exc_info=True
            )
            raise
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Flow execution {analysis_id} failed after "
                f"{execution_time:.2f} seconds: {e}",
                exc_info=True
            )
            raise
    
    async def execute_flow_stream(
        self,
        request: GmailAnalysisRequest
    ) -> AsyncGenerator[str, None]:
        """Execute Gmail Read Flow with SSE progress updates.
        
        Executes the flow and streams progress events using Server-Sent Events
        format. Emits progress, complete, and error events.
        
        Args:
            request: The analysis request with sender emails, language, and days
            
        Yields:
            SSE-formatted event strings with progress updates
            
        Event Types:
            - progress: Status updates during execution
            - complete: Final result with full analysis data
            - error: Error information if execution fails
        """
        analysis_id = str(uuid.uuid4())
        
        try:
            logger.info(
                f"Starting streaming flow execution {analysis_id} for "
                f"{len(request.sender_emails)} sender(s)"
            )
            
            # Send initial progress event
            yield f"event: progress\ndata: {{\"status\": \"Initializing analysis...\", \"analysis_id\": \"{analysis_id}\"}}\n\n"
            
            # Send progress event for flow execution
            yield f"event: progress\ndata: {{\"status\": \"Executing Gmail Read Flow...\", \"analysis_id\": \"{analysis_id}\"}}\n\n"
            
            # Execute flow
            result = await self.execute_flow(request)
            
            # Prepare completion data
            completion_data = {
                "analysis_id": result.analysis_id,
                "result": result.result,
                "parameters": result.parameters,
                "timestamp": result.timestamp.isoformat(),
                "execution_time_seconds": result.execution_time_seconds
            }
            
            # Add structured_result if available
            if result.structured_result:
                try:
                    completion_data["structured_result"] = result.structured_result
                except Exception as e:
                    logger.warning(
                        f"Could not include structured_result in streaming response "
                        f"for analysis {result.analysis_id}: {e}",
                        exc_info=False
                    )
            
            # Add token_usage if available
            if result.token_usage:
                try:
                    completion_data["token_usage"] = result.token_usage
                except Exception as e:
                    logger.warning(
                        f"Could not include token_usage in streaming response "
                        f"for analysis {result.analysis_id}: {e}",
                        exc_info=False
                    )
            
            # Send completion event with full result
            try:
                result_json = json.dumps(completion_data)
            except TypeError as e:
                logger.error(
                    f"JSON serialization error for streaming response "
                    f"for analysis {result.analysis_id}: {e}. "
                    f"Falling back to minimal response",
                    exc_info=True
                )
                # Fallback to minimal response without structured data
                minimal_data = {
                    "analysis_id": result.analysis_id,
                    "result": result.result,
                    "parameters": result.parameters,
                    "timestamp": result.timestamp.isoformat(),
                    "execution_time_seconds": result.execution_time_seconds
                }
                result_json = json.dumps(minimal_data)
            
            yield f"event: complete\ndata: {result_json}\n\n"
            
            logger.info(f"Streaming flow execution {analysis_id} completed")
            
        except Exception as e:
            logger.error(
                f"Streaming flow execution {analysis_id} failed: {e}",
                exc_info=True
            )
            
            # Send error event
            error_data = json.dumps({
                "error": type(e).__name__,
                "message": str(e),
                "analysis_id": analysis_id
            })
            
            yield f"event: error\ndata: {error_data}\n\n"
