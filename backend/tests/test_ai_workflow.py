import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.ai.workflow.state import ConversationState
from app.domain.ai.workflow.graph import build_chat_graph
from app.domain.ai.workflow.nodes import (
    answer_faq,
    check_order_mcp,
    classify_intent,
    collect_order_no,
    collect_refund_info,
    collect_update_order_info,
    confirm_after_sale,
    enter_after_sale,
    ensure_order_no,
    handle_greeting,
    handoff_human,
    process_refund,
    process_refund_mcp,
    query_order_mcp,
    retrieve_faq,
    update_order_mcp,
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
            "enter_after_sale",
            "ensure_order_no",
            "collect_order_no",
            "query_order_mcp",
            "collect_update_order_info",
            "update_order_mcp",
            "confirm_after_sale",
            "cancel_order_mcp",
            "check_order_mcp",
            "process_refund_mcp",
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
        """退款收集路由：订单号 → 原因/金额 → 确认 → 退款"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls, patch(
            "app.domain.ai.workflow.nodes.create_case"
        ) as mock_create_case:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery", "buyer_id": 7}
            )
            mock_instance.process_refund = AsyncMock(
                return_value={"success": True, "message": "退款成功"}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "refund", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()

            # Turn 1: 订单号 + 原因 → 提取订单号并询问金额
            result1 = await graph.ainvoke(
                make_state(messages=[HumanMessage(content="退款 ORD-1001 商品坏了")])
            )
            assert result1["skills"]["after_sale"]["order_no"] == "ORD-1001"
            assert "退款金额" in result1.get("flow", {}).get("response", "")

            # Turn 2: 金额 → 查单通过 → 询问确认（未执行退款）
            result2 = await graph.ainvoke(
                make_state(
                    skills={"refund": result1["skills"]["refund"], "after_sale": result1["skills"]["after_sale"]},
                    messages=[HumanMessage(content="退款 ORD-1001 商品坏了"), HumanMessage(content="199")],
                )
            )
            assert result2["skills"]["refund"]["order_no"] == "ORD-1001"
            assert result2["skills"]["refund"]["amount"] == "199"
            assert "确认退款" in result2.get("flow", {}).get("response", "")
            mock_instance.process_refund.assert_not_called()

            # Turn 3: 确认 → 退款成功，以持久化的 buyer_id 落售后 case
            result3 = await graph.ainvoke(
                make_state(
                    skills={"refund": result2["skills"]["refund"], "after_sale": result2["skills"]["after_sale"]},
                    messages=[HumanMessage(content="退款 ORD-1001 商品坏了"), HumanMessage(content="199"), HumanMessage(content="确认")],
                )
            )
            assert result3["mcp"]["refund_success"] is True
            assert "退款成功" in result3.get("flow", {}).get("response", "")
            mock_create_case.assert_called_once()
            assert mock_create_case.call_args.kwargs["buyer_id"] == 7

    @pytest.mark.asyncio
    async def test_refund_requires_confirmation(self) -> None:
        """退款需确认后才执行：确认前不调用 process_refund"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls, patch(
            "app.domain.ai.workflow.nodes.create_case"
        ) as mock_create_case:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery", "buyer_id": 7}
            )
            mock_instance.process_refund = AsyncMock(
                return_value={"success": True, "message": "退款成功"}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "refund", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()

            # Turn 1: 退款信息完整 → 查单通过 → 停在确认环节，未执行退款
            state = make_state(
                skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-888"}, "refund": {"reason": "不想要了", "amount": "199"}},
                messages=[HumanMessage(content="确认退款")],
            )
            result = await graph.ainvoke(state)
            assert "确认退款" in result.get("flow", {}).get("response", "")
            mock_instance.process_refund.assert_not_called()

            # Turn 2: 确认 → 退款成功，以持久化的 buyer_id 落售后 case
            state2 = make_state(
                skills={"refund": result["skills"]["refund"], "after_sale": result["skills"]["after_sale"]},
                messages=[HumanMessage(content="确认退款"), HumanMessage(content="确认")],
            )
            result2 = await graph.ainvoke(state2)
            assert result2["mcp"]["refund_success"] is True
            assert "退款成功" in result2.get("flow", {}).get("response", "")
            mock_create_case.assert_called_once()
            assert mock_create_case.call_args.kwargs["buyer_id"] == 7

    @pytest.mark.asyncio
    async def test_refund_multi_turn_flow(self) -> None:
        """多轮退款：订单号 → 原因 → 金额 → 确认，中途不因意图分类偏移而中断"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls, patch(
            "app.domain.ai.workflow.nodes.create_case"
        ) as mock_create_case:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery", "buyer_id": 7}
            )
            mock_instance.process_refund = AsyncMock(
                return_value={"success": True, "message": "退款成功"}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "refund", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()

            # Turn 1: 订单号 → 提取并询问金额
            result1 = await graph.ainvoke(
                make_state(messages=[HumanMessage(content="退款 ORD-1001")])
            )
            assert result1["skills"]["after_sale"]["order_no"] == "ORD-1001"
            assert "退款金额" in result1.get("flow", {}).get("response", "")

            # Turn 2: 原因 + 金额 → 查单 → 询问确认
            result2 = await graph.ainvoke(
                make_state(
                    skills={"refund": result1["skills"]["refund"], "after_sale": result1["skills"]["after_sale"]},
                    messages=[HumanMessage(content="退款 ORD-1001"), HumanMessage(content="商品坏了 199")],
                )
            )
            assert result2["skills"]["refund"]["reason"] == "退款 ORD-1001"
            assert result2["skills"]["refund"]["amount"] == "商品坏了 199"
            assert "确认退款" in result2.get("flow", {}).get("response", "")

            # Turn 3: 确认 → 退款成功，以持久化的 buyer_id 落售后 case
            result3 = await graph.ainvoke(
                make_state(
                    skills={"refund": result2["skills"]["refund"], "after_sale": result2["skills"]["after_sale"]},
                    messages=[HumanMessage(content="退款 ORD-1001"), HumanMessage(content="商品坏了 199"), HumanMessage(content="确认")],
                )
            )
            assert result3["mcp"]["refund_success"] is True
            assert "退款成功" in result3.get("flow", {}).get("response", "")
            mock_create_case.assert_called_once()
            assert mock_create_case.call_args.kwargs["buyer_id"] == 7

    @pytest.mark.asyncio
    async def test_cancel_order_full_flow(self) -> None:
        """cancel_order：查单通过 → 确认 → 取消成功"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls, patch(
            "app.domain.ai.workflow.nodes.create_case"
        ) as mock_create_case:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery", "buyer_id": 7}
            )
            mock_instance.update_order_status = AsyncMock(
                return_value={"success": True, "message": "ok"}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "cancel_order", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()

            # Turn 1: 提供订单号 → 查单 → 询问确认
            result = await graph.ainvoke(
                make_state(messages=[HumanMessage(content="取消订单 ORD-777")])
            )
            assert "确认" in result.get("flow", {}).get("response", "")
            assert result["skills"]["after_sale"]["order_no"] == "ORD-777"

            # Turn 2: 确认 → 取消成功，以持久化的 buyer_id 落售后 case
            result2 = await graph.ainvoke(
                make_state(
                    skills={"after_sale": result["skills"]["after_sale"]},
                    messages=[HumanMessage(content="取消订单 ORD-777"), HumanMessage(content="确认")],
                )
            )
            assert result2["mcp"]["cancel_success"] is True
            assert "取消" in result2.get("flow", {}).get("response", "")
            mock_create_case.assert_called_once()
            assert mock_create_case.call_args.kwargs["buyer_id"] == 7

    @pytest.mark.asyncio
    async def test_cancel_order_rejected_when_in_delivery(self) -> None:
        """配送中订单取消被拒"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "in_delivery", "buyer_id": 7}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "cancel_order", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()
            result = await graph.ainvoke(
                make_state(messages=[HumanMessage(content="取消订单 ORD-777")])
            )
            assert "无法取消" in result.get("flow", {}).get("response", "")

    @pytest.mark.asyncio
    async def test_query_order_full_flow(self) -> None:
        """after_sale(query_order)：查订单全流程"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls:
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={
                    "status": "delivered",
                    "amount": "299.00",
                    "created_at": "2026-01-01 10:00:00",
                }
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "query_order", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            state = make_state(
                messages=[HumanMessage(content="查一下订单 ORD-999")],
            )
            graph = build_chat_graph()
            result = await graph.ainvoke(state)
            assert "ORD-999" in result.get("flow", {}).get("response", "")
            assert "已送达" in result.get("flow", {}).get("response", "")

    @pytest.mark.asyncio
    async def test_update_order_full_flow(self) -> None:
        """after_sale(update_order)：收集订单号 → 收集目标状态 → 调 update_order_status"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls:
            mock_instance = MagicMock()
            mock_instance.update_order_status = AsyncMock(
                return_value={"success": True, "message": "ok"}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "update_order", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            # Turn 1: 只给订单号，收集到后停在 END（未收集状态）
            state = make_state(messages=[HumanMessage(content="把订单 ORD-456 状态改一下")])
            graph = build_chat_graph()
            result = await graph.ainvoke(state)
            assert result["skills"]["after_sale"]["update_order"]["order_no"] == "ORD-456"
            assert "状态" in result.get("flow", {}).get("response", "")

            # Turn 2: 给出目标状态，子意图已持久化，进入 update_order_mcp
            state2 = make_state(
                skills={"after_sale": result["skills"]["after_sale"]},
                messages=[
                    HumanMessage(content="把订单 ORD-456 状态改一下"),
                    HumanMessage(content="已送达"),
                ],
            )
            result2 = await graph.ainvoke(state2)
            assert result2["mcp"]["update_success"] is True
            assert "ORD-456" in result2.get("flow", {}).get("response", "")

    @pytest.mark.asyncio
    async def test_confirm_after_sale_no_then_new_refund(self) -> None:
        """退款被否后 refund/after_sale 槽位应清空，新一轮退款需重新收集原因/金额，不复用旧值"""
        with patch(
            "app.domain.ai.workflow.nodes.intent_prompt"
        ) as mock_prompt, patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_sub_prompt, patch(
            "app.domain.ai.workflow.nodes.MCPClient"
        ) as mock_mcp_cls, patch(
            "app.domain.ai.workflow.nodes.create_case"
        ):
            mock_instance = MagicMock()
            mock_instance.check_order = AsyncMock(
                return_value={"status": "pending_delivery", "buyer_id": 7}
            )
            mock_mcp_cls.get_instance.return_value = mock_instance

            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"intent": "after_sale", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            mock_sub_chain = AsyncMock()
            mock_sub_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "refund", "confidence": 0.9}'
            )
            mock_sub_prompt.__or__.return_value = mock_sub_chain

            from langchain_core.messages import HumanMessage

            graph = build_chat_graph()

            # 第一轮：退款信息完整，确认时回复「否」→ refund/after_sale 槽位应清空
            result1 = await graph.ainvoke(
                make_state(
                    skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-1"}, "refund": {"order_no": "ORD-1", "reason": "商品坏了", "amount": "199"}},
                    messages=[HumanMessage(content="退款 ORD-1"), HumanMessage(content="商品坏了 199"), HumanMessage(content="否")],
                )
            )
            assert "order_no" not in result1["skills"]["after_sale"]
            assert "sub_intent" not in result1["skills"]["after_sale"]
            assert result1["skills"]["refund"] == {}

            # 第二轮：新一轮退款（不同订单/原因），应重新收集原因，不保留旧值
            result2 = await graph.ainvoke(
                make_state(
                    skills={"refund": result1["skills"]["refund"], "after_sale": result1["skills"]["after_sale"]},
                    messages=[HumanMessage(content="退款 ORD-1"), HumanMessage(content="商品坏了 199"), HumanMessage(content="否"), HumanMessage(content="退款 ORD-2 不想要了")],
                )
            )
            assert result2["skills"]["refund"]["order_no"] == "ORD-2"
            assert result2["skills"]["refund"]["reason"] == "退款 ORD-2 不想要了"
            assert "amount" not in result2["skills"]["refund"]
            assert "退款金额" in result2.get("flow", {}).get("response", "")


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
        """退单进行中时，classify_intent 应直接返回 after_sale + sub_intent=refund，不调 LLM"""
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"refund": {"order_no": "12345"}},
            messages=[HumanMessage(content="商品有问题")],
        )
        result = await classify_intent(state)
        assert result["flow"]["intent"] == "after_sale"
        assert result["flow"]["sub_intent"] == "refund"
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
        state = make_state(
            skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-123"}},
            messages=[MagicMock(content="商品坏了")],
        )
        result = await collect_refund_info(state)
        assert "退款金额" in result["flow"]["response"]
        assert result["skills"]["refund"]["order_no"] == "ORD-123"
        assert result["skills"]["refund"]["reason"] == "商品坏了"

    @pytest.mark.asyncio
    async def test_collect_refund_second_turn(self) -> None:
        state = make_state(
            skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-123"}, "refund": {"reason": "商品坏了"}},
            messages=[MagicMock(content="99.9")],
        )
        result = await collect_refund_info(state)
        assert "flow" not in result
        assert result["skills"]["refund"]["order_no"] == "ORD-123"
        assert result["skills"]["refund"]["amount"] == "99.9"

    @pytest.mark.asyncio
    async def test_collect_refund_all_filled(self) -> None:
        state = make_state(
            skills={"refund": {"order_no": "ORD-123", "reason": "bad", "amount": "50"}},
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

    @pytest.mark.asyncio
    async def test_enter_after_sale_uses_flow_sub_intent(self) -> None:
        """短路时 flow.sub_intent 已确定，应跳过子意图 LLM 分类"""
        from langchain_core.messages import HumanMessage

        state = make_state(
            flow={"intent": "after_sale", "sub_intent": "refund"},
            skills={"after_sale": {}},
            messages=[HumanMessage(content="商品有问题")],
        )
        result = await enter_after_sale(state)
        assert result["skills"]["after_sale"]["sub_intent"] == "refund"

    @pytest.mark.asyncio
    async def test_enter_after_sale_uses_persisted_sub_intent(self) -> None:
        """多轮中 skills.after_sale.sub_intent 已存在，应跳过 LLM 分类"""
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "update_order"}},
            messages=[HumanMessage(content="改订单")],
        )
        result = await enter_after_sale(state)
        assert result["skills"]["after_sale"]["sub_intent"] == "update_order"

    @pytest.mark.asyncio
    async def test_enter_after_sale_classifies_via_llm(self) -> None:
        """无既有子意图时，应通过 sub_intent_prompt 分类"""
        with patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "query_order", "confidence": 0.9}'
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage

            state = make_state(messages=[HumanMessage(content="帮我查一下订单")])
            result = await enter_after_sale(state)
            assert result["skills"]["after_sale"]["sub_intent"] == "query_order"

    @pytest.mark.asyncio
    async def test_enter_after_sale_low_confidence_defaults_query(self) -> None:
        """子意图置信度过低时默认 query_order"""
        with patch(
            "app.domain.ai.workflow.nodes.sub_intent_prompt"
        ) as mock_prompt:
            mock_chain = AsyncMock()
            mock_chain.ainvoke.return_value = MagicMock(
                content='{"sub_intent": "refund", "confidence": 0.2}'
            )
            mock_prompt.__or__.return_value = mock_chain

            from langchain_core.messages import HumanMessage

            state = make_state(messages=[HumanMessage(content="随便问问")])
            result = await enter_after_sale(state)
            assert result["skills"]["after_sale"]["sub_intent"] == "query_order"

    @pytest.mark.asyncio
    async def test_enter_after_sale_no_message_defaults_query(self) -> None:
        """无用户消息时默认 query_order"""
        state = make_state(messages=[])
        result = await enter_after_sale(state)
        assert result["skills"]["after_sale"]["sub_intent"] == "query_order"

    @pytest.mark.asyncio
    async def test_enter_after_sale_keeps_other_skills(self) -> None:
        """enter_after_sale 不应覆盖 skills 中的 refund 等信息"""
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"refund": {"order_no": "12345"}, "after_sale": {}},
            messages=[HumanMessage(content="商品有问题")],
        )
        result = await enter_after_sale(state)
        assert result["skills"]["refund"]["order_no"] == "12345"

    @pytest.mark.asyncio
    async def test_ensure_order_no_matches_pattern(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "query_order"}},
            messages=[HumanMessage(content="查一下 ORD-123")],
        )
        result = await ensure_order_no(state)
        assert result["skills"]["after_sale"]["order_no"] == "ORD-123"

    @pytest.mark.asyncio
    async def test_ensure_order_no_asks_when_missing(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "query_order"}},
            messages=[HumanMessage(content="帮我查订单")],
        )
        result = await ensure_order_no(state)
        assert "请提供订单号" in result["flow"]["response"]
        assert "order_no" not in result["skills"]["after_sale"]

    @pytest.mark.asyncio
    async def test_ensure_order_no_skips_when_present(self) -> None:
        state = make_state(
            skills={"after_sale": {"sub_intent": "query_order", "order_no": "ORD-999"}},
            messages=[],
        )
        result = await ensure_order_no(state)
        assert result["skills"]["after_sale"]["order_no"] == "ORD-999"

    @pytest.mark.asyncio
    async def test_confirm_after_sale_yes(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "cancel_order", "order_no": "ORD-1"}},
            messages=[HumanMessage(content="确认")],
        )
        result = await confirm_after_sale(state)
        assert result["skills"]["after_sale"]["confirmed"] is True

    @pytest.mark.asyncio
    async def test_confirm_after_sale_no(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "cancel_order", "order_no": "ORD-1"}, "refund": {"order_no": "ORD-1", "reason": "商品坏了", "amount": "199"}},
            messages=[HumanMessage(content="不要")],
        )
        result = await confirm_after_sale(state)
        assert "取消" in result["flow"]["response"]
        assert "order_no" not in result["skills"]["after_sale"]
        assert "sub_intent" not in result["skills"]["after_sale"]
        assert "confirmed" not in result["skills"]["after_sale"]
        assert result["skills"]["refund"] == {}

    @pytest.mark.asyncio
    async def test_confirm_after_sale_asks_again(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "cancel_order", "order_no": "ORD-1"}},
            messages=[HumanMessage(content="随便")],
        )
        result = await confirm_after_sale(state)
        assert "确认" in result["flow"]["response"]
        assert "confirmed" not in result["skills"]["after_sale"]

    @pytest.mark.asyncio
    async def test_collect_order_no_from_slot(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "query_order", "order_no": "ORD-123"}},
            messages=[HumanMessage(content="ORD-123")],
        )
        result = await collect_order_no(state)
        assert result["skills"]["after_sale"]["query_order"]["order_no"] == "ORD-123"

    @pytest.mark.asyncio
    async def test_query_order_mcp_success(self) -> None:
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(
            return_value={
                "status": "delivered",
                "amount": "299.00",
                "created_at": "2026-01-01 10:00:00",
            }
        )

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "query_order", "query_order": {"order_no": "ORD-123"}}},
            )
            result = await query_order_mcp(state)
            assert result["mcp"]["order_status"] == "delivered"
            assert "ORD-123" in result["flow"]["response"]
            assert "已送达" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_query_order_mcp_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "not_found"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "query_order", "query_order": {"order_no": "ORD-NOPE"}}},
            )
            result = await query_order_mcp(state)
            assert result["mcp"]["order_status"] == "not_found"
            assert "未找到订单" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_query_order_mcp_missing_order_no(self) -> None:
        state = make_state(skills={"after_sale": {"sub_intent": "query_order"}})
        result = await query_order_mcp(state)
        assert result["mcp"]["order_status"] == "not_found"
        assert "未提供订单号" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_query_order_mcp_exception_degrades_to_human(self) -> None:
        mock_client = MagicMock()
        mock_client.check_order.side_effect = RuntimeError("MCP 连接失败")

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "query_order", "query_order": {"order_no": "ORD-ERR"}}},
            )
            result = await query_order_mcp(state)
            assert result["mcp"]["order_status"] == "error"
            assert result["flow"]["intent"] == "human"

    @pytest.mark.asyncio
    async def test_collect_update_order_first_turn(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "update_order", "order_no": "ORD-456"}},
            messages=[HumanMessage(content="ORD-456")],
        )
        result = await collect_update_order_info(state)
        assert result["skills"]["after_sale"]["update_order"]["order_no"] == "ORD-456"
        assert "状态" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_collect_update_order_second_turn(self) -> None:
        from langchain_core.messages import HumanMessage

        state = make_state(
            skills={"after_sale": {"sub_intent": "update_order", "update_order": {"order_no": "ORD-456"}}},
            messages=[HumanMessage(content="已送达")],
        )
        result = await collect_update_order_info(state)
        assert result["skills"]["after_sale"]["update_order"]["status"] == "已送达"
        assert "flow" not in result

    @pytest.mark.asyncio
    async def test_update_order_mcp_success(self) -> None:
        mock_client = MagicMock()
        mock_client.update_order_status = AsyncMock(return_value={"success": True, "message": "ok"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "update_order", "update_order": {"order_no": "ORD-456", "status": "已送达"}}},
            )
            result = await update_order_mcp(state)
            assert result["mcp"]["update_success"] is True
            assert "ORD-456" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_update_order_mcp_failure(self) -> None:
        mock_client = MagicMock()
        mock_client.update_order_status = AsyncMock(return_value={"success": False, "message": "状态不合法"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "update_order", "update_order": {"order_no": "ORD-456", "status": "已送达"}}},
            )
            result = await update_order_mcp(state)
            assert result["mcp"]["update_success"] is False
            assert "修改失败" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_update_order_mcp_missing_info(self) -> None:
        state = make_state(skills={"after_sale": {"sub_intent": "update_order"}})
        result = await update_order_mcp(state)
        assert result["mcp"]["update_success"] is False
        assert "缺少订单号" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_update_order_mcp_exception_degrades_to_human(self) -> None:
        mock_client = MagicMock()
        mock_client.update_order_status.side_effect = RuntimeError("MCP 内部错误")

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "update_order", "update_order": {"order_no": "ORD-456", "status": "已送达"}}},
            )
            result = await update_order_mcp(state)
            assert result["mcp"]["update_success"] is False
            assert result["flow"]["intent"] == "human"


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

    @pytest.mark.asyncio
    async def test_process_message_persists_cleared_refund_and_after_sale(self) -> None:
        """确认「否」清空 refund/after_sale 后，engine 应持久化空槽位以清除跨轮残留"""
        with patch(
            "app.domain.ai.workflow.engine.MessageRepository"
        ) as mock_msg_repo, patch(
            "app.domain.ai.workflow.engine.ConversationRepository"
        ) as mock_conv_repo, patch(
            "app.domain.ai.workflow.graph.StateGraph"
        ):
            prev_refund = MagicMock(sender="system", msg_type="refund_info", content=json.dumps({"order_no": "ORD-1", "reason": "商品坏了", "amount": "199"}, ensure_ascii=False))
            prev_after_sale = MagicMock(sender="system", msg_type="after_sale_info", content=json.dumps({"sub_intent": "refund", "order_no": "ORD-1"}, ensure_ascii=False))
            mock_msg_instance = MagicMock()
            mock_msg_instance.list_by_conversation.return_value = [prev_refund, prev_after_sale]
            mock_msg_instance.create.return_value = MagicMock()
            mock_msg_repo.return_value = mock_msg_instance
            mock_conv_repo.return_value = MagicMock()

            engine = ChatEngine()
            engine.graph = MagicMock()
            engine.graph.ainvoke = AsyncMock(
                return_value={
                    "flow": {"intent": "after_sale", "response": "已为您取消「退款」操作。"},
                    "skills": {"refund": {}, "after_sale": {}},
                }
            )

            from sqlalchemy.orm import Session

            async for _ in engine.process_message(MagicMock(spec=Session), 1, "否"):
                pass

            system_creates = [c for c in mock_msg_instance.create.call_args_list if c.args[2] == "system"]
            assert {c.kwargs.get("msg_type") for c in system_creates} == {"refund_info", "after_sale_info"}


class TestGraphRoutingLogic:
    def test_route_after_intent_greeting(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": "greeting"})) == "greeting"

    def test_route_after_intent_faq(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": "faq"})) == "faq"

    def test_route_after_intent_after_sale(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": "after_sale"})) == "after_sale"

    def test_route_after_intent_human(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": "human"})) == "human"

    def test_route_after_intent_none_fallback(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_intent
        assert _route_after_intent(make_state(flow={"intent": None})) == "human"

    def test_route_after_after_sale_query(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_after_sale
        state = make_state(skills={"after_sale": {"sub_intent": "query_order"}})
        assert _route_after_after_sale(state) == "query_order"

    def test_route_after_after_sale_update(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_after_sale
        state = make_state(skills={"after_sale": {"sub_intent": "update_order"}})
        assert _route_after_after_sale(state) == "update_order"

    def test_route_after_after_sale_refund(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_after_sale
        state = make_state(skills={"after_sale": {"sub_intent": "refund"}})
        assert _route_after_after_sale(state) == "refund"

    def test_route_after_after_sale_cancel(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_after_sale
        state = make_state(skills={"after_sale": {"sub_intent": "cancel_order"}})
        assert _route_after_after_sale(state) == "cancel_order"

    def test_route_after_after_sale_default_query(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_after_sale
        assert _route_after_after_sale(make_state()) == "query_order"

    def test_route_after_ensure_missing(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_ensure
        from langgraph.graph import END
        state = make_state(skills={"after_sale": {"sub_intent": "query_order"}})
        assert _route_after_ensure(state) == END

    def test_route_after_ensure_present_query(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_ensure
        state = make_state(skills={"after_sale": {"sub_intent": "query_order", "order_no": "ORD-1"}})
        assert _route_after_ensure(state) == "query_order"

    def test_route_after_ensure_present_cancel(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_ensure
        state = make_state(skills={"after_sale": {"sub_intent": "cancel_order", "order_no": "ORD-1"}})
        assert _route_after_ensure(state) == "cancel_order"

    def test_route_after_confirm_cancel(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_confirm
        state = make_state(skills={"after_sale": {"sub_intent": "cancel_order", "confirmed": True}})
        assert _route_after_confirm(state) == "cancel_order_mcp"

    def test_route_after_confirm_refund(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_confirm
        state = make_state(skills={"after_sale": {"sub_intent": "refund", "confirmed": True}})
        assert _route_after_confirm(state) == "process_refund_mcp"

    def test_route_after_confirm_not_confirmed(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_confirm
        from langgraph.graph import END
        state = make_state(skills={"after_sale": {"sub_intent": "cancel_order"}})
        assert _route_after_confirm(state) == END

    def test_route_after_update_collect_complete(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_update_collect
        state = make_state(skills={"after_sale": {"update_order": {"order_no": "1", "status": "已送达"}}})
        assert _route_after_update_collect(state) == "update_order_mcp"

    def test_route_after_update_collect_incomplete(self) -> None:
        from app.domain.ai.workflow.graph import _route_after_update_collect
        from langgraph.graph import END
        state = make_state(skills={"after_sale": {"update_order": {"order_no": "1"}}})
        assert _route_after_update_collect(state) == END

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
        """pending_delivery 状态应记录 buyer_id 到持久化槽位并路由到确认环节，不设置 flow.response"""
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "pending_delivery", "buyer_id": 7, "amount": "199.00", "message": "订单查询成功"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-PENDING-001"}, "refund": {"reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "pending_delivery"
            assert result["mcp"]["order_buyer_id"] == 7
            assert result["skills"]["after_sale"]["order_buyer_id"] == 7
            assert "response" not in result.get("flow", {})

    @pytest.mark.asyncio
    async def test_check_order_mcp_in_delivery(self) -> None:
        """in_delivery 状态应拒绝退款，设置 flow.response"""
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "in_delivery", "amount": "199.00", "message": "订单查询成功"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-DELIVERY-001"}, "refund": {"reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "in_delivery"
            assert "无法退款" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_check_order_mcp_delivered(self) -> None:
        """delivered 状态应提示无法退款"""
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "delivered", "amount": "199.00", "message": "订单查询成功"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-DONE-001"}, "refund": {"reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "delivered"
            assert "无法退款" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_check_order_mcp_not_found(self) -> None:
        """不存在的订单应提示"""
        mock_client = MagicMock()
        mock_client.check_order = AsyncMock(return_value={"status": "unknown", "message": "订单不存在"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client):
            state = make_state(
                skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-NOEXIST-001"}, "refund": {"reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "not_found"
            assert "未找到订单" in result["flow"]["response"]

    @pytest.mark.asyncio
    async def test_check_order_mcp_missing_order_no(self) -> None:
        """无订单号应提示"""
        state = make_state(
            skills={"after_sale": {"sub_intent": "refund"}, "refund": {"reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
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
                skills={"after_sale": {"sub_intent": "refund", "order_no": "ORD-ERROR-001"}, "refund": {"reason": "不想要了", "amount": "199.00"}, "faq": {"context": []}},
            )
            result = await check_order_mcp(state)
            assert result["mcp"]["order_status"] == "error"
            assert result["flow"]["intent"] == "human"

    @pytest.mark.asyncio
    async def test_process_refund_mcp_success(self) -> None:
        """process_refund_mcp 应返回退款成功，并以持久化的 buyer_id 落售后 case"""
        mock_client = MagicMock()
        mock_client.process_refund = AsyncMock(return_value={"success": True, "message": "退款已处理"})

        with patch("app.domain.ai.workflow.nodes.MCPClient.get_instance", return_value=mock_client), patch(
            "app.domain.ai.workflow.nodes.create_case"
        ) as mock_create_case:
            state = make_state(
                skills={"refund": {"order_no": "ORD-PENDING-001", "reason": "不想要了", "amount": "199.00"}, "after_sale": {"order_buyer_id": 7}, "faq": {"context": []}},
            )
            result = await process_refund_mcp(state)
            assert result["mcp"]["refund_success"] is True
            assert "退款成功" in result["flow"]["response"]
            mock_create_case.assert_called_once()
            call_kwargs = mock_create_case.call_args.kwargs
            assert call_kwargs["order_no"] == "ORD-PENDING-001"
            assert call_kwargs["buyer_id"] == 7
            assert call_kwargs["case_type"] == "refund"
            assert "order_buyer_id" not in result["skills"]["after_sale"]

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
