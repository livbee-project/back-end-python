"""
캠페인 서비스 단위 테스트
"""

import uuid
from datetime import date, timedelta

import pytest

from app.models.campaign import Campaign
from app.models.user import UserRole
from app.services.campaign_service import (
    check_application_exists,
    check_campaign_ownership,
    get_campaign_by_id,
    get_campaigns_with_applied_status,
    get_user_campaigns,
)


@pytest.fixture
def test_user(db_session):
    """테스트용 사용자 생성"""
    from app.services.user_service import create_user

    return create_user(
        db_session,
        name="Test User",
        email="test@example.com",
        password="password123",
        role=UserRole.BRAND,
        brand_name="Test Brand",
    )


@pytest.fixture
def test_campaign(db_session, test_user):
    """테스트용 캠페인 생성"""
    campaign = Campaign(
        id=str(uuid.uuid4()),
        title="Test Campaign",
        content="Test content",
        brand_name="Test Brand",
        created_by=test_user.id,
        close_at=date.today() + timedelta(days=7),
        is_public=True,
    )
    db_session.add(campaign)
    db_session.flush()
    return campaign


def test_get_campaign_by_id_success(db_session, test_campaign):
    """캠페인 ID로 조회 성공 테스트"""
    campaign = get_campaign_by_id(db_session, test_campaign.id)

    assert campaign is not None
    assert campaign.id == test_campaign.id


def test_get_campaign_by_id_not_found(db_session):
    """존재하지 않는 캠페인 조회 테스트"""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        get_campaign_by_id(db_session, str(uuid.uuid4()))

    assert exc_info.value.status_code == 404


def test_get_user_campaigns(db_session, test_user, test_campaign):
    """사용자 캠페인 목록 조회 테스트"""
    campaigns = get_user_campaigns(db_session, test_user.id)

    assert len(campaigns) == 1
    assert campaigns[0].id == test_campaign.id


def test_check_campaign_ownership_success(db_session, test_campaign, test_user):
    """캠페인 소유권 확인 성공 테스트"""
    campaign = check_campaign_ownership(
        db_session, campaign_id=test_campaign.id, user_id=test_user.id, user_role="brand"
    )

    assert campaign is not None
    assert campaign.id == test_campaign.id


def test_check_campaign_ownership_forbidden(db_session, test_campaign):
    """캠페인 소유권 확인 실패 테스트"""
    from fastapi import HTTPException

    from app.services.user_service import create_user

    other_user = create_user(
        db_session,
        name="Other User",
        email="other@example.com",
        password="password123",
        role=UserRole.BRAND,
        brand_name="Other Brand",
    )

    with pytest.raises(HTTPException) as exc_info:
        check_campaign_ownership(
            db_session, campaign_id=test_campaign.id, user_id=other_user.id, user_role="brand"
        )

    assert exc_info.value.status_code == 403


def test_check_application_exists(db_session, test_campaign):
    """지원 여부 확인 테스트"""
    from app.services.application_service import create_application
    from app.services.user_service import create_user

    showhost = create_user(
        db_session,
        name="Showhost",
        email="showhost@example.com",
        password="password123",
        role=UserRole.SHOWHOST,
    )

    # 지원 전
    assert check_application_exists(db_session, test_campaign.id, showhost.id) == False

    # 지원 후
    create_application(db_session, campaign_id=test_campaign.id, user_id=showhost.id)

    assert check_application_exists(db_session, test_campaign.id, showhost.id) == True


def test_get_campaigns_with_applied_status(db_session, test_user):
    """캠페인 목록 조회 (지원 여부 포함) 테스트"""
    # 캠페인 생성
    campaign = Campaign(
        id=str(uuid.uuid4()),
        title="Test Campaign",
        content="Test content",
        brand_name="Test Brand",
        created_by=test_user.id,
        close_at=date.today() + timedelta(days=7),
        is_public=True,
    )
    db_session.add(campaign)
    db_session.flush()

    # 지원서 생성
    from app.services.application_service import create_application
    from app.services.user_service import create_user

    showhost = create_user(
        db_session,
        name="Showhost",
        email="showhost@example.com",
        password="password123",
        role=UserRole.SHOWHOST,
    )

    create_application(db_session, campaign_id=campaign.id, user_id=showhost.id)

    # 조회
    campaigns, total, applied_ids = get_campaigns_with_applied_status(
        db_session, page=1, limit=10, user_id=showhost.id
    )

    assert len(campaigns) == 1
    assert campaign.id in applied_ids
