import json
from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
from app.domain.ai.workflow.graph import build_chat_graph
from app.domain.ai.workflow.state import ConversationState


class ChatEngine:

    def __init__(self) -> None:
        self.graph = build_chat_graph()
        self.conv_repo = ConversationRepository()
        self.msg_repo = MessageRepository()

    async def process_message(
        self,
        db: Session,
        conversation_id: int,
        user_message: str,
    ) -> AsyncGenerator[dict, None]:
        db_messages = self.msg_repo.list_by_conversation(db, conversation_id)

        lc_messages: list = []
        refund_info: dict = {}
        for msg in db_messages:
            if msg.sender == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.sender == "ai":
                lc_messages.append(AIMessage(content=msg.content))
            elif msg.sender == "system" and msg.msg_type == "refund_info":
                try:
                    refund_info = json.loads(msg.content)
                except (json.JSONDecodeError, TypeError):
                    refund_info = {}

        lc_messages.append(HumanMessage(content=user_message))

        state: ConversationState = {
            "messages": lc_messages,
            "intent": None,
            "confidence": 0.0,
            "refund_info": refund_info,
            "faq_context": [],
            "response": "",
            "conversation_id": conversation_id,
        }

        result = await self.graph.ainvoke(state)

        self.msg_repo.create(db, conversation_id, "user", user_message)
        if result.get("response"):
            self.msg_repo.create(db, conversation_id, "ai", result["response"])

        updated_refund = result.get("refund_info", {})
        if updated_refund and updated_refund != refund_info:
            self.msg_repo.create(
                db,
                conversation_id,
                "system",
                json.dumps(updated_refund, ensure_ascii=False),
                msg_type="refund_info",
            )

        yield {"type": "intent", "value": result.get("intent")}
        yield {"type": "token", "content": result.get("response", "")}
        yield {"type": "done"}
