import time
from functools import wraps
from custom import CustomLogger

logger = CustomLogger.setup_logger(__name__, save_to_disk=False, log_dir='./data/profile')

def profile_endpoint(func):
    """
    Decorator to profile an endpoint function and log its execution time.

    Args:
        func (Callable): The endpoint function to be profiled.
    
    Returns:
        Callable: The wrapped function with profiling.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            # Call the wrapped endpoint function
            response = await func(*args, **kwargs)
            return response
        finally:
            # Calculate and log the execution time
            elapsed_time = time.time() - start_time
            logger.info(f"PROFILE :: {func.__name__} executed in {elapsed_time:.2f} seconds.")
    return wrapper