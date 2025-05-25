from fastapi import APIRouter, Depends, HTTPException
import uuid
import logging

from fastapi import Request
from api.models.query_models import QueryRequest, QueryResponse
from domain.services.query_service import QueryService
from domain.services.entity_service import EntityService
from domain.services.session_service import SessionService
from infrastructure.storage.factory import get_storage
from infrastructure.storage.session_repository import StorageSessionRepository
from core.config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependências
def get_query_service(request: Request):
    """Dependência para obter o serviço de consulta"""
    settings = get_settings()
    
    # Criar o armazenamento de contexto
    storage = get_storage(
        storage_type=settings.STORAGE_TYPE,
        redis_url=settings.REDIS_URL,
        sqlite_db_path=settings.SQLITE_DB_PATH
    )
    
    # Criar o repositório de sessões
    session_repository = StorageSessionRepository(storage)

    # Pegando o singleton já carregado
    extractor = request.app.state.entity_extractor
    entity_service = EntityService(entity_extractor=extractor)
    session_service = SessionService(session_repository)
    
    # Retornar o serviço de consulta
    return QueryService(entity_service, session_service)

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, query_service: QueryService = Depends(get_query_service)):
    """Processa uma consulta de texto"""
    try:
        # Usar o ID da sessão fornecido ou gerar um novo
        session_id = request.session_id or str(uuid.uuid4())
        
        # Processar a consulta
        query, response = query_service.process_query(session_id, request.query)
        
        # Construir a resposta
        return QueryResponse(
            session_id=response.session_id,
            query=response.query_text,
            response=response.response_text,
            status=response.status,
            distribuidor=response.distribuidor,
            pedido=response.pedido,
            nota_fiscal=response.nota_fiscal,
            missing_fields=response.get_missing_fields() if response.is_missing_info() else None,
            error=response.error,
            data=response.data
        )
    except Exception as e:
        logger.error(f"Erro ao processar consulta: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar consulta: {str(e)}")