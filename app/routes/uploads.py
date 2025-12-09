"""
Upload 라우트
파일 업로드 관련 API (Cloudinary 서명 생성)
"""
import time
import hashlib
import hmac
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.config import settings
from app.middleware.auth import get_current_user
from app.utils.response import success_response, fail_response

router = APIRouter(prefix="/uploads", tags=["uploads"])


def get_upload_folder_path(category: Optional[str] = None, resource_id: Optional[str] = None) -> Optional[str]:
    """
    업로드 파일의 폴더 경로 생성
    
    Args:
        category: 파일 카테고리 (campaign, portfolio, news, user 등)
        resource_id: 리소스 ID (campaign_id, portfolio_id 등)
    
    Returns:
        폴더 경로 문자열 또는 None
    """
    # 기본 폴더가 설정되어 있으면 기본 경로 사용
    base_folder = settings.CLOUDINARY_FOLDER or "livbee"
    
    if not category:
        return base_folder
    
    # 카테고리별 폴더 구조
    category_folders = {
        "campaign": "campaigns",
        "portfolio": "portfolios",
        "news": "news",
        "user": "users",
        "studio": "studios",
    }
    
    folder_name = category_folders.get(category.lower())
    if not folder_name:
        return base_folder
    
    # 리소스 ID가 있으면 하위 폴더로 구성
    if resource_id:
        return f"{base_folder}/{folder_name}/{resource_id}"
    
    return f"{base_folder}/{folder_name}"


def generate_cloudinary_signature(params: dict, api_secret: str) -> str:
    """
    Cloudinary 업로드 서명 생성
    
    Args:
        params: 업로드 파라미터 딕셔너리
        api_secret: Cloudinary API Secret
    
    Returns:
        서명 문자열 (hexdigest)
    """
    # 파라미터를 키 기준으로 정렬하고 문자열로 변환
    sorted_params = sorted(params.items())
    param_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    
    # HMAC-SHA1 서명 생성
    signature = hmac.new(
        api_secret.encode('utf-8'),
        param_string.encode('utf-8'),
        hashlib.sha1
    ).hexdigest()
    
    return signature


@router.get("/signature")
async def get_upload_signature(
    type: str = Query(..., description="업로드 타입: image 또는 raw"),
    category: Optional[str] = Query(None, description="파일 카테고리: campaign, portfolio, news, user, studio"),
    resource_id: Optional[str] = Query(None, description="리소스 ID (campaign_id, portfolio_id 등)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Cloudinary 업로드 서명 생성 API
    
    프론트엔드에서 Cloudinary에 직접 파일을 업로드하기 위한 서명을 생성합니다.
    
    Args:
        type: 업로드 타입 (image 또는 raw)
        category: 파일 카테고리 (campaign, portfolio, news, user, studio)
        resource_id: 리소스 ID (campaign_id, portfolio_id 등, 선택사항)
        current_user: 현재 인증된 사용자 정보
    
    Returns:
        Cloudinary 업로드에 필요한 서명 정보
    
    폴더 구조:
    - 기본: livbee/ (또는 CLOUDINARY_FOLDER 환경변수 값)
    - 캠페인: livbee/campaigns/{campaign_id}/
    - 포트폴리오: livbee/portfolios/{portfolio_id}/
    - 뉴스: livbee/news/{news_id}/
    - 사용자: livbee/users/{user_id}/
    - 스튜디오: livbee/studios/{studio_id}/
    """
    # Cloudinary 설정 확인
    if not settings.CLOUDINARY_API_KEY or not settings.CLOUDINARY_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary 설정이 완료되지 않았습니다."
        )
    
    # 타입 검증
    if type not in ["image", "raw"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="type 파라미터는 'image' 또는 'raw'여야 합니다."
        )
    
    # 카테고리 검증
    valid_categories = ["campaign", "portfolio", "news", "user", "studio"]
    if category and category.lower() not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"category 파라미터는 다음 중 하나여야 합니다: {', '.join(valid_categories)}"
        )
    
    # 타임스탬프 생성 (현재 시간)
    timestamp = int(time.time())
    
    # 폴더 경로 생성
    folder_path = get_upload_folder_path(category, resource_id)
    
    # 업로드 파라미터 구성
    upload_params = {
        "timestamp": timestamp,
    }
    
    # 폴더 경로 추가
    if folder_path:
        upload_params["folder"] = folder_path
    
    # 타입별 추가 파라미터
    if type == "image":
        # 이미지 업로드 파라미터 (필요시 추가)
        pass
    elif type == "raw":
        # 파일 업로드 파라미터 (필요시 추가)
        pass
    
    # Cloudinary 서명 생성
    signature = generate_cloudinary_signature(
        upload_params,
        settings.CLOUDINARY_API_SECRET
    )
    
    # 응답 데이터 구성
    response_data = {
        "apiKey": settings.CLOUDINARY_API_KEY,
        "signature": signature,
        "timestamp": str(timestamp),
        "cloudName": settings.CLOUDINARY_CLOUD_NAME,
    }
    
    # 폴더 경로 추가
    if folder_path:
        response_data["folder"] = folder_path
    
    return success_response({"data": response_data})

