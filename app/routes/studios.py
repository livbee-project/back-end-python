"""
Studio 라우트
스튜디오 관리
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.studios import StudioCreate, StudioUpdate
from app.services.studio_service import (
    create_studio as create_studio_svc,
)
from app.services.studio_service import (
    get_studio_by_id,
)
from app.services.studio_service import (
    update_studio as update_studio_svc,
)
from app.utils.common import model_to_dict
from app.utils.response import success_response

router = APIRouter(prefix="/studios", tags=["studios"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_studio(request: StudioCreate, db: Session = Depends(get_db)):
    """
    새로운 스튜디오 정보 생성
    """
    studio_data = request.model_dump(exclude_unset=True, by_alias=False)

    # 서비스를 통한 스튜디오 생성
    studio = create_studio_svc(db, **studio_data)

    data = model_to_dict(studio)
    return success_response({"data": data}, status_code=status.HTTP_201_CREATED)


@router.put("/{studio_id}")
async def update_studio(studio_id: str, request: StudioUpdate, db: Session = Depends(get_db)):
    """
    특정 ID를 가진 스튜디오 정보 수정
    """
    update_data = request.model_dump(exclude_unset=True, by_alias=False)

    # 서비스를 통한 스튜디오 수정
    studio = update_studio_svc(db, studio_id, **update_data)

    data = model_to_dict(studio)
    return success_response({"data": data})


@router.get("/{studio_id}")
async def get_studio(studio_id: str, db: Session = Depends(get_db)):
    """
    특정 ID를 가진 스튜디오 정보 조회
    """
    studio = get_studio_by_id(db, studio_id)

    data = model_to_dict(studio)
    return success_response({"data": data})
