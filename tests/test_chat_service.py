"""
채팅 서비스 단위 테스트
"""
import pytest
from app.services.chat_service import ensure_chat_room
from app.models.chat import ChatRoom, ChatParticipant, ChatParticipantRole, ChatRoomStatus
from app.models.user import User, UserRole
import uuid


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
        brand_name="Test Brand"
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
        role=UserRole.SHOWHOST
    )


@pytest.fixture
def test_campaign_id():
    """테스트용 캠페인 ID"""
    return str(uuid.uuid4())


def test_ensure_chat_room_create_new(db_session, test_brand_user, test_showhost_user, test_campaign_id):
    """새 채팅방 생성 테스트"""
    room = ensure_chat_room(
        db_session,
        campaign_id=test_campaign_id,
        brand_user_id=test_brand_user.id,
        showhost_user_id=test_showhost_user.id
    )
    
    assert room is not None
    assert room.campaign_id == test_campaign_id
    assert room.brand_user_id == test_brand_user.id
    assert room.showhost_user_id == test_showhost_user.id
    assert room.status == ChatRoomStatus.ACTIVE
    
    # 참가자 확인
    participants = db_session.query(ChatParticipant).filter(
        ChatParticipant.room_id == room.id
    ).all()
    
    assert len(participants) == 2
    participant_user_ids = {p.user_id for p in participants}
    assert test_brand_user.id in participant_user_ids
    assert test_showhost_user.id in participant_user_ids


def test_ensure_chat_room_existing(db_session, test_brand_user, test_showhost_user, test_campaign_id):
    """기존 채팅방 조회 테스트"""
    # 첫 번째 생성
    room1 = ensure_chat_room(
        db_session,
        campaign_id=test_campaign_id,
        brand_user_id=test_brand_user.id,
        showhost_user_id=test_showhost_user.id
    )
    
    # 두 번째 호출 (기존 방 반환)
    room2 = ensure_chat_room(
        db_session,
        campaign_id=test_campaign_id,
        brand_user_id=test_brand_user.id,
        showhost_user_id=test_showhost_user.id
    )
    
    assert room1.id == room2.id
    
    # 참가자는 중복 생성되지 않아야 함
    participants = db_session.query(ChatParticipant).filter(
        ChatParticipant.room_id == room1.id
    ).all()
    
    assert len(participants) == 2


def test_ensure_chat_room_with_application_id(db_session, test_brand_user, test_showhost_user, test_campaign_id):
    """application_id를 포함한 채팅방 생성 테스트"""
    application_id = str(uuid.uuid4())
    
    room = ensure_chat_room(
        db_session,
        campaign_id=test_campaign_id,
        brand_user_id=test_brand_user.id,
        showhost_user_id=test_showhost_user.id,
        application_id=application_id
    )
    
    assert room.application_id == application_id


def test_ensure_chat_room_update_application_id(db_session, test_brand_user, test_showhost_user, test_campaign_id):
    """기존 채팅방에 application_id 추가 테스트"""
    # application_id 없이 생성
    room1 = ensure_chat_room(
        db_session,
        campaign_id=test_campaign_id,
        brand_user_id=test_brand_user.id,
        showhost_user_id=test_showhost_user.id
    )
    
    assert room1.application_id is None
    
    # application_id 추가
    application_id = str(uuid.uuid4())
    room2 = ensure_chat_room(
        db_session,
        campaign_id=test_campaign_id,
        brand_user_id=test_brand_user.id,
        showhost_user_id=test_showhost_user.id,
        application_id=application_id
    )
    
    assert room1.id == room2.id
    assert room2.application_id == application_id

