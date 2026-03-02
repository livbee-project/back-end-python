"""
지원서 서비스 단위 테스트
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.models.application import ApplicationStatus
from app.models.campaign import Campaign
from app.models.user import UserRole
from app.services.application_service import (
    create_application,
    get_application_by_campaign_and_user,
    get_applications_by_campaign,
    update_application_status,
)


@pytest.fixture
def test_brand_user(db_session):
    """테스트용 브랜드 사용자 생성"""
    from app.services.user_service import create_user

    return create_user(
        db_session,
        name="Brand User",
        email="brand@example.com",
        password="password123",
        role=UserRole.BRAND,
        brand_name="Test Brand",
    )


@pytest.fixture
def test_showhost_user(db_session):
    """테스트용 쇼호스트 사용자 생성"""
    from app.services.user_service import create_user

    return create_user(
        db_session,
        name="Showhost User",
        email="showhost@example.com",
        password="password123",
        role=UserRole.SHOWHOST,
    )


@pytest.fixture
def test_campaign(db_session, test_brand_user):
    """테스트용 캠페인 생성"""
    campaign = Campaign(
        id=str(uuid.uuid4()),
        title="Test Campaign",
        content="Test content",
        brand_name="Test Brand",
        created_by=test_brand_user.id,
        close_at=date.today() + timedelta(days=7),
        is_public=True,
    )
    db_session.add(campaign)
    db_session.flush()
    return campaign


def test_create_application_success(db_session, test_campaign, test_showhost_user):
    """지원서 생성 성공 테스트"""
    availability_date = date.today() + timedelta(days=2)
    application = create_application(
        db_session,
        campaign_id=test_campaign.id,
        user_id=test_showhost_user.id,
        message="Test application",
        available_date=availability_date,
        available_time="evening",
    )

    assert application is not None
    assert application.campaign_id == test_campaign.id
    assert application.user_id == test_showhost_user.id
    assert application.status == ApplicationStatus.SUBMITTED
    assert application.available_date == availability_date
    assert application.available_time == "evening"


def test_create_application_deadline_passed(db_session, test_campaign, test_showhost_user):
    """마감일이 지난 캠페인에 지원 실패 테스트"""
    # 마감일을 과거로 변경
    test_campaign.close_at = date.today() - timedelta(days=1)
    db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        create_application(db_session, campaign_id=test_campaign.id, user_id=test_showhost_user.id)

    assert exc_info.value.status_code == 409


def test_create_application_duplicate(db_session, test_campaign, test_showhost_user):
    """중복 지원 실패 테스트"""
    # 첫 번째 지원
    create_application(db_session, campaign_id=test_campaign.id, user_id=test_showhost_user.id)

    # 중복 지원 시도
    with pytest.raises(HTTPException) as exc_info:
        create_application(db_session, campaign_id=test_campaign.id, user_id=test_showhost_user.id)

    assert exc_info.value.status_code == 409


def test_get_application_by_campaign_and_user(db_session, test_campaign, test_showhost_user):
    """캠페인과 사용자로 지원서 조회 테스트"""
    # 지원서 생성
    created = create_application(
        db_session, campaign_id=test_campaign.id, user_id=test_showhost_user.id
    )

    # 조회
    application = get_application_by_campaign_and_user(
        db_session, campaign_id=test_campaign.id, user_id=test_showhost_user.id
    )

    assert application is not None
    assert application.id == created.id


def test_get_applications_by_campaign(db_session, test_campaign, test_brand_user):
    """캠페인의 지원서 목록 조회 테스트"""
    # 지원서 생성
    from app.services.user_service import create_user

    showhost = create_user(
        db_session,
        name="Showhost",
        email="showhost2@example.com",
        password="password123",
        role=UserRole.SHOWHOST,
    )

    create_application(db_session, campaign_id=test_campaign.id, user_id=showhost.id)

    # 오너로 조회
    applications = get_applications_by_campaign(
        db_session, campaign_id=test_campaign.id, user_id=test_brand_user.id, user_role="brand"
    )

    assert len(applications) == 1


def test_update_application_status(db_session, test_campaign, test_brand_user, test_showhost_user):
    """지원서 상태 변경 테스트"""
    # 지원서 생성
    application = create_application(
        db_session, campaign_id=test_campaign.id, user_id=test_showhost_user.id
    )

    # 상태 변경
    updated = update_application_status(
        db_session,
        application_id=application.id,
        new_status=ApplicationStatus.ACCEPTED,
        user_id=test_brand_user.id,
        user_role="brand",
    )

    assert updated.status == ApplicationStatus.ACCEPTED
