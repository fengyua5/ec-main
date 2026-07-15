from langgraph.graph import StateGraph, END

from app.domain.ai.workflow.state import ConversationState
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


def _route_after_intent(state: ConversationState) -> str:
    flow = state.get("flow", {})
    return flow.get("intent", "human") or "human"


def _route_after_faq(state: ConversationState) -> str:
    flow = state.get("flow", {})
    return flow.get("intent", "faq") or "faq"


def _route_after_refund(state: ConversationState) -> str:
    refund = state.get("skills", {}).get("refund", {})
    if all(k in refund for k in ("order_no", "reason", "amount")):
        return "check_order_mcp"
    return END


def _route_after_check(state: ConversationState) -> str:
    mcp = state.get("mcp", {})
    status = mcp.get("order_status", "")
    if status == "pending_delivery":
        return "process_refund_mcp"
    return END


def build_chat_graph() -> StateGraph:
    workflow = StateGraph(ConversationState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("handle_greeting", handle_greeting)
    workflow.add_node("retrieve_faq", retrieve_faq)
    workflow.add_node("answer_faq", answer_faq)
    workflow.add_node("collect_refund_info", collect_refund_info)
    workflow.add_node("process_refund", process_refund)
    workflow.add_node("check_order_mcp", check_order_mcp)
    workflow.add_node("process_refund_mcp", process_refund_mcp)
    workflow.add_node("handoff_human", handoff_human)

    workflow.set_entry_point("classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        _route_after_intent,
        {
            "greeting": "handle_greeting",
            "faq": "retrieve_faq",
            "refund": "collect_refund_info",
            "human": "handoff_human",
        },
    )

    workflow.add_conditional_edges(
        "retrieve_faq",
        _route_after_faq,
        {
            "faq": "answer_faq",
            "human": "handoff_human",
        },
    )

    workflow.add_edge("handle_greeting", END)
    workflow.add_edge("answer_faq", END)
    workflow.add_edge("process_refund", END)
    workflow.add_edge("handoff_human", END)

    workflow.add_conditional_edges(
        "collect_refund_info",
        _route_after_refund,
        {
            "check_order_mcp": "check_order_mcp",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "check_order_mcp",
        _route_after_check,
        {
            "process_refund_mcp": "process_refund_mcp",
            END: END,
        },
    )

    workflow.add_edge("process_refund_mcp", END)

    return workflow.compile()
