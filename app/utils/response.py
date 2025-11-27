"""
응답 헬퍼 함수
일관된 API 응답 형식 제공
"""
from typing import Any, Optional
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import status
from app.utils.error_messages import get_error_message


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    성공 응답 생성
    
    Args:
        data: 응답 데이터
        message: 응답 메시지
        status_code: HTTP 상태 코드
    
    Returns:
        JSONResponse
    """
    response_data = {"ok": True}
    
    if data is not None:
        response_data["data"] = data
    
    if message:
        response_data["message"] = message
    
    response = JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response_data)
    )
    # CORS는 미들웨어에서 처리되므로 여기서는 제거
    return response


def fail_response(
    error_key: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    additional_data: Optional[dict] = None
) -> JSONResponse:
    """
    실패 응답 생성
    
    Args:
        error_key: 에러 키 (error_messages.py에 정의된 키)
        status_code: HTTP 상태 코드
        additional_data: 추가 데이터
    
    Returns:
        JSONResponse
    """
    error = get_error_message(error_key)
    
    response_data = {
        "ok": False,
        "error": error_key,
        "message": error["message"],
        "userMessage": error["userMessage"],
    }
    
    if additional_data:
        response_data.update(additional_data)
    
    response = JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response_data)
    )
    # CORS는 미들웨어에서 처리되므로 여기서는 제거
    return response

