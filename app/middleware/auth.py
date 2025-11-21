"""
인증 미들웨어
JWT 토큰 검증 및 사용자 정보 추출
"""
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
from app.utils.error_messages import get_error_message

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    현재 인증된 사용자 정보 반환
    
    Args:
        credentials: HTTP Bearer 토큰
    
    Returns:
        사용자 정보 딕셔너리 (예: {"sub": user_id, "role": user_role})
    
    Raises:
        HTTPException: 인증 실패 시
    """
    if not credentials:
        error = get_error_message("AUTH_REQUIRED")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AUTH_REQUIRED",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        error = get_error_message("INVALID_TOKEN")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_TOKEN",
                "message": error["message"],
                "userMessage": error["userMessage"],
            }
        )
    
    return payload


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    선택적 인증 사용자 정보 반환
    토큰이 없어도 에러를 발생시키지 않음
    
    Args:
        credentials: HTTP Bearer 토큰
    
    Returns:
        사용자 정보 딕셔너리 또는 None
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    return payload if payload else None

