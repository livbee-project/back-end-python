"""
스튜디오 서비스 단위 테스트
"""

import uuid

import pytest
from fastapi import HTTPException

from app.models.studio import Studio
from app.services.studio_service import create_studio, get_studio_by_id, update_studio


@pytest.fixture
def test_studio(db_session):
    """테스트용 스튜디오 생성"""
    studio = Studio(id=str(uuid.uuid4()), brand_name="Test Studio", one_line_intro="Test intro")
    db_session.add(studio)
    db_session.flush()
    return studio


def test_get_studio_by_id_success(db_session, test_studio):
    """스튜디오 ID로 조회 성공 테스트"""
    studio = get_studio_by_id(db_session, test_studio.id)

    assert studio is not None
    assert studio.id == test_studio.id
    assert studio.brand_name == "Test Studio"


def test_get_studio_by_id_not_found(db_session):
    """존재하지 않는 스튜디오 조회 테스트"""
    with pytest.raises(HTTPException) as exc_info:
        get_studio_by_id(db_session, str(uuid.uuid4()))

    assert exc_info.value.status_code == 404


def test_create_studio_success(db_session):
    """스튜디오 생성 성공 테스트"""
    studio = create_studio(
        db_session,
        brand_name="New Studio",
        one_line_intro="New intro",
        detailed_intro="Detailed intro",
        main_thumbnail_url="https://example.com/thumb.jpg",
    )

    assert studio is not None
    assert studio.brand_name == "New Studio"
    assert studio.one_line_intro == "New intro"
    assert studio.detailed_intro == "Detailed intro"
    assert studio.main_thumbnail_url == "https://example.com/thumb.jpg"


def test_create_studio_with_optional_fields(db_session):
    """선택적 필드를 포함한 스튜디오 생성 테스트"""
    studio = create_studio(
        db_session,
        brand_name="Studio with Options",
        contact={"phone": "010-1234-5678", "email": "studio@example.com"},
        location={"address": "Seoul", "lat": 37.5665, "lng": 126.9780},
        sub_thumbnail_urls=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
    )

    assert studio.brand_name == "Studio with Options"
    assert studio.contact is not None
    assert studio.location is not None
    assert len(studio.sub_thumbnail_urls) == 2


def test_update_studio_success(db_session, test_studio):
    """스튜디오 수정 성공 테스트"""
    updated = update_studio(
        db_session,
        studio_id=test_studio.id,
        brand_name="Updated Studio",
        one_line_intro="Updated intro",
    )

    assert updated.brand_name == "Updated Studio"
    assert updated.one_line_intro == "Updated intro"


def test_update_studio_partial(db_session, test_studio):
    """스튜디오 부분 수정 테스트"""
    original_intro = test_studio.one_line_intro
    updated = update_studio(db_session, studio_id=test_studio.id, brand_name="Updated Studio")

    assert updated.brand_name == "Updated Studio"
    assert updated.one_line_intro == original_intro  # 변경되지 않음


def test_update_studio_not_found(db_session):
    """존재하지 않는 스튜디오 수정 실패 테스트"""
    with pytest.raises(HTTPException) as exc_info:
        update_studio(db_session, studio_id=str(uuid.uuid4()), brand_name="Updated Studio")

    assert exc_info.value.status_code == 404
