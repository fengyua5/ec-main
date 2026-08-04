import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.ai.workflow.state import ConversationState
from app.domain.ai.workflow.graph import build_chat_graph
from app.domain.ai.workflow.nodes import (
    answer_faq,
    check_order_mcp,
    classify_intent,
    collect_refund_info,
    handle_greeting,
    handoff_human,
    process_refund,
    process_refund_mcp,
    retrieve_faq,
)
from app.domain.ai.workflow.engine import ChatEngine


def make_state(**overrides) -> ConversationState:
    defaults: ConversationState = {
        "messages": [],
        "flow": {"intent": None, "confidence": 0.0, "conversation_id": None, "response": ""},
        "skills": {"refund": {}, "faq": {"context": []}},
        "mcp": {},
    }
    defaults.update(overrides)
    return defaults


class TestState:
    def test_state_defaults(self) -> None:
        state = make_state()
        assert state["flow"]["intent"] is None
        assert state["flow"]["confidence"] == 0.0
        assert state["skills"]["refund"] == {}
        assert state["skills"]["faq"]["context"] == []
        assert state["flow"]["response"] == ""
        assert state["flow"]["conversation_id"] is None
        assert state["messages"] == []

    def test_state_with_values(self) -> None:
        state = make_state(flow={"intent": "faq", "confidence": 0.9, "response": "hello"})
        assert state["flow"]["intent"] == "faq"
        assert state["flow"]["confidence"] == 0.9
        assert state["flow"]["response"] == "hello"


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
                flow={"intent": "greeting"},
                messages=[HumanMessage(content="你好")],
            )
            result = await graph.ainvoke(state)
            assert result.get("flow", {}).get("response") != ""

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
                flow={"intent": "human", "conversation_id": 1},
                messages=[HumanMessage(content="转人工")],
            )
            result = await graph.ainvoke(state)
            assert "人工客服" in result.get("flow", {}).get("response", "")

    @pytest.mark.asyncio
    async def test_refund_collection_routing(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery"}
            )
            mock_instance.process_refund = AsyncMock(
                return_value={"success": True}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "refund", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage
            state = make_state(
                flow={"intent": "refund"},
                skills={"refund": {"order_no": "123", "reason": "defective", "amount": "50"}},
                messages=[HumanMessage(content="50")],
            )
            graph = build_chat_graph()
            result = await graph.ainvoke(state)
            assert "退款成功" in result.get("flow", {}).get("response", "")

    @pytest.mark.asyncio
    async def test_refund_multi_turn_flow(self) -> None:
        """多轮退单流程：提供信息 → 继续收集 → 提交处理，中途不因意图分类偏移而中断"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery"}
            )
            mock_instance.process_refund = AsyncMock(
                return_value={"success": True}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            from langchain_core.messages import HumanMessage

            # Turn 1: 用户有部分退款信息，classify_intent 应跳过 LLM 直接路由到 collect_refund_info
            state = make_state(
                flow={"intent": None},
                skills={"refund": {"order_no": "ORD-PEND-001"}},
                messages=[HumanMessage(content="商品有质量问题")],
            )
            graph = build_chat_graph()
            result = await graph.ainvoke(state)
            # 应收集到 reason，并提示输入金额（不直接提交）
            assert result["skills"]["refund"]["order_no"] == "ORD-PEND-001"
            assert result["skills"]["refund"]["reason"] == "商品有质量问题"
            assert "退款金额" in result.get("flow", {}).get("response", "")

            # Turn 2: 用户提供金额，此时 reason 已收集，amount 尚缺
            state2 = make_state(
                flow={"intent": None},
                skills={"refund": result["skills"]["refund"]},
                messages=[
                    HumanMessage(content="商品有质量问题"),
                    HumanMessage(content="99.9"),
                ],
            )
            result2 = await graph.ainvoke(state2)
            # 应收集到 amount，并路由到 check_order_mcp → process_refund_mcp
            assert result2["skills"]["refund"]["amount"] == "99.9"
            assert "退款成功" in result2.get("flow", {}).get("response", "")


class TestNodes:
    @pytest.mark.asyncio
    async def test_handle_greeting(self) -> None:
        state = make_state()
        result = await handle_greeting(state)
        assert "您好" in result["flow"]["response"] or "你好" in result["flow"]["response"]

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
            assert result["flow"]["intent"] == "human"

    @pytest.mark.asyncio
    async def test_classify_intent_skips_llm_when_refund_in_progress(self) -> None:
        """退单进行中时，classify_intent 应直接返回 refund，不调 LLM"""
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"refund": {"order_no": "12345"}},
            messages=[HumanMessage(content="商品有问题")],
        )
        result = await classify_intent(state)
        assert result["flow"]["intent"] == "refund"
        assert result["flow"]["confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_classify_intent_proceeds_normally_when_refund_empty(self) -> None:
        """无退单信息时，classify_intent 应正常调 LLM"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "faq", "confidence": 0.8}'
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage

            state = make_state(messages=[HumanMessage(content="退货政策是什么")])
            result = await classify_intent(state)
            assert result["flow"]["intent"] == "faq"

    @pytest.mark.asyncio
    async def test_collect_refund_first_turn(self) -> None:
        state = make_state(skills={"refund": {}}, messages=[MagicMock(content="我要退款")])
        result = await collect_refund_info(state)
        assert "退款原因" in result["flow"]["response"]
        assert result["skills"]["refund"]["order_no"] == "我要退款"

    @pytest.mark.asyncio
    async def test_collect_refund_second_turn(self) -> None:
        state = make_state(
            skills={"refund": {"order_no": "12345"}},
            messages=[MagicMock(content="商品有问题")],
        )
        result = await collect_refund_info(state)
        assert "退款金额" in result["flow"]["response"]
        assert result["skills"]["refund"]["order_no"] == "12345"
        assert result["skills"]["refund"]["reason"] == "商品有问题"

    @pytest.mark.asyncio
    async def test_collect_refund_all_filled(self) -> None:
        state = make_state(
            skills={"refund": {"order_no": "123", "reason": "bad", "amount": "50"}},
            messages=[MagicMock(content="50")],
        )
        result = await collect_refund_info(state)
        assert "flow" not in result

    @pytest.mark.asyncio
    async def test_process_refund(self) -> None:
        state = make_state()
        result = await process_refund(state)
        assert "退单" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_handoff_human(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.ConversationRepository.update_status"
        ):
            state = make_state(flow={"conversation_id": 1})
            result = await handoff_human(state)
            assert "人工客服" in result["flow"]["response"]

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
            assert result["flow"]["intent"] == "human"
            assert result["skills"]["faq"]["context"] == []

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
            assert len(result["skills"]["faq"]["context"]) == 1
            assert "flow" not in result  # intent unchanged (flow not set)

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
                skills={"faq": {"context": [{"content": "退货政策 30 天", "score": 0.9}]}},
                messages=[HumanMessage(content="退货政策是什么")],
            )
            result = await answer_faq(state)
            assert "退货" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_answer_faq_passes_source_evidence(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.faq_prompt"
        ) as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content="根据 FAQ，退货政策是 30 天内。（依据：faq.md）"
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage

            state = make_state(
                skills={"faq": {"context": [{"content": "退货政策 30 天", "score": 0.9, "source": "faq.md"}]}},
                messages=[HumanMessage(content="退货政策是什么")],
            )
            result = await answer_faq(state)
            assert "退货" in result["flow"]["response"]

            called_args = mock_chain.ainvoke.call_args
            assert called_args is not None
            context_text = called_args[0][0]["context"]
            assert "[来源: faq.md]" in context_text

    @pytest.mark.asyncio
    async def test_answer_faq_without_source_uses_plain_content(self) -> None:
        with patch(
            "app.domain.ai.workflow.nodes.faq_prompt"
        ) as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(content="回答")
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage

            state = make_state(
                skills={"faq": {"context": [{"content": "退货政策 30 天", "score": 0.9}]}},
                messages=[HumanMessage(content="退货政策是什么")],
            )
            await answer_faq(state)

            called_args = mock_chain.ainvoke.call_args
            context_text = called_args[0][0]["context"]
            assert context_text == "退货政策 30 天"


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
                    "flow": {"intent": "greeting", "response": "你好！"},
                    "skills": {"refund": {}},
                }
            )

            events = []
            async for event in engine.process_message(
                MagicMock(spec=Session), 1, "你好"
            ):
                events.append(event)

            assert events[0]["type"] == "status"
            assert events[0]["content"] == "正在查找中..."
            assert events[1]["type"] == "intent"
            assert "".join(e["content"] for e in events if e["type"] == "token") == "你好！"
            assert events[-1]["type"] == "done"

    @pytest.mark.asyncio
    async def test_process_message_streams_tokens_in_chunks(self) -> None:
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
                    "flow": {"intent": "faq", "response": "一二三四五六七八九十"},
                    "skills": {"refund": {}},
                }
            )

            tokens = []
            async for event in engine.process_message(
                MagicMock(spec=Session), 1, "退货政策是什么"
            ):
                if event["type"] == "token":
                    tokens.append(event["content"])

            assert len(tokens) > 1
            assert max(len(t) for t in tokens) <= 4
            assert "".join(tokens) == "一二三四五六七八九十"


class TestGraphRoutingLogic:
    def test_route_after_intent_greeting(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": "greeting"})) == "greeting"

    def test_route_after_intent_faq(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": "faq"})) == "faq"

    def test_route_after_intent_refund(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": "refund"})) == "refund"

    def test_route_after_intent_human(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": "human"})) == "human"

    def test_route_after_intent_none_fallback(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": None})) == "human"

    def test_route_after_refund_complete(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_refund
        state = make_state(skills={"refund": {"order_no": "1", "reason": "a", "amount": "b"}})
        assert _route_after_refund(state) == "check_order_mcp"

    def test_route_after_refund_incomplete(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_refund
        from langgraph.graph import END
        state = make_state(skills={"refund": {"order_no": "1"}})
        assert _route_after_refund(state) == END

    def test_route_after_faq_faq(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_faq
        assert _route_after_faq(make_state(flow={"intent": "faq"})) == "faq"

    def test_route_after_faq_human(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_faq
        assert _route_after_faq(make_state(flow={"intent": "human"})) == "human"


class TestMcpNodes:
    @pytest.mark.asyncio
    async def test_check_order_mcp_pending_delivery(self) -> None:
        """pending_delivery 状态应路由到 process_refund_mcp，不设置 flow.response"""
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "pending_delivery", "amount": "199.00", "message": "订单查询成功"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"refund": {"order_no": "ORD-PENDING-001", "reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "pending_delivery"
            assert "response" not in result.get("flow", {})

    @pytest.mark.asyncio
    async def test_check_order_mcp_in_delivery(self) -> None:
        """in_delivery 状态应拒绝退款，设置 flow.response"""
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "in_delivery", "amount": "199.00", "message": "订单查询成功"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"refund": {"order_no": "ORD-DELIVERY-001", "reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "in_delivery"
            assert "配送中" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_check_order_mcp_delivered(self) -> None:
        """delivered 状态应提示通过售后渠道"""
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "delivered", "amount": "199.00", "message": "订单查询成功"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"refund": {"order_no": "ORD-DONE-001", "reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "delivered"
            assert "售后" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_check_order_mcp_not_found(self) -> None:
        """不存在的订单应提示"""
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "unknown", "message": "订单不存在"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"refund": {"order_no": "ORD-NOEXIST-001", "reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "not_found"
            assert "未找到订单" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_check_order_mcp_missing_order_no(self) -> None:
        """无订单号应提示"""
        state = make_state(
            skills={"refund": {"reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
        )
        result = await check_order_mcp(state)
        assert result["mcp"]["order_status"] == "not_found"
        assert "缺少订单号" in result["mcp"].get("error", "")
        assert "未提供订单号" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_check_order_mcp_error_fallback(self) -> None:
        """MCP 异常应降级，设置 flow.intent=human"""
        mock_client = MagicMock()
        mock_client.check_order.side_effect = RuntimeError("MCP 连接失败")

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"refund": {"order_no": "ORD-ERROR-001", "reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "error"
            assert result["flow"]["intent"] == "human"

    @pytest.mark.asyncio
    async def test_process_refund_mcp_success(self) -> None:
        """process_refund_mcp 应返回退款成功"""
        mock_client = MagicMock()
        mock_client.process_refund = AsyncMock(return_value={"success": True, "message": "退款已处理"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"refund": {"order_no": "ORD-PENDING-001", "reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await process_refund_mcp(state)
            assert result["mcp"]["refund_success"] is True
            assert "退款成功" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_process_refund_mcp_failure(self) -> None:
        """process_refund_mcp 应处理失败情况"""
        mock_client = MagicMock()
        mock_client.process_refund = AsyncMock(return_value={"success": False, "message": "订单状态不允许退款"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"refund": {"order_no": "ORD-DELIVERY-001", "reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await process_refund_mcp(state)
            assert result["mcp"]["refund_success"] is False
            assert "退款失败" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_process_refund_mcp_exception(self) -> None:
        """process_refund_mcp 异常应降级转人工"""
        mock_client = MagicMock()
        mock_client.process_refund.side_effect = RuntimeError("MCP 内部错误")

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"refund": {"order_no": "ORD-ERROR-001", "reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await process_refund_mcp(state)
            assert result["mcp"]["refund_success"] is False
            assert result["flow"]["intent"] == "human"
