from fastapi import APIRouter, Depends, HTTPException
import logging

from api.models.query_models import SessionRequest, SessionResponse
from domain.services.session_service import SessionService
from infrastructure.storage.factory import get_storage
from infrastructure.storage.session_repository import StorageSessionRepository
from core.config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependências
def get_session_service():
    """Dependência para obter o serviço de sessão"""
    settings = get_settings()
    
    # Criar o armazenamento de contexto
    storage = get_storage(
        storage_type=settings.STORAGE_TYPE,
        redis_url=settings.REDIS_URL,
        sqlite_db_path=settings.SQLITE_DB_PATH
    )
    
    # Criar o repositório de sessões
    session_repository = StorageSessionRepository(storage)
    
    # Retornar o serviço de sessão
    return SessionService(session_repository)

@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest, session_service: SessionService = Depends(get_session_service)):
    """Cria uma nova sessão"""
    try:
        # Criar uma nova sessão
        session = session_service.create_session(user_id=request.user_id)
        
        # Adicionar metadados, se fornecidos
        if request.metadata:
            for key, value in request.metadata.items():
                session.update_context(f"metadata_{key}", value)
            session_service.session_repository.update(session)
        
        # Construir a resposta
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            active=session.active
        )
    except Exception as e:
        logger.error(f"Erro ao criar sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar sessão: {str(e)}")

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, session_service: SessionService = Depends(get_session_service)):
    """Obtém uma sessão pelo ID"""
    try:
        # Obter a sessão
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Sessão não encontrada: {session_id}")
        
        # Construir a resposta
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            active=session.active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter sessão: {str(e)}")

@router.delete("/sessions/{session_id}", response_model=dict)
async def deactivate_session(session_id: str, session_service: SessionService = Depends(get_session_service)):
    """Desativa uma sessão"""
    try:
        # Desativar a sessão
        success = session_service.deactivate_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Sessão não encontrada: {session_id}")
        
        # Retornar resposta de sucesso
        return {"message": "Sessão desativada com sucesso", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao desativar sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao desativar sessão: {str(e)}")