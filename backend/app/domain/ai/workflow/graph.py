from langgraph.graph import StateGraph, END

from app.domain.ai.workflow.state import ConversationState
from app.domain.ai.workflow.nodes import (
    answer_faq,
    check_order_mcp,
    classify_intent,
    collect_order_no,
    collect_refund_info,
    collect_update_order_info,
    enter_after_sale,
    handle_greeting,
    handoff_human,
    process_refund,
    process_refund_mcp,
    query_order_mcp,
    retrieve_faq,
    update_order_mcp,
)


def _route_after_intent(state: ConversationState) -> str:
    flow = state.get("flow", {})
    return flow.get("intent", "human") or "human"


def _route_after_faq(state: ConversationState) -> str:
    flow = state.get("flow", {})
    return flow.get("intent", "faq") or "faq"


def _route_after_after_sale(state: ConversationState) -> str:
    after_sale = state.get("skills", {}).get("after_sale", {})
    sub_intent = after_sale.get("sub_intent", "query_order")
    return sub_intent if sub_intent in ("query_order", "update_order", "refund") else "query_order"


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


def _route_after_update_collect(state: ConversationState) -> str:
    update_order = state.get("skills", {}).get("after_sale", {}).get("update_order", {})
    if all(k in update_order for k in ("order_no", "status")):
        return "update_order_mcp"
    return END


def build_chat_graph() -> StateGraph:
    workflow = StateGraph(ConversationState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("handle_greeting", handle_greeting)
    workflow.add_node("retrieve_faq", retrieve_faq)
    workflow.add_node("answer_faq", answer_faq)
    workflow.add_node("enter_after_sale", enter_after_sale)
    workflow.add_node("collect_order_no", collect_order_no)
    workflow.add_node("query_order_mcp", query_order_mcp)
    workflow.add_node("collect_update_order_info", collect_update_order_info)
    workflow.add_node("update_order_mcp", update_order_mcp)
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
            "after_sale": "enter_after_sale",
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

    workflow.add_conditional_edges(
        "enter_after_sale",
        _route_after_after_sale,
        {
            "query_order": "collect_order_no",
            "update_order": "collect_update_order_info",
            "refund": "collect_refund_info",
        },
    )

    workflow.add_edge("handle_greeting", END)
    workflow.add_edge("answer_faq", END)
    workflow.add_edge("process_refund", END)
    workflow.add_edge("handoff_human", END)
    workflow.add_edge("collect_order_no", "query_order_mcp")
    workflow.add_edge("query_order_mcp", END)

    workflow.add_conditional_edges(
        "collect_update_order_info",
        _route_after_update_collect,
        {
            "update_order_mcp": "update_order_mcp",
            END: END,
        },
    )

    workflow.add_edge("update_order_mcp", END)

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
