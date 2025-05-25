from typing import Dict
from infrastructure.storage.base import ContextStorage

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