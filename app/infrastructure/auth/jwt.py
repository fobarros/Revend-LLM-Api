from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from core.config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Modelo para token
class Token(BaseModel):
    access_token: str
    token_type: str

# Modelo para dados do token
class TokenData(BaseModel):
    session_id: Optional[str] = None

# Configuração de segurança para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuração do OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Função para criar um token de acesso
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token JWT com os dados fornecidos"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

# Função para verificar um token
async def get_session_id(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Extrai e valida o session_id de um token JWT"""
    if token is None:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        session_id: str = payload.get("sub")
        
        if session_id is None:
            return None
        
        token_data = TokenData(session_id=session_id)
        return token_data.session_id
    except JWTError:
        return None

# Função para gerar um novo token de sessão
def generate_session_token(session_id: str) -> Token:
    """Gera um novo token JWT para a sessão especificada"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": session_id}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

# Função para verificar se o token é válido e obter o session_id
async def get_current_session_id(token: Optional[str] = Depends(oauth2_scheme)) -> str:
    """Obtém o session_id atual ou gera um erro se o token for inválido"""
    session_id = await get_session_id(token)
    
    if session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sessão inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return session_id

# Função para obter o session_id opcional (não gera erro se não existir)
async def get_optional_session_id(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Obtém o session_id atual ou retorna None se o token for inválido"""
    return await get_session_id(token)