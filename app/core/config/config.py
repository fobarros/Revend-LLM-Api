import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env se existir
load_dotenv()

# Configurações do modelo NER
DEFAULT_NER_MODEL = os.getenv("NER_MODEL", "pucpr/ner-bert-base-portuguese-cased")
FALLBACK_NER_MODEL = os.getenv("FALLBACK_NER_MODEL", "xlm-roberta-base")

# Configurações da API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "True").lower() in ("true", "1", "t")

# Configurações de segurança
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_para_desenvolvimento_local")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Configurações de armazenamento
# Por padrão, usamos armazenamento em memória, mas pode ser configurado para Redis ou SQLite
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "memory")  # memory, redis, sqlite
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./storage.db")

# Configurações de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")