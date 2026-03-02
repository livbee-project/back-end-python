"""
User 라우트
사용자 인증 및 관리
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.rate_limit import limiter
from app.middleware.auth import get_current_user
from app.models.user import UserRole
from app.schemas.users import LoginRequest, SignupRequest
from app.services.user_service import authenticate_user, create_user, get_user_by_id
from app.utils.common import mask_email, mask_phone, normalize_phone_number
from app.utils.response import fail_response, success_response

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def signup(request: Request, signup_request: SignupRequest, db: Session = Depends(get_db)):
    """
    회원가입
    역할('brand', 'showhost')에 따라 다른 정보를 받아 사용자를 생성
    """
    # 입력값 검증
    name = signup_request.name.strip()
    email = signup_request.email.lower().strip()
    password = signup_request.password
    role = signup_request.role

    if not name or not email or not password or not role:
        return fail_response("VALIDATION_MISSING_FIELDS", status.HTTP_400_BAD_REQUEST)

    # 'brand' 역할의 경우, 'brandName' 필드가 필수
    if role == UserRole.BRAND and not (signup_request.brand_name or "").strip():
        return fail_response(
            "VALIDATION_MISSING_FIELDS",
            status.HTTP_400_BAD_REQUEST,
            {"userMessage": "브랜드 이름은 필수 입력 항목입니다."},
        )

    # 서비스를 통한 사용자 생성
    try:
        user = create_user(
            db,
            name=name,
            email=email,
            password=password,
            role=role,
            phone=signup_request.phone,
            brand_name=signup_request.brand_name,
            company_name=signup_request.company_name,
            business_number=signup_request.business_number,
            nickname=signup_request.nickname,
            sns_link=signup_request.sns_link,
            introduction=signup_request.introduction,
        )
    except HTTPException:
        # HTTPException은 그대로 전파 (중복 이메일 등)
        db.rollback()
        raise
    except Exception as e:
        # 예상치 못한 에러 처리
        db.rollback()
        logger.error(f"회원가입 중 오류 발생: {str(e)}", exc_info=True)
        return fail_response("INTERNAL_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR)

    return success_response(
        {"userId": user.id, "role": user.role}, status_code=status.HTTP_201_CREATED
    )


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, login_request: LoginRequest, db: Session = Depends(get_db)):
    """
    로그인
    이메일, 비밀번호를 받아 로그인 처리 후 JWT 토큰을 발급
    역할(role)은 선택적이며, 제공되지 않으면 사용자의 실제 역할을 사용
    """
    # 입력값 검증 및 정규화
    email = login_request.email.lower().strip() if login_request.email else ""
    password = login_request.password or ""
    requested_role = login_request.role

    logger.info(f"Login attempt for email: {email[:3]}*** (role: {requested_role})")

    if not email or not password:
        logger.warning("Login failed: Missing email or password")
        return fail_response("VALIDATION_MISSING_FIELDS", status.HTTP_400_BAD_REQUEST)

    # 서비스를 통한 사용자 인증
    try:
        user, token = authenticate_user(
            db, email=email, password=password, requested_role=requested_role
        )
        user_role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
        logger.info(f"Login successful for user: {user.id} (email: {email[:3]}***)")
    except Exception:
        # HTTPException은 그대로 전파
        raise

    return success_response(
        {
            "token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user_role_value,
                "isBrand": bool(getattr(user, "is_brand", False)),
                "isShowhost": bool(getattr(user, "is_showhost", False)),
            },
        }
    )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    현재 로그인된 사용자의 기본 정보 조회
    """
    user_id = current_user.get("sub")
    if not user_id:
        return fail_response("AUTH_REQUIRED", status.HTTP_401_UNAUTHORIZED)

    user = get_user_by_id(db, user_id)

    normalized_phone = normalize_phone_number(user.phone) if user.phone else None
    role_value = user.role.value if hasattr(user.role, "value") else user.role

    return success_response(
        {
            "id": user.id,
            "name": user.name,
            "role": role_value,
            "email": user.email,
            "maskedEmail": mask_email(user.email),
            "phone": user.phone,
            "maskedPhone": mask_phone(user.phone),
            "normalizedPhone": normalized_phone,
            "isBrand": bool(getattr(user, "is_brand", False)),
            "isShowhost": bool(getattr(user, "is_showhost", False)),
        }
    )
