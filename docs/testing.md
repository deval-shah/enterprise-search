## Testing

We've configured pytest for our project using the following files:

1. [pytest.ini](../pytest.ini): This file contains the main configuration for pytest, including:
   - Automatic asyncio mode
   - Verbose output
   - HTML report generation
   - Custom test discovery paths
   - Logging configuration

2. [conftest.py](../tests/conftest.py): Contains shared pytest fixtures and configuration used across multiple test files. This file also includes sample QA pairs used for testing.

3. [test_docs](../data/test_docs/): Contains sample documents used for testing.

### Start the API Server

Follow steps in the [README.md](../README.md) to start the ES API server locally.

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
- **pull_test_data**: You can uncomment this stage to pull the latest test data from DVC storage. You need to configure  the DVC remote storage in the `.dvc/config` file.
- **run_tests**: Set up the test environment.

After execution, you can find the test results in the `report.html` file in the project root directory.

To run specific tests, you can modify the pytest command in the run_tests stage of the `tests/dvc.yaml` file or run pytest directly with custom options.

To run specific tests, you can use pytest's built-in options. For example:

```bash
pytest tests/api/test_specific_file.py
```

## Troubleshooting

If you encounter any issues while running the tests, please refer to the project's documentation or reach out to the development team.

### Guidlines for adding new Test Cases

To add new test cases:

1. Choose the appropriate directory (`api/` or `pipeline/`) based on what you're testing.
2. Create a new test file or add to an existing one, following the naming convention `test_*.py`.
3. Write your test functions, prefixing them with `test_`.
4. Use fixtures from `conftest.py` as needed.
5. If necessary, add new test documents to the `data/test_docs` folder.
6. Update the sample QA pairs in `tests/conftest.py` if required for your new tests.