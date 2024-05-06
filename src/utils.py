import aiohttp
import time
from functools import wraps
from datetime import datetime
from prometheus_client import Summary
from src.settings import config
from src.custom import CustomLogger

logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir=config.application.log_dir, log_name='profile.log')

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