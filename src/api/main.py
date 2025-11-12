"""FastAPI application entry point for Briefler API.

This module initializes the FastAPI application, configures middleware,
registers routers, and sets up global exception handlers.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from api.core.config import settings
from api.routes import flows, history, health


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Initialize FastAPI application
app = FastAPI(
    title="Briefler API",
    description=(
        "REST API for Gmail analysis using CrewAI. "
        "Provides endpoints for executing email analysis flows, "
        "retrieving analysis history, and monitoring service health."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS middleware for localhost development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(
    flows.router,
    prefix="/api/flows",
    tags=["flows"]
)

app.include_router(
    history.router,
    prefix="/api/history",
    tags=["history"]
)

app.include_router(
    health.router,
    tags=["health"]
)


# Global exception handlers

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.
    
    Catches validation errors from request body/query parameter validation
    and returns a structured error response with field-level details.
    
    Args:
        request: The incoming request that failed validation
        exc: The validation exception with error details
        
    Returns:
        JSONResponse with 400 status and validation error details
    """
    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {exc.errors()}"
    )
    
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        error_dict = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": str(error.get("input")) if error.get("input") is not None else None
        }
        errors.append(error_dict)
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "ValidationError",
            "message": "Invalid input parameters",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected errors.
    
    Catches all unhandled exceptions and returns a generic error response.
    In development mode, includes exception details for debugging.
    
    Args:
        request: The incoming request that caused the error
        exc: The unhandled exception
        
    Returns:
        JSONResponse with 500 status and error information
    """
    logger.error(
        f"Unexpected error on {request.method} {request.url.path}: {exc}",
        exc_info=True
    )
    
    # Include exception details only in development mode
    details = str(exc) if settings.ENVIRONMENT == "development" else None
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": details
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup information."""
    logger.info("=" * 60)
    logger.info("Briefler API starting up")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"History Storage: {settings.HISTORY_STORAGE_DIR}")
    logger.info(f"OpenAPI Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Briefler API shutting down")


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information.
    
    Returns:
        dict: API metadata and available documentation links
    """
    return {
        "name": "Briefler API",
        "version": "1.0.0",
        "description": "REST API for Gmail analysis using CrewAI",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }
