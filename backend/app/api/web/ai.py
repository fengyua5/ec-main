import json
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository
from app.domain.ai.workflow.engine import ChatEngine


class ConversationResponse(BaseModel):
    id: int
    buyer_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender: str
    content: str
    msg_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]


router = APIRouter(prefix="/ai")


async def _event_generator(
    db: Session,
    conversation_id: int,
    user_message: str,
) -> None:
    engine = ChatEngine()
    async for event in engine.process_message(db, conversation_id, user_message):
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(
    conversation_id: int | None = None,
    content: str = ...,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    if conversation_id is None:
        conv_repo = ConversationRepository()
        conv = conv_repo.create(db, buyer_id=1)
        conversation_id = conv.id

    return StreamingResponse(
        _event_generator(db, conversation_id, content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(db: Session = Depends(get_db)) -> ConversationListResponse:
    repo = ConversationRepository()
    conversations = repo.list_by_buyer(db, buyer_id=1)
    return ConversationListResponse(conversations=conversations)


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
def get_messages(
    conversation_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> MessageListResponse:
    repo = MessageRepository()
    messages = repo.list_by_conversation(db, conversation_id, limit=limit, offset=offset)
    return MessageListResponse(messages=messages)
