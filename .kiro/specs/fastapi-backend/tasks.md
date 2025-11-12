# Implementation Plan

- [x] 1. Set up FastAPI project structure
  - Create `src/api/` directory with proper Python package structure
  - Create subdirectories: `routes/`, `models/`, `services/`, `core/`
  - Add `__init__.py` files to make packages importable
  - Create `data/history/` directory for JSON storage
  - _Requirements: 5.1, 5.2_

- [x] 2. Implement core configuration and settings
  - [x] 2.1 Create `src/api/core/config.py` with Pydantic Settings
    - Define settings for API host, port, CORS origins
    - Add history storage configuration
    - Support loading from environment variables
    - _Requirements: 5.5_
  
  - [x] 2.2 Create `src/api/core/logging.py` for logging configuration
    - Configure Python logging with appropriate format
    - Set log levels based on environment
    - Add request/response logging
    - _Requirements: 4.2_

- [ ] 3. Implement Pydantic data models
  - [x] 3.1 Create `src/api/models/requests.py` with request models
    - Implement `GmailAnalysisRequest` with validation
    - Add email format validator
    - Add ISO 639-1 language code validator
    - Add days range validator (1-365)
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [x] 3.2 Create `src/api/models/responses.py` with response models
    - Implement `GmailAnalysisResponse` model
    - Implement `ErrorResponse` model
    - Implement `HistoryItem` and `HistoryListResponse` models
    - _Requirements: 1.4, 6.2, 6.3_

- [ ] 4. Implement history service
  - [x] 4.1 Create `src/api/services/history_service.py`
    - Implement `save()` method for persisting analysis results to JSON
    - Implement `get_history()` method with pagination support
    - Implement `get_by_id()` method for retrieving specific analysis
    - Implement `_cleanup_old_files()` to maintain 100 file limit
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [ ] 5. Implement flow orchestration service
  - [x] 5.1 Create `src/api/services/flow_service.py`
    - Implement `execute_flow()` method for synchronous execution
    - Generate unique UUID for each analysis
    - Capture execution time metrics
    - Integrate with `GmailReadFlow` from existing codebase
    - Save results to history service
    - _Requirements: 1.3, 1.4_
  
  - [x] 5.2 Implement SSE streaming support
    - Implement `execute_flow_stream()` async generator
    - Emit progress events during flow execution
    - Emit complete event with final result
    - Emit error events on exceptions
    - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [ ] 6. Implement API routes
  - [x] 6.1 Create `src/api/routes/flows.py` for flow endpoints
    - Implement POST `/api/flows/gmail-read` endpoint
    - Implement GET `/api/flows/gmail-read/stream` SSE endpoint
    - Add error handling for validation and execution errors
    - Return appropriate HTTP status codes
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 3.1, 3.3_
  
  - [x] 6.2 Create `src/api/routes/history.py` for history endpoints
    - Implement GET `/api/history` with pagination
    - Implement GET `/api/history/{analysis_id}` endpoint
    - Handle 404 errors for missing analyses
    - _Requirements: 6.2, 6.3_
  
  - [x] 6.3 Create `src/api/routes/health.py` for health check endpoints
    - Implement GET `/health` endpoint
    - Implement GET `/ready` endpoint with dependency checks
    - Check Gmail credentials availability
    - Check environment variables configuration
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 7. Create FastAPI application
  - [x] 7.1 Create `src/api/main.py` as application entry point
    - Initialize FastAPI app with title and description
    - Configure CORS middleware for localhost
    - Register all routers (flows, history, health)
    - Add global exception handlers
    - Enable OpenAPI documentation at `/docs`
    - _Requirements: 4.1, 4.3, 5.4_

- [ ] 8. Update project dependencies
  - [x] 8.1 Add FastAPI dependencies to `pyproject.toml`
    - Add `fastapi>=0.104.0`
    - Add `uvicorn[standard]>=0.24.0`
    - Add `pydantic-settings>=2.0.0`
    - _Requirements: 5.2_

- [ ] 9. Create API documentation
  - [x] 9.1 Create `src/api/README.md` with usage instructions
    - Document how to run the API server
    - Document available endpoints
    - Provide example requests with curl
    - Document environment variables
    - _Requirements: 4.2_

- [ ] 10. Manual testing and validation
  - [x] 10.1 Test POST `/api/flows/gmail-read` endpoint
    - Test with valid parameters
    - Test with invalid email format
    - Test with invalid language code
    - Test with invalid days value
    - Verify analysis result is returned
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.4_
  
  - [x] 10.2 Test SSE streaming endpoint
    - Test GET `/api/flows/gmail-read/stream` with query params
    - Verify progress events are emitted
    - Verify complete event with result
    - Test error handling
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 10.3 Test history endpoints
    - Test GET `/api/history` with pagination
    - Test GET `/api/history/{analysis_id}`
    - Verify 404 for non-existent analysis
    - Verify history limit enforcement
    - _Requirements: 6.1, 6.2, 6.3, 6.5_
  
  - [x] 10.4 Test health check endpoints
    - Test GET `/health` returns 200
    - Test GET `/ready` checks dependencies
    - Verify readiness check fails without credentials
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 10.5 Test CORS configuration
    - Verify CORS headers are present
    - Test requests from localhost origins
    - _Requirements: 4.3, 5.4_
