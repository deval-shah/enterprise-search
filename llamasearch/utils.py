import aiohttp
import time
from functools import wraps
from datetime import datetime
from prometheus_client import Summary
from llamasearch.logger import logger
import os, yaml
from typing import Dict, Any
import sys
import traceback

# Metrics dictionary to hold all metrics instances
metrics = {}

def get_function_metric(func_name):
    """Retrieve or create a Summary metric for a specific function."""
    if func_name not in metrics:
        metrics[func_name] = Summary(f'{func_name}_query_time_seconds', f'Time spent executing {func_name}')
    return metrics[func_name]

def profile_(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        func_metric = get_function_metric(func.__name__)
        start_time = time.time()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed_time = time.time() - start_time
            func_metric.observe(elapsed_time)
            logger.info(f"PROFILE :: {func.__name__} executed in {elapsed_time:.2f} seconds.")
    return wrapper

def profile_to_endpoint(func):
    """
    Decorator to profile an endpoint function, log its execution time, send profiling data to a local server, and include a timestamp.

    Args:
        func (Callable): The endpoint function to be profiled.
    
    Returns:
        Callable: The wrapped function with profiling.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            response = await func(*args, **kwargs)
            return response
        finally:
            elapsed_time = time.time() - start_time
            logger.info(f"PROFILE :: {func.__name__} executed in {elapsed_time:.2f} seconds.")
            await send_profiling_data(func.__name__, elapsed_time)
    return wrapper

async def send_profiling_data(function_name, elapsed_time):
    """
    Sends profiling data to the local server endpoint asynchronously, including a timestamp, and handles server unavailability gracefully.
    
    Args:
        function_name (str): Name of the function profiled.
        elapsed_time (float): Execution time of the function.
    """
    url = "http://127.0.0.1:8001/receive-profile/"
    timestamp = datetime.now().isoformat()
    data = {
        "function_name": function_name,
        "execution_time": elapsed_time,
        "timestamp": timestamp
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info("Profiling data successfully sent to local endpoint.")
                else:
                    logger.error(f"Failed to send profiling data. Status: {response.status}")
    except Exception as e:
        logger.error(f"Failed to connect to profiling server: {e}")

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


sys.excepthook = custom_exception_handler