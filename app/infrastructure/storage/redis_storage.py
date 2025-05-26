import json
from typing import Dict, Any
from infrastructure.storage.base import ContextStorage

class RedisStorage(ContextStorage):
    def __init__(self, redis_url: str):
        try:
            import redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.prefix = "session:"  # <<< use nome mais claro
        except ImportError:
            raise ImportError("Redis não está instalado. Instale com 'pip install redis'")
    
    def get(self, session_id: str) -> Dict[str, Any]:
        key = f"{self.prefix}{session_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return {}

    def set(self, session_id: str, session_data: Dict[str, Any]) -> None:
        key = f"{self.prefix}{session_id}"
        self.redis.set(key, json.dumps(session_data), ex=86400)

    def delete(self, session_id: str) -> None:
        key = f"{self.prefix}{session_id}"
        self.redis.delete(key)

    def exists(self, session_id: str) -> bool:
        key = f"{self.prefix}{session_id}"
        return bool(self.redis.exists(key))
