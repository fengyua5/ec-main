from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
from app.models.user import Base
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


async def _fake_events(
    _db, _conversation_id: int, _user_message: str
) -> AsyncGenerator[dict, None]:
    yield {"type": "intent", "value": "faq"}
    yield {"type": "token", "content": "你好，有什么可以帮助你的？"}
    yield {"type": "done"}


async def _fake_done(
    _db, _conversation_id: int, _user_message: str
) -> AsyncGenerator[dict, None]:
    yield {"type": "done"}


def test_chat_streaming_response() -> None:
    with patch(
        "app.api.web.ai.ChatEngine.process_message",
        side_effect=_fake_events,
    ):
        response = client.post("/api/v1/web/ai/chat", json={"content": "你好"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert response.headers["x-accel-buffering"] == "no"

        lines = response.text.strip().split("\n\n")
        assert len(lines) == 3
        assert '"intent"' in lines[0] and '"faq"' in lines[0]
        assert "你好" in lines[1]
        assert '"done"' in lines[2]


def test_chat_new_conversation_on_missing_id() -> None:
    with patch(
        "app.api.web.ai.ChatEngine.process_message",
        side_effect=_fake_done,
    ):
        response = client.post("/api/v1/web/ai/chat", json={"content": "test"})
        assert response.status_code == 200


def test_list_conversations_empty() -> None:
    response = client.get("/api/v1/web/ai/conversations")
    assert response.status_code == 200
    assert response.json() == {"conversations": []}


def test_list_conversations_with_data() -> None:
    repo = ConversationRepository()
    db = SessionLocal()
    try:
        repo.create(db, buyer_id=1)
        repo.create(db, buyer_id=1)
    finally:
        db.close()

    response = client.get("/api/v1/web/ai/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["conversations"]) == 2


def test_get_messages_empty() -> None:
    repo = ConversationRepository()
    db = SessionLocal()
    try:
        conv = repo.create(db, buyer_id=1)
        conv_id = conv.id
    finally:
        db.close()

    response = client.get(f"/api/v1/web/ai/conversations/{conv_id}/messages")
    assert response.status_code == 200
    assert response.json() == {"messages": []}


def test_get_messages_with_limit_offset() -> None:
    db = SessionLocal()
    try:
        conv = ConversationRepository().create(db, buyer_id=1)
        cid = conv.id
        msg_repo = MessageRepository()
        for i in range(5):
            msg_repo.create(db, cid, "user", f"msg {i}")
    finally:
        db.close()

    response = client.get(
        f"/api/v1/web/ai/conversations/{cid}/messages",
        params={"limit": 2, "offset": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 2
