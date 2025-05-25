from typing import Dict, Optional, Any
from datetime import datetime
import uuid

from domain.models.session import Session
from domain.models.query import Query
from domain.models.response import Response
from domain.repositories.session_repository import SessionRepository

class SessionService:
    """Serviço para gerenciamento de sessões"""
    
    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository
    
    def create_session(self, user_id: Optional[str] = None) -> Session:
        """Cria uma nova sessão"""
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active=True
        )
        
        return self.session_repository.create(session)
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Obtém uma sessão pelo ID"""
        return self.session_repository.get(session_id)
    
    def update_session_context(self, session_id: str, context_updates: Dict[str, Any]) -> Optional[Session]:
        """Atualiza o contexto de uma sessão"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Atualizar o contexto com os novos valores
        for key, value in context_updates.items():
            session.update_context(key, value)
        
        # Salvar a sessão atualizada
        return self.session_repository.update(session)
    
    def add_interaction(self, session_id: str, query: Query, response: Response) -> Optional[Session]:
        """Adiciona uma interação ao histórico da sessão"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Adicionar a interação ao histórico
        session.add_to_history(
            query=query.query_text,
            response=response.response_text,
            entities=query.entities
        )
        
        # Atualizar o contexto com as entidades da consulta
        if query.distribuidor:
            session.update_context("distribuidor", query.distribuidor)
        
        if query.pedido:
            session.update_context("pedido", query.pedido)
        
        if query.nota_fiscal:
            session.update_context("nota_fiscal", query.nota_fiscal)
        
        # Salvar a sessão atualizada
        return self.session_repository.update(session)
    
    def deactivate_session(self, session_id: str) -> bool:
        """Desativa uma sessão"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.deactivate()
        self.session_repository.update(session)
        return True
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Obtém o contexto de uma sessão"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return session.context