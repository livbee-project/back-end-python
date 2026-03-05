"""
Auth 라우트
SMS 인증 전용 (인증번호 발송·검증)
"""

import random

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.rate_limit import limiter
from app.core.redis import delete_sms_code, get_redis, get_sms_code, set_sms_code
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.schemas.auth import (
    BusinessVerificationRequest,
    KakaoLoginRequest,
    SendSmsRequest,
    VerifySmsRequest,
)
from app.services.business_verification_service import (
    BusinessVerificationError,
    verify_business,
)
from app.services.user_service import get_user_by_email
from app.utils.common import normalize_phone_number
from app.utils.response import fail_response, success_response
from app.utils.sms import send_sms_verification

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-sms")
@limiter.limit("5/minute")
async def send_sms(request: Request, body: SendSmsRequest):
    """
    SMS 인증번호 발송.
    전화번호 정규화 후 6자리 코드 생성 → Redis 저장 → SMS 발송.
    """
    normalized = normalize_phone_number(body.phone_number)
    if not normalized:
        return fail_response("VALIDATION_FAILED", status.HTTP_400_BAD_REQUEST)

    if get_redis() is None:
        logger.warning("send_sms: Redis unavailable")
        return fail_response("REDIS_UNAVAILABLE", status.HTTP_503_SERVICE_UNAVAILABLE)

    code = "".join(str(random.randint(0, 9)) for _ in range(6))
    set_sms_code(normalized, code)

    if not send_sms_verification(normalized, code):
        logger.warning("send_sms: SMS 발송 실패 phone=%s", normalized[:6] + "***")
        return fail_response("SMS_SEND_FAILED", status.HTTP_502_BAD_GATEWAY)

    logger.info("SMS 인증번호 발송 완료: phone=%s***", normalized[:6])
    return success_response(message="인증번호를 발송했습니다.")


@router.post("/verify-sms")
async def verify_sms(request: Request, body: VerifySmsRequest):
    """
    SMS 인증번호 검증.
    Redis에 저장된 코드와 비교 후 일치하면 키 삭제하고 성공 응답.
    """
    normalized = normalize_phone_number(body.phone_number)
    if not normalized:
        return fail_response("VALIDATION_FAILED", status.HTTP_400_BAD_REQUEST)

    stored = get_sms_code(normalized)
    if stored is None or stored != body.code:
        logger.info("verify_sms: 불일치 또는 만료 phone=%s***", normalized[:6])
        return fail_response("SMS_VERIFY_FAILED", status.HTTP_400_BAD_REQUEST)

    delete_sms_code(normalized)
    logger.info("SMS 인증 성공: phone=%s***", normalized[:6])
    return success_response(message="인증에 성공했습니다.")


@router.post("/kakao/login")
@limiter.limit("5/minute")
async def kakao_login(
    request: Request,
    body: KakaoLoginRequest,
    db: Session = Depends(get_db),
):
    """
    카카오 간편 로그인

    - 프론트에서 이미 카카오 OAuth를 통해 kakaoId, email, name, role을 받아온 상태에서 호출
    - kakaoId + role 기준으로 우선 조회, 없으면 email + role 기준으로 조회
    - 해당 역할로 가입된 유저가 있으면 JWT 토큰 발급
    - 유저가 없으면 USER_NOT_FOUND 에러 반환
    """
    kakao_id = body.kakao_id.strip() if body.kakao_id else ""
    email = body.email.lower().strip()
    requested_role: UserRole = body.role

    if not kakao_id or not email or not requested_role:
        return fail_response("VALIDATION_MISSING_FIELDS", status.HTTP_400_BAD_REQUEST)

    # 1) kakao_id 기준으로 우선 조회
    user = db.query(User).filter(User.kakao_id == kakao_id).first()

    # 2) kakao_id로 못 찾으면 email 기준으로 조회 (기존 이메일 가입 계정과 연결)
    if not user:
        user = get_user_by_email(db, email)

    # 3) 여전히 사용자 없으면 USER_NOT_FOUND 반환
    if not user:
        return fail_response(
            "USER_NOT_FOUND",
            status.HTTP_404_NOT_FOUND,
            {"code": "USER_NOT_FOUND"},
        )

    # 4) 역할 권한 확인 (is_brand / is_showhost 플래그 기반)
    requested_role_value = (
        requested_role.value if hasattr(requested_role, "value") else str(requested_role)
    )
    has_brand = bool(getattr(user, "is_brand", False))
    has_showhost = bool(getattr(user, "is_showhost", False))

    # 요청한 역할로는 아직 가입되지 않은 경우: USER_NOT_FOUND_FOR_ROLE (404)
    if requested_role_value == UserRole.BRAND.value and not has_brand:
        return fail_response(
            "USER_NOT_FOUND_FOR_ROLE",
            status.HTTP_404_NOT_FOUND,
            {"code": "USER_NOT_FOUND_FOR_ROLE"},
        )
    if requested_role_value == UserRole.SHOWHOST.value and not has_showhost:
        return fail_response(
            "USER_NOT_FOUND_FOR_ROLE",
            status.HTTP_404_NOT_FOUND,
            {"code": "USER_NOT_FOUND_FOR_ROLE"},
        )

    # 5) 이메일로 매칭된 기존 계정에 kakao_id가 비어 있으면 이번 로그인으로 연동
    if not getattr(user, "kakao_id", None):
        user.kakao_id = kakao_id
        db.flush()
        db.refresh(user)

    # 6) JWT 토큰 생성 (기존 /users/login 과 동일한 페이로드 구조)
    user_role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    token_data = {
        "sub": user.id,
        "role": user_role_value,
        "isBrand": has_brand,
        "isShowhost": has_showhost,
    }
    token = create_access_token(data=token_data)

    # 7) 응답 형식은 /users/login 과 동일하게 유지
    return success_response(
        {
            "token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user_role_value,
                "isBrand": has_brand,
                "isShowhost": has_showhost,
            },
        }
    )


@router.post("/verify-business")
@limiter.limit("5/minute")
async def verify_business_status(request: Request, body: BusinessVerificationRequest):
    """
    국세청 사업자등록정보 상태조회 기반 진위확인.

    - 입력: 사업자등록번호(필수), 개업일자/대표자명(선택, 현재는 보관만)
    - 처리: 공공데이터포털 국세청 상태조회 API(status)를 호출해 계속사업자 여부 확인
    - 출력: ok=true/false + valid 플래그 및 상태/과세유형 요약 정보
    """
    # 사업자번호는 숫자만 남기고 정규화
    normalized_bno = "".join(ch for ch in body.business_number if ch.isdigit())
    if len(normalized_bno) != 10:
        return fail_response("VALIDATION_FAILED", status.HTTP_400_BAD_REQUEST)

    try:
        result = verify_business(
            business_number=normalized_bno,
            opening_date=body.opening_date,
            representative_name=body.representative_name,
        )
    except BusinessVerificationError as exc:
        logger.warning("verify-business failed: %s", exc)
        return fail_response("BUSINESS_VERIFY_FAILED", status.HTTP_502_BAD_GATEWAY)

    return success_response(
        {
            "valid": result.valid,
            "businessNumber": result.business_number,
            "status": result.status,
            "statusCode": result.status_code,
            "taxType": result.tax_type,
            "taxTypeCode": result.tax_type_code,
        },
        message="사업자 등록정보를 확인했습니다.",
    )
