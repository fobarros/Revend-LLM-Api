from typing import Optional, List, Dict, Any
from domain.models.session import Session
from domain.repositories.session_repository import SessionRepository
from infrastructure.storage.base import ContextStorage

class StorageSessionRepository(SessionRepository):
    """Implementação do repositório de sessões usando ContextStorage"""
    
    def __init__(self, storage: ContextStorage):
        self.storage = storage
    
    def get(self, session_id: str) -> Optional[Session]:
        """Obtém uma sessão pelo ID"""
        session_data = self.storage.get(session_id)
        if not session_data:
            return None
        
        return Session.from_dict(session_data)
    
    def create(self, session: Session) -> Session:
        """Cria uma nova sessão"""
        session_data = session.to_dict()
        self.storage.set(session.session_id, session_data)
        return session
    
    def update(self, session: Session) -> Session:
        """Atualiza uma sessão existente"""
        session_data = session.to_dict()
        self.storage.set(session.session_id, session_data)
        return session
    
    def delete(self, session_id: str) -> bool:
        """Exclui uma sessão pelo ID"""
        if self.storage.exists(session_id):
            self.storage.delete(session_id)
            return True
        return False
    
    def list_by_user(self, user_id: str) -> List[Session]:
        """Lista todas as sessões de um usuário"""
        # Nota: Esta implementação é ineficiente para grandes volumes de dados
        # Em um ambiente de produção, seria melhor usar um banco de dados com índices
        sessions = []
        
        # Como o ContextStorage não tem um método para listar todas as sessões,
        # esta implementação é limitada e não recomendada para produção
        # Em um ambiente real, seria necessário implementar um mecanismo de busca
        # ou usar um banco de dados adequado
        
        # Esta é uma implementação de exemplo que assume que temos acesso a todos os IDs
        # Em uma implementação real, isso seria substituído por uma consulta ao banco de dados
        if hasattr(self.storage, "get_all_keys"):
            all_keys = getattr(self.storage, "get_all_keys")()  # Método hipotético
            for session_id in all_keys:
                session_data = self.storage.get(session_id)
                if session_data and session_data.get("user_id") == user_id:
                    sessions.append(Session.from_dict(session_data))
        
        return sessions
    
    def list_active(self) -> List[Session]:
        """Lista todas as sessões ativas"""
        # Mesma limitação da implementação anterior
        sessions = []
        
        if hasattr(self.storage, "get_all_keys"):
            all_keys = getattr(self.storage, "get_all_keys")()  # Método hipotético
            for session_id in all_keys:
                session_data = self.storage.get(session_id)
                if session_data and session_data.get("active", False):
                    sessions.append(Session.from_dict(session_data))
        
        return sessions