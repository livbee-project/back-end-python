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
    current_user: dict = Depends(get_current_user)
):
    """
    Cloudinary 업로드 서명 생성 API
    
    프론트엔드에서 Cloudinary에 직접 파일을 업로드하기 위한 서명을 생성합니다.
    
    Args:
        type: 업로드 타입 (image 또는 raw)
        current_user: 현재 인증된 사용자 정보
    
    Returns:
        Cloudinary 업로드에 필요한 서명 정보
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
    
    # 타임스탬프 생성 (현재 시간)
    timestamp = int(time.time())
    
    # 업로드 파라미터 구성
    upload_params = {
        "timestamp": timestamp,
    }
    
    # 폴더 설정이 있으면 추가
    if settings.CLOUDINARY_FOLDER:
        upload_params["folder"] = settings.CLOUDINARY_FOLDER
    
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
    
    # 폴더가 설정되어 있으면 추가
    if settings.CLOUDINARY_FOLDER:
        response_data["folder"] = settings.CLOUDINARY_FOLDER
    
    return success_response({"data": response_data})

