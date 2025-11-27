"""
스튜디오 관련 비즈니스 로직 서비스
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.models.studio import Studio
from app.utils.db_helpers import get_or_404
import uuid


def get_studio_by_id(
    db: Session,
    studio_id: str
) -> Studio:
    """
    스튜디오 ID로 조회
    
    Args:
        db: 데이터베이스 세션
        studio_id: 스튜디오 ID
    
    Returns:
        스튜디오 인스턴스
    
    Raises:
        HTTPException: 스튜디오를 찾을 수 없는 경우
    """
    return get_or_404(
        db,
        Studio,
        lambda q: q.filter(Studio.id == studio_id),
        error_key="NOT_FOUND"
    )


def create_studio(
    db: Session,
    brand_name: Optional[str] = None,
    one_line_intro: Optional[str] = None,
    detailed_intro: Optional[str] = None,
    usage_info: Optional[str] = None,
    price_info: Optional[str] = None,
    main_thumbnail_url: Optional[str] = None,
    background_image_url: Optional[str] = None,
    sub_thumbnail_urls: Optional[List[str]] = None,
    gallery_urls: Optional[List[str]] = None,
    contact: Optional[Dict] = None,
    location: Optional[Dict] = None,
    weekly_schedule: Optional[Dict] = None
) -> Studio:
    """
    스튜디오 생성
    
    Args:
        db: 데이터베이스 세션
        ... (기타 필드들)
    
    Returns:
        생성된 스튜디오 인스턴스
    """
    studio_data = {
        "id": str(uuid.uuid4()),
        "brand_name": brand_name,
        "one_line_intro": one_line_intro,
        "detailed_intro": detailed_intro,
        "usage_info": usage_info,
        "price_info": price_info,
        "main_thumbnail_url": main_thumbnail_url,
        "background_image_url": background_image_url,
        "sub_thumbnail_urls": sub_thumbnail_urls,
        "gallery_urls": gallery_urls,
        "contact": contact,
        "location": location,
        "weekly_schedule": weekly_schedule,
    }
    
    # None 값 제거
    studio_data = {k: v for k, v in studio_data.items() if v is not None}
    
    studio = Studio(**studio_data)
    db.add(studio)
    db.refresh(studio)
    
    return studio


def update_studio(
    db: Session,
    studio_id: str,
    brand_name: Optional[str] = None,
    one_line_intro: Optional[str] = None,
    detailed_intro: Optional[str] = None,
    usage_info: Optional[str] = None,
    price_info: Optional[str] = None,
    main_thumbnail_url: Optional[str] = None,
    background_image_url: Optional[str] = None,
    sub_thumbnail_urls: Optional[List[str]] = None,
    gallery_urls: Optional[List[str]] = None,
    contact: Optional[Dict] = None,
    location: Optional[Dict] = None,
    weekly_schedule: Optional[Dict] = None
) -> Studio:
    """
    스튜디오 수정
    
    Args:
        db: 데이터베이스 세션
        studio_id: 스튜디오 ID
        ... (기타 필드들)
    
    Returns:
        수정된 스튜디오 인스턴스
    
    Raises:
        HTTPException: 스튜디오를 찾을 수 없는 경우
    """
    studio = get_studio_by_id(db, studio_id)
    
    update_data = {
        "brand_name": brand_name,
        "one_line_intro": one_line_intro,
        "detailed_intro": detailed_intro,
        "usage_info": usage_info,
        "price_info": price_info,
        "main_thumbnail_url": main_thumbnail_url,
        "background_image_url": background_image_url,
        "sub_thumbnail_urls": sub_thumbnail_urls,
        "gallery_urls": gallery_urls,
        "contact": contact,
        "location": location,
        "weekly_schedule": weekly_schedule,
    }
    
    # None이 아닌 값만 업데이트
    for key, value in update_data.items():
        if value is not None:
            setattr(studio, key, value)
    
    db.refresh(studio)
    
    return studio

