from abc import ABC, abstractmethod
from typing import Dict

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