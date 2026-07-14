from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.domain.ai.models.conversation_repo import ConversationRepository, MessageRepository

router = APIRouter(prefix="/ai/conversations")


@router.get("/")
def list_conversations(status: str | None = None, db: Session = Depends(get_db)):
    if status == "waiting_human":
        conversations = ConversationRepository.list_waiting_human(db)
    else:
        conversations = ConversationRepository.list_all(db)
    return {
        "conversations": [
            {
                "id": c.id,
                "buyer_id": c.buyer_id,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in conversations
        ]
    }


@router.get("/{conversation_id}/messages")
def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    messages = MessageRepository.list_by_conversation(
        db, conversation_id, limit=200
    )
    return {
        "messages": [
            {
                "id": m.id,
                "sender": m.sender,
                "content": m.content,
                "msg_type": m.msg_type,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
    }


@router.post("/{conversation_id}/reply")
def reply_message(
    conversation_id: int,
    content: str,
    db: Session = Depends(get_db),
):
    message = MessageRepository.create(
        db,
        conversation_id=conversation_id,
        sender="admin",
        content=content,
    )
    ConversationRepository.update_status(db, conversation_id, "active")
    return {
        "message": {
            "id": message.id,
            "sender": message.sender,
            "content": message.content,
            "msg_type": message.msg_type,
            "created_at": message.created_at.isoformat(),
        }
    }
