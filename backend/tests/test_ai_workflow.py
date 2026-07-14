import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.ai.workflow.state import ConversationState
from app.domain.ai.workflow.graph import build_chat_graph
from app.domain.ai.workflow.nodes import (
    classify_intent,
    handle_greeting,
    retrieve_faq,
    answer_faq,
    collect_refund_info,
    process_refund,
    handoff_human,
)
from app.domain.ai.workflow.engine import ChatEngine


def make_state(**overrides) -> ConversationState:
    defaults: ConversationState = {
        "messages": [],
        "intent": None,
        "confidence": 0.0,
        "refund_info": {},
        "faq_context": [],
        "response": "",
        "conversation_id": None,
    }
    defaults.update(overrides)
    return defaults


class TestState:
    def test_state_defaults(self) -> None:
        state = make_state()
        assert state["intent"] is None
        assert state["confidence"] == 0.0
        assert state["refund_info"] == {}
        assert state["faq_context"] == []
        assert state["response"] == ""
        assert state["conversation_id"] is None
        assert state["messages"] == []

    def test_state_with_values(self) -> None:
        state = make_state(intent="faq", confidence=0.9, response="hello")
        assert state["intent"] == "faq"
        assert state["confidence"] == 0.9
        assert state["response"] == "hello"


class TestGraph:
    def test_build_compiles(self) -> None:
        graph = build_chat_graph()
        assert graph is not None

    def test_has_all_nodes(self) -> None:
        graph = build_chat_graph()
        expected = {
            "classify_intent",
            "handle_greeting",
            "retrieve_faq",
            "answer_faq",
            "collect_refund_info",
            "process_refund",
            "handoff_human",
        }
        assert expected.issubset(graph.nodes)

    @pytest.mark.asyncio
    async def test_greeting_routing(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "greeting", "confidence": 0.95}'
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage
            graph = build_chat_graph()
            state = make_state(
                intent="greeting",
                messages=[HumanMessage(content="你好")],
            )
            result = await graph.ainvoke(state)
            assert result.get("response") != ""

    @pytest.mark.asyncio
    async def test_human_routing(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.ConversationRepository.update_status"
        ) as mock_update:
            mock_update.return_value = None
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "human", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage
            graph = build_chat_graph()
            state = make_state(
                intent="human",
                conversation_id=1,
                messages=[HumanMessage(content="转人工")],
            )
            result = await graph.ainvoke(state)
            assert "人工客服" in result.get("response", "")

    @pytest.mark.asyncio
    async def test_refund_collection_routing(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "refund", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage
            state = make_state(
                intent="refund",
                refund_info={"order_no": "123", "reason": "defective", "amount": "50"},
                messages=[HumanMessage(content="50")],
            )
            graph = build_chat_graph()
            result = await graph.ainvoke(state)
            assert "退单" in result.get("response", "")


class TestNodes:
    @pytest.mark.asyncio
    async def test_handle_greeting(self) -> None:
        state = make_state()
        result = await handle_greeting(state)
        assert "您好" in result["response"] or "你好" in result["response"]

    @pytest.mark.asyncio
    async def test_classify_intent_low_confidence_rollback(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "faq", "confidence": 0.3}'
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage

            state = make_state(messages=[HumanMessage(content="test")])
            result = await classify_intent(state)
            assert result["intent"] == "human"

    @pytest.mark.asyncio
    async def test_collect_refund_first_turn(self) -> None:
        state = make_state(refund_info={}, messages=[MagicMock(content="我要退款")])
        result = await collect_refund_info(state)
        assert "退款原因" in result["response"]
        assert result["refund_info"]["order_no"] == "我要退款"

    @pytest.mark.asyncio
    async def test_collect_refund_second_turn(self) -> None:
        state = make_state(
            refund_info={"order_no": "12345"},
            messages=[MagicMock(content="商品有问题")],
        )
        result = await collect_refund_info(state)
        assert "退款金额" in result["response"]
        assert result["refund_info"]["order_no"] == "12345"
        assert result["refund_info"]["reason"] == "商品有问题"

    @pytest.mark.asyncio
    async def test_collect_refund_all_filled(self) -> None:
        state = make_state(
            refund_info={"order_no": "123", "reason": "bad", "amount": "50"},
            messages=[MagicMock(content="50")],
        )
        result = await collect_refund_info(state)
        assert "response" not in result or result["response"] == ""

    @pytest.mark.asyncio
    async def test_process_refund(self) -> None:
        state = make_state()
        result = await process_refund(state)
        assert "退单" in result["response"]

    @pytest.mark.asyncio
    async def test_handoff_human(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.ConversationRepository.update_status"
        ):
            state = make_state(conversation_id=1)
            result = await handoff_human(state)
            assert "人工客服" in result["response"]

    @pytest.mark.asyncio
    async def test_retrieve_faq_empty(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.FaqRetriever"
        ) as mock_retriever_cls:
            mock_instance = MagicMock()
            mock_instance.retrieve.return_value = []
            mock_retriever_cls.return_value = mock_instance

            from langchain_core.messages import HumanMessage

            state = make_state(messages=[HumanMessage(content="test question")])
            result = await retrieve_faq(state)
            assert result["intent"] == "human"
            assert result["faq_context"] == []

    @pytest.mark.asyncio
    async def test_retrieve_faq_with_results(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.FaqRetriever"
        ) as mock_retriever_cls:
            mock_instance = MagicMock()
            mock_instance.retrieve.return_value = [
                {"content": "FAQ content", "score": 0.85, "source": "faq.md"}
            ]
            mock_retriever_cls.return_value = mock_instance

            from langchain_core.messages import HumanMessage

            state = make_state(messages=[HumanMessage(content="test question")])
            result = await retrieve_faq(state)
            assert len(result["faq_context"]) == 1
            assert "intent" not in result  # intent unchanged

    @pytest.mark.asyncio
    async def test_answer_faq(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.faq_prompt"
        ) as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content="根据 FAQ，退货政策是 30 天内。"
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage

            state = make_state(
                faq_context=[{"content": "退货政策 30 天", "score": 0.9}],
                messages=[HumanMessage(content="退货政策是什么")],
            )
            result = await answer_faq(state)
            assert "退货" in result["response"]


class TestEngine:
    @pytest.mark.asyncio
    async def test_process_message_yields_events(self) -> None:
        with patch(
            "app.domain.ai.workflow.engine.MessageRepository"
        ) as mock_msg_repo, patch(
            "app.domain.ai.workflow.engine.ConversationRepository"
        ) as mock_conv_repo, patch(
            "app.domain.ai.workflow.graph.StateGraph"
        ):
            mock_msg_instance = MagicMock()
            mock_msg_instance.list_by_conversation.return_value = []
            mock_msg_instance.create.return_value = MagicMock()
            mock_msg_repo.return_value = mock_msg_instance
            mock_conv_repo.return_value = MagicMock()

            from sqlalchemy.orm import Session

            engine = ChatEngine()
            engine.graph = MagicMock()
            engine.graph.ainvoke = AsyncMock(
                return_value={
                    "intent": "greeting",
                    "response": "你好！",
                    "refund_info": {},
                }
            )

            events = []
            async for event in engine.process_message(
                MagicMock(spec=Session), 1, "你好"
            ):
                events.append(event)

            assert len(events) == 3
            assert events[0]["type"] == "intent"
            assert events[1]["type"] == "token"
            assert events[1]["content"] == "你好！"
            assert events[2]["type"] == "done"


class TestGraphRoutingLogic:
    def test_route_after_intent_greeting(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(intent="greeting")) == "greeting"

    def test_route_after_intent_faq(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(intent="faq")) == "faq"

    def test_route_after_intent_refund(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(intent="refund")) == "refund"

    def test_route_after_intent_human(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(intent="human")) == "human"

    def test_route_after_intent_none_fallback(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(intent=None)) == "human"

    def test_route_after_refund_complete(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_refund
        state = make_state(refund_info={"order_no": "1", "reason": "a", "amount": "b"})
        assert _route_after_refund(state) == "process_refund"

    def test_route_after_refund_incomplete(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_refund
        from langgraph.graph import END
        state = make_state(refund_info={"order_no": "1"})
        assert _route_after_refund(state) == END

    def test_route_after_faq_faq(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_faq
        assert _route_after_faq(make_state(intent="faq")) == "faq"

    def test_route_after_faq_human(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_faq
        assert _route_after_faq(make_state(intent="human")) == "human"
