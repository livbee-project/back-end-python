"""
에러 메시지 정의
사용자 친화적인 에러 메시지와 시스템 메시지 매핑
"""
from typing import Dict, Any

ErrorDefinition = Dict[str, Any]

ERROR_MESSAGES: Dict[str, ErrorDefinition] = {
    # --- 공통 에러 ---
    "INTERNAL_ERROR": {
        "message": "Internal Server Error",
        "userMessage": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
    },
    "NOT_FOUND": {
        "message": "Resource not found",
        "userMessage": "요청하신 정보를 찾을 수 없습니다.",
    },
    "VALIDATION_FAILED": {
        "message": "Validation failed",
        "userMessage": "입력값이 올바르지 않습니다.",
    },
    "FORBIDDEN": {
        "message": "Forbidden",
        "userMessage": "요청에 대한 권한이 없습니다.",
    },
    "INVALID_ID": {
        "message": "Invalid ID format",
        "userMessage": "올바르지 않은 ID 형식입니다.",
    },
    
    # --- 인증 (Users) ---
    "INVALID_CREDENTIALS": {
        "message": "Invalid credentials",
        "userMessage": "이메일 또는 비밀번호가 잘못되었습니다.",
    },
    "ROLE_MISMATCH": {
        "message": "Role does not match",
        "userMessage": "선택하신 역할과 계정 정보가 일치하지 않습니다.",
    },
    "DUPLICATE": {
        "message": "Duplicate email",
        "userMessage": "이미 가입된 이메일입니다.",
    },
    "AUTH_NO_ROLE": {
        "message": "Role not present in token",
        "userMessage": "사용자 역할 정보가 없습니다. 다시 로그인해주세요.",
    },
    "AUTH_FORBIDDEN_ROLE": {
        "message": "Role is not permitted",
        "userMessage": "이 기능을 사용할 권한이 없습니다.",
    },
    "AUTH_REQUIRED": {
        "message": "Authentication required",
        "userMessage": "인증이 필요합니다.",
    },
    "INVALID_TOKEN": {
        "message": "Invalid or expired token",
        "userMessage": "유효하지 않은 토큰입니다.",
    },
    "VALIDATION_MISSING_FIELDS": {
        "message": "Required fields are missing",
        "userMessage": "필수 입력값이 누락되었습니다.",
    },
    "VALIDATION_INVALID_ROLE": {
        "message": "Invalid role value",
        "userMessage": "역할 값이 올바르지 않습니다.",
    },
    
    # --- 지원 (Applications) ---
    "ALREADY_APPLIED": {
        "message": "Duplicate application submission",
        "userMessage": "이미 지원한 공고입니다.",
    },
    "DEADLINE_PASSED": {
        "message": "Application deadline has passed",
        "userMessage": "모집이 마감된 공고입니다.",
    },
    "NOT_RECRUIT": {
        "message": "Campaign is not a recruit type",
        "userMessage": "모집형 캠페인에만 지원할 수 있습니다.",
    },
    
    # --- 캠페인 (Campaigns) ---
    "COVER_IMAGE_REQUIRED": {
        "message": "Cover image is required when publishing",
        "userMessage": "게시 상태로 변경하려면 커버 이미지가 반드시 필요합니다.",
    },
    "RECRUIT_FORBIDDEN_EDIT": {
        "message": "Forbidden to edit recruit",
        "userMessage": "공고를 수정할 권한이 없습니다.",
    },
    "RECRUIT_FORBIDDEN_DELETE": {
        "message": "Forbidden to delete recruit",
        "userMessage": "공고를 삭제할 권한이 없습니다.",
    },
    
    # --- 포트폴리오 (Portfolios) ---
    "PORTFOLIO_FORBIDDEN_EDIT": {
        "message": "Forbidden to edit portfolio",
        "userMessage": "포트폴리오를 수정할 권한이 없습니다.",
    },
    "PORTFOLIO_FORBIDDEN_DELETE": {
        "message": "Forbidden to delete portfolio",
        "userMessage": "포트폴리오를 삭제할 권한이 없습니다.",
    },
    "PORTFOLIO_DUP": {
        "message": "Portfolio already exists for this user",
        "userMessage": "이미 포트폴리오가 존재합니다.",
    },
}


def get_error_message(error_key: str) -> ErrorDefinition:
    """
    에러 키에 해당하는 에러 메시지 반환
    
    Args:
        error_key: 에러 키 (예: "NOT_FOUND")
    
    Returns:
        에러 메시지 딕셔너리
    """
    return ERROR_MESSAGES.get(
        error_key,
        {
            "message": "Unknown error",
            "userMessage": "알 수 없는 오류가 발생했습니다.",
        }
    )

