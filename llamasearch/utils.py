from prometheus_client import Summary
from llamasearch.logger import logger
from typing import Dict, Any
from functools import lru_cache
import os, yaml
import traceback
import sys
import csv

# Metrics dictionary to hold all metrics instances
metrics = {}

def get_function_metric(func_name):
    """Retrieve or create a Summary metric for a specific function."""
    if func_name not in metrics:
        metrics[func_name] = Summary(f'{func_name}_query_time_seconds', f'Time spent executing {func_name}')
    return metrics[func_name]

@lru_cache(maxsize=1000)
def dummy_file_checked(directory: str) -> bool:
    return os.path.exists(os.path.join(directory, "dummy.csv"))

def load_yaml_file(filepath: str) -> Dict[str, Any]:
    """
    Load a YAML file and return the data as a dictionary.

    Args:
        filepath (str): The path to the YAML file to be loaded.

    Returns:
        Dict[str, Any]: The data from the YAML file as a dictionary.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No such file: '{filepath}'")

    with open(filepath, 'r') as file:
        try:
            data = yaml.safe_load(file)  # Use safe_load to prevent execution of arbitrary code
            return data
        except yaml.YAMLError as exc:
            print(f"Error in configuration file: {exc}")
            raise

def custom_exception_handler(exc_type, exc_value, exc_traceback):
    # Get the traceback object
    tb = traceback.extract_tb(exc_traceback)
    
    # Find the last frame in the traceback that's from our file
    for frame in reversed(tb):
        if frame.filename.endswith('qdrant_hybrid_search.py'):
            filename = frame.filename
            line_number = frame.lineno
            line = frame.line
            break
    else:
        # If we didn't find our file in the traceback, fall back to default handling
        return sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # Log the error
    error_msg = f"Error in {filename} at line {line_number}:\n{line}\n{exc_type.__name__}: {exc_value}"
    logger.error(error_msg)


def ensure_dummy_csv(directory: str):
    if not dummy_file_checked(directory):
        dummy_file = os.path.join(directory, "dummy.csv")
        if not os.path.exists(dummy_file):
            with open(dummy_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["This", "is", "a", "dummy", "file"])
                writer.writerow(["to", "ensure", "the", "directory", "is", "not", "empty"])
        dummy_file_checked.cache_clear()  # Clear the cache for this directory

sys.excepthook = custom_exception_handler