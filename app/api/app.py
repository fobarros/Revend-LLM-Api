from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from api.endpoints import query, session
from core.config.settings import get_settings

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Obter configurações
settings = get_settings()

# Criar aplicação FastAPI
app = FastAPI(
    title="Revend LLM API",
    description="API para consulta de status de pedidos e notas fiscais",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"Método: {request.method} | URL: {request.url.path} | "
        f"Status: {response.status_code} | Tempo: {process_time:.4f}s"
    )
    return response

# Tratamento global de exceções
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocorreu um erro interno no servidor."}
    )

# Incluir routers
app.include_router(query.router, prefix="/api", tags=["consultas"])
app.include_router(session.router, prefix="/api", tags=["sessões"])

# Rota de verificação de saúde
@app.get("/health", tags=["saúde"])
async def health_check():
    return {"status": "ok", "version": app.version}

# Rota raiz
@app.get("/", tags=["raiz"])
async def root():
    return {
        "message": "Bem-vindo à API Revend LLM",
        "docs": "/docs",
        "health": "/health"
    }