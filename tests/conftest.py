import pytest
import configparser
import os

# Read the config file
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'test_config.ini'))

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    terminalreporter.write_sep("=", "Test summary")
    terminalreporter.write_line(f"Total tests: {terminalreporter.stats.get('total', 0)}")
    terminalreporter.write_line(f"Passed: {len(terminalreporter.stats.get('passed', []))}")
    terminalreporter.write_line(f"Failed: {len(terminalreporter.stats.get('failed', []))}")
    terminalreporter.write_line(f"Skipped: {len(terminalreporter.stats.get('skipped', []))}")
