# Briefler API Tests

## Running Tests

```bash
# All tests
pytest tests/api/ -v

# Specific file
pytest tests/api/test_health.py -v

# Specific test
pytest tests/api/test_health.py::TestHealthCheckEndpoint::test_health_check_returns_200 -v

# Using venv directly
.venv/bin/pytest tests/api/ -v
```

## Structure

```
tests/
├── __init__.py              # Required for pytest importlib mode
├── conftest.py              # Shared fixtures
└── api/
    ├── __init__.py          # Required for pytest importlib mode
    ├── test_health.py       # Health endpoints tests
    ├── test_history.py      # History endpoints tests
    ├── test_flows_post.py   # POST /api/flows/gmail-read tests
    ├── test_flows_stream.py # GET /api/flows/gmail-read/stream tests
    └── test_cors.py         # CORS configuration tests
```

## Configuration

Pytest is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]              # Adds src/ to Python path
testpaths = ["tests"]             # Test directory
addopts = [
    "--import-mode=importlib",    # Uses importlib for imports
    "-ra",                        # Shows short summary of all tests
    "--strict-markers",           # Strict marker validation
]
```

**Important:** When using `--import-mode=importlib`, all test directories must contain `__init__.py`.

## Coverage

- **test_health.py** - 10 tests for health/ready endpoints
- **test_history.py** - 14 tests for history API
- **test_flows_post.py** - 20 tests for POST endpoint
- **test_flows_stream.py** - 15 tests for streaming endpoint
- **test_cors.py** - 12 tests for CORS configuration
