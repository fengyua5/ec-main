import asyncio
import json
from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
from app.domain.ai.workflow.graph import build_chat_graph
from app.domain.ai.workflow.state import ConversationState

_TOKEN_CHUNK_SIZE = 4
_TOKEN_CHUNK_INTERVAL = 0.02


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
        yield {"type": "status", "content": "正在查找中..."}

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
            "flow": {
                "intent": None,
                "confidence": 0.0,
                "conversation_id": conversation_id,
                "response": "",
            },
            "skills": {
                "refund": refund_info,
                "faq": {"context": []},
            },
            "mcp": {},
        }

        result = await self.graph.ainvoke(state)

        self.msg_repo.create(db, conversation_id, "user", user_message)
        if result.get("flow", {}).get("response"):
            self.msg_repo.create(db, conversation_id, "ai", result["flow"]["response"])

        updated_refund = result.get("skills", {}).get("refund", {})
        if updated_refund and updated_refund != refund_info:
            self.msg_repo.create(
                db,
                conversation_id,
                "system",
                json.dumps(updated_refund, ensure_ascii=False),
                msg_type="refund_info",
            )

        yield {"type": "intent", "value": result.get("flow", {}).get("intent")}
        response = result.get("flow", {}).get("response", "")
        for i in range(0, len(response), _TOKEN_CHUNK_SIZE):
            yield {"type": "token", "content": response[i:i + _TOKEN_CHUNK_SIZE]}
            await asyncio.sleep(_TOKEN_CHUNK_INTERVAL)
        yield {"type": "done"}
