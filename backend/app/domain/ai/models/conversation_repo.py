from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:

    @staticmethod
    def create(db: Session, buyer_id: int) -> Conversation:
        conv = Conversation(buyer_id=buyer_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def get_by_id(db: Session, id: int) -> Conversation | None:
        return db.query(Conversation).filter(Conversation.id == id).first()

    @staticmethod
    def get_active_by_buyer(db: Session, buyer_id: int) -> Conversation | None:
        return db.query(Conversation).filter(
            Conversation.buyer_id == buyer_id,
            Conversation.status == "active",
        ).first()

    @staticmethod
    def list_by_buyer(db: Session, buyer_id: int, limit: int = 20) -> list[Conversation]:
        return db.query(Conversation).filter(
            Conversation.buyer_id == buyer_id,
        ).order_by(
            Conversation.updated_at.desc(),
        ).limit(limit).all()

    @staticmethod
    def list_all(db: Session, limit: int = 50) -> list[Conversation]:
        return db.query(Conversation).order_by(
            Conversation.updated_at.desc(),
        ).limit(limit).all()

    @staticmethod
    def list_waiting_human(db: Session) -> list[Conversation]:
        return db.query(Conversation).filter(
            Conversation.status == "waiting_human",
        ).order_by(
            Conversation.updated_at.asc(),
        ).all()

    @staticmethod
    def update_status(db: Session, id: int, status: str) -> Conversation:
        conv = db.query(Conversation).filter(Conversation.id == id).first()
        if not conv:
            raise ValueError(f"Conversation {id} not found")
        conv.status = status
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def delete(db: Session, id: int) -> bool:
        conv = db.query(Conversation).filter(Conversation.id == id).first()
        if not conv:
            return False
        db.delete(conv)
        db.commit()
        return True


class MessageRepository:

    @staticmethod
    def create(db: Session, conversation_id: int, sender: str, content: str, msg_type: str = "text") -> Message:
        msg = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=content,
            msg_type=msg_type,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def list_by_conversation(db: Session, conversation_id: int, limit: int = 50, offset: int = 0) -> list[Message]:
        return db.query(Message).filter(
            Message.conversation_id == conversation_id,
        ).order_by(
            Message.created_at.asc(),
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_last_message(db: Session, conversation_id: int) -> Message | None:
        return db.query(Message).filter(
            Message.conversation_id == conversation_id,
        ).order_by(
            Message.created_at.desc(),
        ).first()
