from langgraph.graph import StateGraph, END

from app.domain.ai.workflow.state import ConversationState
from app.domain.ai.workflow.nodes import (
    answer_faq,
    classify_intent,
    collect_refund_info,
    handle_greeting,
    handoff_human,
    process_refund,
    retrieve_faq,
)


def _route_after_intent(state: ConversationState) -> str:
    return state.get("intent", "human") or "human"


def _route_after_faq(state: ConversationState) -> str:
    return state.get("intent", "faq") or "faq"


def _route_after_refund(state: ConversationState) -> str:
    refund_info = state.get("refund_info", {})
    if all(k in refund_info for k in ("order_no", "reason", "amount")):
        return "process_refund"
    return END


def build_chat_graph() -> StateGraph:
    workflow = StateGraph(ConversationState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("handle_greeting", handle_greeting)
    workflow.add_node("retrieve_faq", retrieve_faq)
    workflow.add_node("answer_faq", answer_faq)
    workflow.add_node("collect_refund_info", collect_refund_info)
    workflow.add_node("process_refund", process_refund)
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
            "process_refund": "process_refund",
            END: END,
        },
    )

    return workflow.compile()
