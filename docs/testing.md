## Testing

### Setup

1. Follow the steps in [README](https://gitlab.aiml.team/products/aiml/enterprise-search/LlamaSearch/-/tree/sc19374/multi-tenancy-qdrant-updates/#running-locally) to setup and test the pipeline locally before you run the tests. Follow steps in `Option 1`.

This will ensure the pipeline is working and ready for the test run.

2. Ensure DVC is installed and configured:
Check if `.dvc/config` is correctly configured to enterprise search gs origin (e.g. `gs://`)
```bash
[core]
    remote = origin
['remote "origin"']
    url = gs://aiml-enterprise-search-data/llamasearch/dvc
```
### Running Tests

Execute the test suite using the provided script in the root directory:
```bash
chmod +x run_tests.sh
./run_tests.sh
```

#### Test Execution Flow

- Pulls test documents from Google Cloud Storage in test data path (defined in test_config.ini)
- Runs pytest with configurations from `pytest.ini` file in root directory
- After running tests, view report.html for detailed results and test coverage.