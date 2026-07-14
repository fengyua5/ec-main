from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: Optional[str]
    confidence: float
    refund_info: dict
    faq_context: list[dict]
    response: str
    conversation_id: Optional[int]
