import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from app.domain.ai.workflow.engine import ChatEngine
from app.models.user import Base
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


def _make_mock_graph() -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value={
        "flow": {"intent": "greeting", "response": "你好！"},
        "skills": {"refund": {}, "after_sale": {}, "faq": {"context": []}},
        "mcp": {},
    })
    return mock_graph


class TestMemoryInjection:
    @pytest.mark.asyncio
    async def test_injects_memory_as_system_message(self) -> None:
        db = SessionLocal()
        try:
            from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
            conv_repo = ConversationRepository()
            msg_repo = MessageRepository()
            conv = conv_repo.create(db, buyer_id=1)
            msg_repo.create(db, conv.id, "user", "你好")

            with patch("app.domain.ai.workflow.engine.get_memory_block") as mock_get, \
                 patch("app.domain.ai.workflow.engine.trim_history") as mock_trim, \
                 patch.object(ChatEngine, "_detect_memory_request", return_value=False):
                mock_get.return_value = "以下是用户长期信息\n【称呼/身份】李女士"
                mock_trim.return_value = MagicMock(
                    messages=[HumanMessage(content="你好")],
                    trimmed=False,
                )

                mock_graph = _make_mock_graph()
                mock_graph.ainvoke.return_value = {
                    "flow": {"intent": "greeting", "response": "你好李女士！"},
                    "skills": {"refund": {}, "after_sale": {}, "faq": {"context": []}},
                    "mcp": {},
                }

                with patch("app.domain.ai.workflow.engine.build_chat_graph", return_value=mock_graph):
                    engine_inst = ChatEngine()
                    events = []
                    async for event in engine_inst.process_message(db, conv.id, "你好"):
                        events.append(event)

                    call_args = mock_graph.ainvoke.call_args
                    state = call_args[0][0]
                    msgs = state["messages"]
                    assert any(isinstance(m, SystemMessage) and "李女士" in m.content for m in msgs)
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_no_memory_no_injection(self) -> None:
        db = SessionLocal()
        try:
            from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
            conv_repo = ConversationRepository()
            msg_repo = MessageRepository()
            conv = conv_repo.create(db, buyer_id=2)
            msg_repo.create(db, conv.id, "user", "你好")

            with patch("app.domain.ai.workflow.engine.get_memory_block") as mock_get, \
                 patch("app.domain.ai.workflow.engine.trim_history") as mock_trim, \
                 patch.object(ChatEngine, "_detect_memory_request", return_value=False):
                mock_get.return_value = None
                mock_trim.return_value = MagicMock(
                    messages=[HumanMessage(content="你好")],
                    trimmed=False,
                )

                mock_graph = _make_mock_graph()
                with patch("app.domain.ai.workflow.engine.build_chat_graph", return_value=mock_graph):
                    engine_inst = ChatEngine()
                    events = []
                    async for event in engine_inst.process_message(db, conv.id, "你好"):
                        events.append(event)

                    call_args = mock_graph.ainvoke.call_args
                    state = call_args[0][0]
                    msgs = state["messages"]
                    assert not any(isinstance(m, SystemMessage) and "长期信息" in m.content for m in msgs)
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_explicit_memory_request_triggers_update(self) -> None:
        db = SessionLocal()
        try:
            from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
            conv_repo = ConversationRepository()
            msg_repo = MessageRepository()
            conv = conv_repo.create(db, buyer_id=3)
            msg_repo.create(db, conv.id, "user", "我叫张三")

            with patch("app.domain.ai.workflow.engine.get_memory_block") as mock_get, \
                 patch("app.domain.ai.workflow.engine.trim_history") as mock_trim, \
                 patch("app.domain.ai.workflow.engine.update_memory") as mock_update, \
                 patch.object(ChatEngine, "_detect_memory_request", return_value=True):
                mock_get.return_value = None
                mock_trim.return_value = MagicMock(
                    messages=[HumanMessage(content="我叫张三")],
                    trimmed=False,
                )
                mock_update.return_value = MagicMock(changed=True, content="【称呼/身份】张三", error=None)

                mock_graph = _make_mock_graph()
                with patch("app.domain.ai.workflow.engine.build_chat_graph", return_value=mock_graph):
                    engine_inst = ChatEngine()
                    events = []
                    async for event in engine_inst.process_message(db, conv.id, "记住我叫张三"):
                        events.append(event)

                    mock_update.assert_called_once()
        finally:
            db.close()
