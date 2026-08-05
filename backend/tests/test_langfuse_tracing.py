from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings
from app.domain.ai.llm.tracing import (
    get_langfuse_client,
    create_chat_trace,
    is_langfuse_enabled,
    record_retrieval,
    _reset_langfuse,
)


def test_langfuse_config_defaults() -> None:
    from app.core.config import settings
    assert settings.langfuse_public_key == ""
    assert settings.langfuse_secret_key == ""
    assert settings.langfuse_host == "http://localhost:5000"


def _configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-test")
    monkeypatch.setattr(settings, "langfuse_host", "http://localhost:5000")


def _unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "langfuse_public_key", "")
    monkeypatch.setattr(settings, "langfuse_secret_key", "")
    monkeypatch.setattr(settings, "langfuse_host", "http://localhost:5000")


def test_disabled_when_not_configured(monkeypatch) -> None:
    _unconfigured(monkeypatch)
    _reset_langfuse()
    assert is_langfuse_enabled() is False
    assert get_langfuse_client() is None
    handler, trace_id = create_chat_trace()
    assert handler is None
    assert trace_id is None


def test_disabled_when_secret_missing(monkeypatch) -> None:
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "")
    _reset_langfuse()
    assert is_langfuse_enabled() is False
    assert get_langfuse_client() is None


def test_handler_created_when_configured(monkeypatch) -> None:
    _configured(monkeypatch)
    _reset_langfuse()
    try:
        with patch("app.domain.ai.llm.tracing.Langfuse") as mock_client_cls, \
             patch("app.domain.ai.llm.tracing.CallbackHandler") as mock_handler_cls:
            mock_client = MagicMock()
            mock_client.create_trace_id.return_value = "trace-123"
            mock_client_cls.return_value = mock_client
            mock_handler_cls.return_value = MagicMock()

            client = get_langfuse_client()
            assert client is not None
            assert mock_client_cls.called

            handler, trace_id = create_chat_trace()
            assert handler is not None
            assert trace_id == "trace-123"
            mock_handler_cls.assert_called_once_with(
                public_key="pk-test",
                trace_context={"trace_id": "trace-123"},
            )
    finally:
        _reset_langfuse()


def test_record_retrieval_uses_trace_id(monkeypatch) -> None:
    _configured(monkeypatch)
    _reset_langfuse()
    try:
        with patch("app.domain.ai.llm.tracing.Langfuse") as mock_client_cls:
            mock_client = MagicMock()
            mock_span = MagicMock()
            mock_client.start_observation.return_value = mock_span
            mock_client_cls.return_value = mock_client

            record_retrieval(
                "trace-abc",
                query="退货政策是什么",
                intent="faq",
                hits=[{"content": "退货 30 天", "score": 0.9, "source": "faq.md"}],
            )

            mock_client.start_observation.assert_called_once()
            call_kwargs = mock_client.start_observation.call_args.kwargs
            assert call_kwargs["name"] == "retrieve_faq"
            assert call_kwargs["as_type"] == "retriever"
            assert call_kwargs["trace_context"] == {"trace_id": "trace-abc"}
            assert call_kwargs["input"] == {"query": "退货政策是什么"}
            assert call_kwargs["output"]["intent"] == "faq"
            assert call_kwargs["metadata"] == {"hit_count": 1}
            mock_span.end.assert_called_once()
    finally:
        _reset_langfuse()


def test_process_message_passes_handler_and_records_retrieval() -> None:
    import asyncio

    from sqlalchemy.orm import Session

    from app.domain.ai.workflow.engine import ChatEngine

    mock_handler = MagicMock()
    with patch(
        "app.domain.ai.workflow.engine.create_chat_trace",
        return_value=(mock_handler, "trace-123"),
    ), patch("app.domain.ai.workflow.engine.record_retrieval") as mock_record, \
         patch("app.domain.ai.workflow.engine.MessageRepository") as mock_msg_repo, \
         patch("app.domain.ai.workflow.engine.ConversationRepository"), \
         patch("app.domain.ai.workflow.graph.StateGraph"):
        mock_msg_instance = MagicMock()
        mock_msg_instance.list_by_conversation.return_value = []
        mock_msg_instance.create.return_value = MagicMock()
        mock_msg_repo.return_value = mock_msg_instance

        engine = ChatEngine()
        engine.graph = MagicMock()
        engine.graph.ainvoke = AsyncMock(
            return_value={
                "flow": {"intent": "faq", "response": "答案"},
                "skills": {
                    "faq": {"context": [
                        {"content": "退货 30 天", "score": 0.9, "source": "faq.md"}
                    ]}
                },
            }
        )

        events = []

        async def _collect() -> None:
            async for e in engine.process_message(
                MagicMock(spec=Session), 1, "退货政策是什么"
            ):
                events.append(e)

        asyncio.run(_collect())

        assert engine.graph.ainvoke.call_args.kwargs["config"]["callbacks"] == [
            mock_handler
        ]
        mock_record.assert_called_once_with(
            "trace-123",
            query="退货政策是什么",
            intent="faq",
            hits=[{"content": "退货 30 天", "score": 0.9, "source": "faq.md"}],
        )
        assert events[0]["type"] == "status"


def test_process_message_skips_tracing_when_disabled() -> None:
    import asyncio

    from sqlalchemy.orm import Session

    from app.domain.ai.workflow.engine import ChatEngine

    with patch(
        "app.domain.ai.workflow.engine.create_chat_trace",
        return_value=(None, None),
    ), patch("app.domain.ai.workflow.engine.record_retrieval") as mock_record, \
         patch("app.domain.ai.workflow.engine.MessageRepository") as mock_msg_repo, \
         patch("app.domain.ai.workflow.engine.ConversationRepository"), \
         patch("app.domain.ai.workflow.graph.StateGraph"):
        mock_msg_instance = MagicMock()
        mock_msg_instance.list_by_conversation.return_value = []
        mock_msg_instance.create.return_value = MagicMock()
        mock_msg_repo.return_value = mock_msg_instance

        engine = ChatEngine()
        engine.graph = MagicMock()
        engine.graph.ainvoke = AsyncMock(
            return_value={"flow": {"intent": "greeting", "response": "你好"}, "skills": {"faq": {"context": []}}}
        )

        events = []

        async def _collect() -> None:
            async for e in engine.process_message(
                MagicMock(spec=Session), 1, "你好"
            ):
                events.append(e)

        asyncio.run(_collect())

        assert "config" not in engine.graph.ainvoke.call_args.kwargs
        mock_record.assert_not_called()
