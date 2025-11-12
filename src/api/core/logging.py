"""Logging configuration for the API server.

Configures Python logging with appropriate format, log levels based on environment,
and request/response logging middleware for FastAPI.
"""

import logging
import sys
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from api.core.config import settings


# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """Configure Python logging with appropriate format and log levels.
    
    Sets log level based on ENVIRONMENT setting:
    - development: DEBUG level for detailed logging
    - production: INFO level for standard logging
    
    Configures console handler with formatted output.
    """
    # Determine log level based on environment
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for third-party libraries to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level set to: {logging.getLevelName(log_level)}")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses.
    
    Logs:
    - Request method, path, and query parameters
    - Response status code
    - Request processing time
    - Client IP address
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response: HTTP response from handler
        """
        logger = logging.getLogger("api.requests")
        
        # Record start time
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        client_ip = request.client.host if request.client else "unknown"
        
        # Log incoming request
        logger.info(
            f"Request started: {method} {path} "
            f"{f'?{query_params}' if query_params else ''} "
            f"from {client_ip}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {method} {path} "
                f"status={response.status_code} "
                f"duration={process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {method} {path} "
                f"error={str(e)} "
                f"duration={process_time:.3f}s",
                exc_info=True
            )
            raise


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)

