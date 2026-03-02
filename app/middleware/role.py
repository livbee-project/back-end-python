"""
역할 기반 접근 제어 미들웨어
"""

from fastapi import Depends, HTTPException, status

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
        is_brand = user.get("isBrand")
        is_showhost = user.get("isShowhost")

        if not user_role:
            error = get_error_message("AUTH_NO_ROLE")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "AUTH_NO_ROLE",
                    "message": error["message"],
                    "userMessage": error["userMessage"],
                },
            )

        # admin은 모든 역할 허용
        if user_role == "admin":
            return user

        # 다중 역할 플래그 기반 체크 (토큰에 isBrand / isShowhost 포함)
        if "brand" in allowed_roles and is_brand:
            return user
        if "showhost" in allowed_roles and is_showhost:
            return user

        # 플래그 정보가 없거나, 과거 토큰 등과의 호환성을 위해 role 값도 함께 검사
        if user_role not in allowed_roles:
            error = get_error_message("AUTH_FORBIDDEN_ROLE")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "AUTH_FORBIDDEN_ROLE",
                    "message": error["message"],
                    "userMessage": error["userMessage"],
                },
            )

        return user

    return role_checker
