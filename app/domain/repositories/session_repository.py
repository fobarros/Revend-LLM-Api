from abc import ABC, abstractmethod
from typing import Optional, List
from domain.models.session import Session

class SessionRepository(ABC):
    """Interface para repositório de sessões"""
    
    @abstractmethod
    def get(self, session_id: str) -> Optional[Session]:
        """Obtém uma sessão pelo ID"""
        pass
    
    @abstractmethod
    def create(self, session: Session) -> Session:
        """Cria uma nova sessão"""
        pass
    
    @abstractmethod
    def update(self, session: Session) -> Session:
        """Atualiza uma sessão existente"""
        pass
    
    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """Exclui uma sessão pelo ID"""
        pass
    
    @abstractmethod
    def list_by_user(self, user_id: str) -> List[Session]:
        """Lista todas as sessões de um usuário"""
        pass
    
    @abstractmethod
    def list_active(self) -> List[Session]:
        """Lista todas as sessões ativas"""
        pass