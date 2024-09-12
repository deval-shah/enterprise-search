## Testing

The test suite is organized as follows:

- `tests/`
  - `api/`: Tests for API endpoints
    - `test_api_http.py`: HTTP API tests
    - `test_api_websocket.py`: WebSocket API tests
    - `base_api_test.py`: Base class for API tests
  - `conftest.py`: Shared pytest fixtures and configuration

### Adding New Test Cases

To add new test cases:

1. Choose the appropriate directory (`api/` or `pipeline/`) based on what you're testing.
2. Create a new test file or add to an existing one, following the naming convention `test_*.py`.
3. Write your test functions, prefixing them with `test_`.
4. Use fixtures from `conftest.py` as needed.

### Running Tests

#### Test Data

Test documents are managed using DVC. The `run_tests.sh` script handles pulling the latest test data before running the tests.

#### Run API Server

Follow steps upto Option 2 in the [README.md](../README.md#option-2-testing-the-pipeline-and-backend-server-api-using-curl-locally) file to start the ES API server locally.

This will set up the necessary components for running the tests against the API server.

To run the test suite:

1. Ensure you're in the project root directory.

2. Start the local conda environment and install requirements as mentioned in the [README.md](../README.md) file.

3. Execute the test script:
```bash
chmod +x ./scripts/run_tests.sh ; ./scripts/run_tests.sh
```

This script will:

- Pull necessary test data using DVC
- Set up the test environment
- Run pytest with the configured options
- Generate a test report (report.html)

To run specific tests, you can modify the pytest command in run_tests.sh or run pytest directly with custom options.