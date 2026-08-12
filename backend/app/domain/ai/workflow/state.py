from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    flow: dict
    skills: dict[str, Any]
    mcp: dict
    memory: str | None
