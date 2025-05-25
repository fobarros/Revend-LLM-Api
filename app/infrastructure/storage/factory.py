from typing import Dict, Any
from infrastructure.storage.base import ContextStorage
from infrastructure.storage.memory import MemoryStorage
from infrastructure.storage.redis_storage import RedisStorage
from infrastructure.storage.sqlite_storage import SQLiteStorage

# Fábrica para criar a implementação de armazenamento apropriada
def get_storage(storage_type: str, **kwargs) -> ContextStorage:
    """Cria e retorna uma instância de armazenamento baseada no tipo especificado
    
    Args:
        storage_type: Tipo de armazenamento ('memory', 'redis', 'sqlite')
        **kwargs: Argumentos adicionais para a inicialização do armazenamento
        
    Returns:
        Uma instância de ContextStorage
    """
    if storage_type == "redis":
        redis_url = kwargs.get("redis_url", "redis://localhost:6379/0")
        return RedisStorage(redis_url)
    elif storage_type == "sqlite":
        db_path = kwargs.get("sqlite_db_path", "./storage.db")
        return SQLiteStorage(db_path)
    else:  # default: memory
        return MemoryStorage()