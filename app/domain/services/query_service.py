from typing import Dict, Optional, Any, Tuple
import logging

from domain.models.query import Query
from domain.models.response import Response
from domain.models.session import Session
from domain.services.entity_service import EntityService
from domain.services.session_service import SessionService

logger = logging.getLogger(__name__)

class QueryService:
    """Serviço para processamento de consultas"""
    
    def __init__(
        self, 
        entity_service: EntityService,
        session_service: SessionService
    ):
        self.entity_service = entity_service
        self.session_service = session_service
    
    def process_query(self, session_id: str, query_text: str) -> Tuple[Query, Response]:
        """Processa uma consulta de texto"""
        try:
            # Obter a sessão
            session = self.session_service.get_session(session_id)
            if not session:
                # Criar uma nova sessão se não existir
                logger.info(f"Criando nova sessão para ID: {session_id}")
                session = self.session_service.create_session()
                session_id = session.session_id
            
            # Extrair entidades da consulta
            query = self.entity_service.process_query(session_id, query_text)
            
            # Enriquecer a consulta com o contexto da sessão
            query = self.entity_service.enrich_query_from_context(query, session.context)
            
            # Verificar se o distribuidor é suportado
            if query.distribuidor and not self.entity_service.entity_extractor.is_distribuidor_suportado(query.distribuidor):
                # Gerar resposta para distribuidor não suportado
                response_text = f"Desculpe, atualmente não trabalhamos com o distribuidor {query.distribuidor}. Os distribuidores suportados são: Officer, Ingram e Golden."
                
                response = Response.success(
                    session_id=session_id,
                    query_text=query_text,
                    response_text=response_text,
                    distribuidor=query.distribuidor,
                    pedido=query.pedido,
                    nota_fiscal=query.nota_fiscal
                )
                
                # Adicionar a interação ao histórico da sessão
                self.session_service.add_interaction(session_id, query, response)
                
                return query, response
            
            # Verificar se a consulta tem informações suficientes
            if not query.is_valid():
                missing_fields = query.get_missing_fields()
                response = Response.missing_info(
                    session_id=session_id,
                    query_text=query_text,
                    missing_fields=missing_fields,
                    distribuidor=query.distribuidor,
                    pedido=query.pedido,
                    nota_fiscal=query.nota_fiscal
                )
                
                # Adicionar a interação ao histórico da sessão
                self.session_service.add_interaction(session_id, query, response)
                
                return query, response
            
            # Aqui seria implementada a lógica para consultar o status do pedido ou nota fiscal
            # Por enquanto, vamos retornar uma resposta simulada
            
            # Simulação de resposta
            response_text = self._generate_mock_response(query)
            
            response = Response.success(
                session_id=session_id,
                query_text=query_text,
                response_text=response_text,
                distribuidor=query.distribuidor,
                pedido=query.pedido,
                nota_fiscal=query.nota_fiscal,
                data={
                    "consulted_at": "2023-06-15T10:30:00",
                    "source": "mock"
                }
            )
            
            # Adicionar a interação ao histórico da sessão
            self.session_service.add_interaction(session_id, query, response)
            
            return query, response
            
        except Exception as e:
            logger.error(f"Erro ao processar consulta: {e}")
            error_response = Response.error(
                session_id=session_id,
                query_text=query_text,
                error_message=f"Ocorreu um erro ao processar sua consulta: {str(e)}"
            )
            
            # Criar um objeto Query mínimo para o registro de erro
            error_query = Query(session_id=session_id, query_text=query_text)
            
            # Tentar registrar o erro na sessão, se possível
            try:
                self.session_service.add_interaction(session_id, error_query, error_response)
            except Exception as session_error:
                logger.error(f"Erro ao registrar interação na sessão: {session_error}")
            
            return error_query, error_response
    
    def _generate_mock_response(self, query: Query) -> str:
        """Gera uma resposta simulada para a consulta"""
        distribuidor = query.distribuidor or "distribuidor não especificado"
        
        if query.pedido:
            return f"O pedido {query.pedido} do distribuidor {distribuidor} está em processamento. A previsão de entrega é para 5 dias úteis."
        
        if query.nota_fiscal:
            return f"A nota fiscal {query.nota_fiscal} do distribuidor {distribuidor} foi emitida e o produto está em trânsito. A previsão de entrega é para 3 dias úteis."
        
        return "Não foi possível identificar informações suficientes para processar sua consulta."