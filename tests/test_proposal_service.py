"""
제안 서비스 단위 테스트
"""

import uuid
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.models.portfolio import Portfolio
from app.models.proposal import ProposalStatus
from app.models.user import UserRole
from app.services.proposal_service import (
    create_proposal,
    get_received_proposals,
    get_sent_proposals,
    withdraw_proposal,
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
def test_portfolio(db_session, test_showhost_user):
    """테스트용 포트폴리오 생성"""
    portfolio = Portfolio(
        id=str(uuid.uuid4()),
        user_id=test_showhost_user.id,
        name="Test Portfolio",
        is_published=True,
    )
    db_session.add(portfolio)
    db_session.flush()
    return portfolio


def test_create_proposal_success(db_session, test_brand_user, test_showhost_user, test_portfolio):
    """제안 생성 성공 테스트"""
    proposal = create_proposal(
        db_session,
        target_portfolio_id=test_portfolio.id,
        proposer_id=test_brand_user.id,
        brand_name="Test Brand",
        shooting_date=date.today() + timedelta(days=7),
        reply_deadline=date.today() + timedelta(days=3),
        fee=100000,
        content="Test proposal",
    )

    assert proposal is not None
    assert proposal.target_portfolio_id == test_portfolio.id
    assert proposal.proposer_id == test_brand_user.id
    assert proposal.target_showhost_id == test_showhost_user.id
    assert proposal.status == ProposalStatus.PENDING


def test_create_proposal_portfolio_not_found(db_session, test_brand_user):
    """존재하지 않는 포트폴리오에 제안 생성 실패 테스트"""
    with pytest.raises(HTTPException) as exc_info:
        create_proposal(
            db_session,
            target_portfolio_id=str(uuid.uuid4()),
            proposer_id=test_brand_user.id,
            brand_name="Test Brand",
            shooting_date=date.today() + timedelta(days=7),
            reply_deadline=date.today() + timedelta(days=3),
        )

    assert exc_info.value.status_code == 404


def test_get_sent_proposals(db_session, test_brand_user, test_portfolio):
    """보낸 제안 목록 조회 테스트"""
    # 제안 생성
    proposal = create_proposal(
        db_session,
        target_portfolio_id=test_portfolio.id,
        proposer_id=test_brand_user.id,
        brand_name="Test Brand",
        shooting_date=date.today() + timedelta(days=7),
        reply_deadline=date.today() + timedelta(days=3),
    )

    # 조회
    proposals, total = get_sent_proposals(db_session, proposer_id=test_brand_user.id)

    assert len(proposals) == 1
    assert total == 1
    assert proposals[0].id == proposal.id


def test_get_sent_proposals_with_filter(db_session, test_brand_user, test_portfolio):
    """상태 필터를 사용한 보낸 제안 목록 조회 테스트"""
    # 제안 생성
    create_proposal(
        db_session,
        target_portfolio_id=test_portfolio.id,
        proposer_id=test_brand_user.id,
        brand_name="Test Brand",
        shooting_date=date.today() + timedelta(days=7),
        reply_deadline=date.today() + timedelta(days=3),
    )

    # PENDING 상태 필터
    proposals, total = get_sent_proposals(
        db_session, proposer_id=test_brand_user.id, status_filter=ProposalStatus.PENDING
    )

    assert len(proposals) == 1

    # ACCEPTED 상태 필터 (결과 없음)
    proposals, total = get_sent_proposals(
        db_session, proposer_id=test_brand_user.id, status_filter=ProposalStatus.ACCEPTED
    )

    assert len(proposals) == 0


def test_get_received_proposals(db_session, test_brand_user, test_showhost_user, test_portfolio):
    """받은 제안 목록 조회 테스트"""
    # 제안 생성
    proposal = create_proposal(
        db_session,
        target_portfolio_id=test_portfolio.id,
        proposer_id=test_brand_user.id,
        brand_name="Test Brand",
        shooting_date=date.today() + timedelta(days=7),
        reply_deadline=date.today() + timedelta(days=3),
    )

    # 조회
    proposals, total = get_received_proposals(db_session, showhost_id=test_showhost_user.id)

    assert len(proposals) == 1
    assert total == 1
    assert proposals[0].id == proposal.id


def test_withdraw_proposal_success(db_session, test_brand_user, test_portfolio):
    """제안 철회 성공 테스트"""
    # 제안 생성
    proposal = create_proposal(
        db_session,
        target_portfolio_id=test_portfolio.id,
        proposer_id=test_brand_user.id,
        brand_name="Test Brand",
        shooting_date=date.today() + timedelta(days=7),
        reply_deadline=date.today() + timedelta(days=3),
    )

    # 철회
    withdrawn = withdraw_proposal(
        db_session, proposal_id=proposal.id, proposer_id=test_brand_user.id
    )

    assert withdrawn.status == ProposalStatus.WITHDRAWN


def test_withdraw_proposal_forbidden(db_session, test_brand_user, test_portfolio):
    """권한 없는 사용자의 제안 철회 실패 테스트"""
    from app.services.user_service import create_user

    # 제안 생성
    proposal = create_proposal(
        db_session,
        target_portfolio_id=test_portfolio.id,
        proposer_id=test_brand_user.id,
        brand_name="Test Brand",
        shooting_date=date.today() + timedelta(days=7),
        reply_deadline=date.today() + timedelta(days=3),
    )

    # 다른 사용자 생성
    other_user = create_user(
        db_session,
        name="Other User",
        email="other@example.com",
        password="password123",
        role=UserRole.BRAND,
        brand_name="Other Brand",
    )

    # 철회 시도
    with pytest.raises(HTTPException) as exc_info:
        withdraw_proposal(db_session, proposal_id=proposal.id, proposer_id=other_user.id)

    assert exc_info.value.status_code == 403
