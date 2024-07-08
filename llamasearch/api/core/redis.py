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