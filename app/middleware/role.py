"""
역할 기반 접근 제어 미들웨어
"""
from typing import List, Optional
from fastapi import HTTPException, status, Depends
from app.middleware.auth import get_current_user
from app.utils.error_messages import get_error_message


def require_role(*allowed_roles: str):
    """
    특정 역할만 허용하는 의존성 함수 생성
    
    Args:
        *allowed_roles: 허용할 역할 목록
    
    Returns:
        의존성 함수
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        """
        사용자 역할 검증
        
        Args:
            user: 현재 사용자 정보
        
        Returns:
            사용자 정보
        
        Raises:
            HTTPException: 역할이 없거나 허용되지 않은 경우
        """
        user_role = user.get("role")
        
        if not user_role:
            error = get_error_message("AUTH_NO_ROLE")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "AUTH_NO_ROLE",
                    "message": error["message"],
                    "userMessage": error["userMessage"],
                }
            )
        
        # admin은 모든 역할 허용
        if user_role == "admin":
            return user
        
        if user_role not in allowed_roles:
            error = get_error_message("AUTH_FORBIDDEN_ROLE")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "AUTH_FORBIDDEN_ROLE",
                    "message": error["message"],
                    "userMessage": error["userMessage"],
                }
            )
        
        return user
    
    return role_checker

