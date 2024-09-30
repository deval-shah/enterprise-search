## Testing

We've configured pytest for our project using the following files:

1. [pytest.ini](./pytest.ini): This file contains the main configuration for pytest, including:
   - Automatic asyncio mode
   - Verbose output
   - HTML report generation
   - Custom test discovery paths
   - Logging configuration

2. [conftest.py](./tests/conftest.py): Contains shared pytest fixtures and configuration used across multiple test files.

### Start the API Server

Follow steps upto Option 2 in the [README.md](../README.md#option-2-testing-the-pipeline-and-backend-server-api-using-curl-locally) file to start the ES API server locally.

This will set up the necessary components for running the tests against the API server.

### Running the Tests locally

To run the test suite, open a new terminal and follow these steps:

1. Ensure you're in the project root directory. 

2. Update current worknig directory to the project root directory.
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

3. Start the local conda environment and install requirements as mentioned in the [README.md](../README.md) file.

4. Execute the DVC pipeline:
```bash
dvc repro -f tests/dvc.yaml
```

This command will run the following stages:
- **pull_test_data**: Pulls the latest test documents from DVC storage.
- **run_tests**: Set up the test environment.

The DVC pipeline ensures that the latest test data is used and all tests are run consistently. After execution, you can find the test results in the `report.html` file in the project root directory.

To run specific tests, you can modify the pytest command in the run_tests stage of the `tests/dvc.yaml` file or run pytest directly with custom options.

## Troubleshooting

If you are getting errors related to DVC, you can try the following:
- Clear .dvc/cache and .dvc/tmp

### Guidlines for adding new Test Cases

To add new test cases:

1. Choose the appropriate directory (`api/` or `pipeline/`) based on what you're testing.
2. Create a new test file or add to an existing one, following the naming convention `test_*.py`.
3. Write your test functions, prefixing them with `test_`.
4. Use fixtures from `conftest.py` as needed.