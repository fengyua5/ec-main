import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.domain.ai.memory.memory_service import update_memory, get_memory_block
from app.models.user import Base
from app.db.session import engine, SessionLocal

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


class TestUpdateMemory:
    @pytest.mark.asyncio
    async def test_changed_persists_new_memory(self) -> None:
        db = SessionLocal()
        try:
            with patch("app.domain.ai.memory.memory_service.get_chat_llm") as mock_llm_cls, \
                 patch("app.domain.ai.memory.memory_service.memory_update_prompt") as mock_prompt:
                mock_chain = AsyncMock()
                mock_chain.ainvoke.return_value = MagicMock(
                    content='{"changed": true, "content": "【称呼/身份】李女士\\n【偏好】偏好纯棉"}'
                )
                mock_prompt.__or__.return_value = mock_chain

                from langchain_core.messages import HumanMessage, AIMessage
                messages = [
                    HumanMessage(content="我叫李女士，我喜欢纯棉的"),
                    AIMessage(content="好的，李女士，纯棉的确实舒适。"),
                ]

                result = await update_memory(db, buyer_id=1, conversation_messages=messages)
                assert result.changed is True
                assert "李女士" in result.content

                from app.domain.ai.memory.memory_repo import get_by_buyer
                mem = get_by_buyer(db, buyer_id=1)
                assert mem is not None
                assert "李女士" in mem.content
                assert mem.version == 1
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_unchanged_does_not_persist(self) -> None:
        db = SessionLocal()
        try:
            with patch("app.domain.ai.memory.memory_service.get_chat_llm") as mock_llm_cls, \
                 patch("app.domain.ai.memory.memory_service.memory_update_prompt") as mock_prompt:
                mock_chain = AsyncMock()
                mock_chain.ainvoke.return_value = MagicMock(
                    content='{"changed": false}'
                )
                mock_prompt.__or__.return_value = mock_chain

                from langchain_core.messages import HumanMessage, AIMessage
                messages = [
                    HumanMessage(content="今天天气怎么样"),
                    AIMessage(content="抱歉，我是客服，无法回答天气问题。"),
                ]

                result = await update_memory(db, buyer_id=99, conversation_messages=messages)
                assert result.changed is False

                from app.domain.ai.memory.memory_repo import get_by_buyer
                mem = get_by_buyer(db, buyer_id=99)
                assert mem is None
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_llm_failure_returns_error(self) -> None:
        db = SessionLocal()
        try:
            with patch("app.domain.ai.memory.memory_service.get_chat_llm") as mock_llm_cls, \
                 patch("app.domain.ai.memory.memory_service.memory_update_prompt") as mock_prompt:
                mock_chain = AsyncMock()
                mock_chain.ainvoke.side_effect = RuntimeError("ollama down")
                mock_prompt.__or__.return_value = mock_chain

                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content="test")]

                result = await update_memory(db, buyer_id=1, conversation_messages=messages)
                assert result.changed is False
                assert result.error is not None
        finally:
            db.close()


class TestGetMemoryBlock:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_memory(self) -> None:
        db = SessionLocal()
        try:
            result = await get_memory_block(db, buyer_id=999)
            assert result is None
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_returns_content_when_exists(self) -> None:
        db = SessionLocal()
        try:
            from app.domain.ai.memory.memory_repo import upsert
            upsert(db, buyer_id=1, content="【称呼/身份】王五", expected_version=0)
            result = await get_memory_block(db, buyer_id=1)
            assert result is not None
            assert "王五" in result
        finally:
            db.close()
