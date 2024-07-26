import pytest
import configparser
import os

# Read the config file
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'test_config.ini'))

@pytest.fixture(scope="session")
def base_dir():
    return "data/sample-docs/slim/"

@pytest.fixture(scope="session")
def filenames():
    return [
        'Llama_Paper.pdf', 
        'meta-10k-1-5.pdf', 
        'uber_10k-1-5.pdf',
        'Reduce_Hallucinations_RAG_Paper.pdf'
    ]

# def pytest_configure(config):
#     #config.option.verbose = 0  # Reduce verbosity
#     #config.option.show_progress = False  # Disable progress bar

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    terminalreporter.write_sep("=", "Test summary")
    terminalreporter.write_line(f"Total tests: {terminalreporter.stats.get('total', 0)}")
    terminalreporter.write_line(f"Passed: {len(terminalreporter.stats.get('passed', []))}")
    terminalreporter.write_line(f"Failed: {len(terminalreporter.stats.get('failed', []))}")
    terminalreporter.write_line(f"Skipped: {len(terminalreporter.stats.get('skipped', []))}")
