from typing import Dict, Optional, Any, Union
import json
import uuid
from abc import ABC, abstractmethod

# Interface abstrata para armazenamento de contexto
class ContextStorage(ABC):
    @abstractmethod
    def get(self, session_id: str) -> Dict:
        pass
    
    @abstractmethod
    def set(self, session_id: str, context: Dict) -> None:
        pass
    
    @abstractmethod
    def delete(self, session_id: str) -> None:
        pass
    
    @abstractmethod
    def exists(self, session_id: str) -> bool:
        pass

# Implementação de armazenamento em memória
class MemoryStorage(ContextStorage):
    def __init__(self):
        self.storage: Dict[str, Dict] = {}
    
    def get(self, session_id: str) -> Dict:
        return self.storage.get(session_id, {})
    
    def set(self, session_id: str, context: Dict) -> None:
        self.storage[session_id] = context
    
    def delete(self, session_id: str) -> None:
        if session_id in self.storage:
            del self.storage[session_id]
    
    def exists(self, session_id: str) -> bool:
        return session_id in self.storage

# Implementação de armazenamento com Redis
class RedisStorage(ContextStorage):
    def __init__(self, redis_url: str):
        try:
            import redis
            self.redis = redis.from_url(redis_url)
            self.prefix = "context:"
        except ImportError:
            raise ImportError("Redis não está instalado. Instale com 'pip install redis'")
    
    def get(self, session_id: str) -> Dict:
        key = f"{self.prefix}{session_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return {}
    
    def set(self, session_id: str, context: Dict) -> None:
        key = f"{self.prefix}{session_id}"
        self.redis.set(key, json.dumps(context))
    
    def delete(self, session_id: str) -> None:
        key = f"{self.prefix}{session_id}"
        self.redis.delete(key)
    
    def exists(self, session_id: str) -> bool:
        key = f"{self.prefix}{session_id}"
        return bool(self.redis.exists(key))

# Implementação de armazenamento com SQLite
class SQLiteStorage(ContextStorage):
    def __init__(self, db_path: str):
        try:
            import sqlite3
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._create_table()
        except ImportError:
            raise ImportError("SQLite3 não está disponível")
    
    def _create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS contexts (
            session_id TEXT PRIMARY KEY,
            context TEXT NOT NULL
        )
        """)
        self.conn.commit()
    
    def get(self, session_id: str) -> Dict:
        self.cursor.execute("SELECT context FROM contexts WHERE session_id = ?", (session_id,))
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return {}
    
    def set(self, session_id: str, context: Dict) -> None:
        context_json = json.dumps(context)
        self.cursor.execute("""
        INSERT OR REPLACE INTO contexts (session_id, context) VALUES (?, ?)
        """, (session_id, context_json))
        self.conn.commit()
    
    def delete(self, session_id: str) -> None:
        self.cursor.execute("DELETE FROM contexts WHERE session_id = ?", (session_id,))
        self.conn.commit()
    
    def exists(self, session_id: str) -> bool:
        self.cursor.execute("SELECT 1 FROM contexts WHERE session_id = ?", (session_id,))
        return bool(self.cursor.fetchone())

# Fábrica para criar a implementação de armazenamento apropriada
def get_storage(storage_type: str, **kwargs) -> ContextStorage:
    if storage_type == "redis":
        redis_url = kwargs.get("redis_url", "redis://localhost:6379/0")
        return RedisStorage(redis_url)
    elif storage_type == "sqlite":
        db_path = kwargs.get("sqlite_db_path", "./storage.db")
        return SQLiteStorage(db_path)
    else:  # default: memory
        return MemoryStorage()