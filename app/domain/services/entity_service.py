from typing import Dict, Optional
from core.services.nlp import EntityExtractor
from domain.models.query import Query
from core.config.settings import get_settings

class EntityService:
    """Serviço para extração e processamento de entidades"""
    
    def __init__(self, entity_extractor: Optional[EntityExtractor] = None):
        settings = get_settings()
        self.entity_extractor = entity_extractor or EntityExtractor(
            model_name=settings.NER_MODEL,
            fallback_model=settings.NER_FALLBACK_MODEL
        )
    
    def extract_entities(self, text: str) -> Dict[str, str]:
        """Extrai entidades de um texto"""
        return self.entity_extractor.extract_entities(text)
    
    def process_query(self, session_id: str, query_text: str) -> Query:
        """Processa uma consulta de texto e extrai entidades"""
        # Extrair entidades do texto da consulta
        entities = self.extract_entities(query_text)
        
        # Criar objeto de consulta com as entidades extraídas
        query = Query.from_entities(session_id, query_text, entities)
        
        return query
    
    def enrich_query_from_context(self, query: Query, context: Dict) -> Query:
        """Enriquece uma consulta com informações do contexto da sessão"""
        # Se alguma entidade estiver faltando na consulta atual, tenta obter do contexto
        if not query.distribuidor and "distribuidor" in context:
            query.distribuidor = context["distribuidor"]
            query.entities["distribuidor"] = context["distribuidor"]
        
        if not query.pedido and "pedido" in context:
            query.pedido = context["pedido"]
            query.entities["pedido"] = context["pedido"]
        
        if not query.nota_fiscal and "nota_fiscal" in context:
            query.nota_fiscal = context["nota_fiscal"]
            query.entities["nota_fiscal"] = context["nota_fiscal"]
        
        return query