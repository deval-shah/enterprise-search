import redis
from llamasearch.api.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL)

def get_redis():
    return redis_client

def set_session(session_id: str, user_id: str, expiry: int = 3600):
    redis_client.setex(f"session:{session_id}", expiry, user_id)

def get_session(session_id: str) -> str:
    return redis_client.get(f"session:{session_id}")

def delete_session(session_id: str):
    redis_client.delete(f"session:{session_id}")

def get_file_count(user_id: str) -> int:
    return int(redis_client.get(f"file_count:{user_id}") or 0)

def update_file_count(user_id: str, count: int):
    redis_client.set(f"file_count:{user_id}", count)

def increment_file_count(user_id: str, increment: int = 1) -> bool:
    current_count = redis_client.incrby(f"file_count:{user_id}", increment)
    if current_count > settings.MAX_FILES:
        # If limit is exceeded, decrement back and return False
        redis_client.decrby(f"file_count:{user_id}", increment)
        return False
    return True