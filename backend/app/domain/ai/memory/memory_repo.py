from sqlalchemy.orm import Session
from app.models.buyer_memory import BuyerMemory


def get_by_buyer(db: Session, buyer_id: int) -> BuyerMemory | None:
    return db.query(BuyerMemory).filter(BuyerMemory.buyer_id == buyer_id).first()


def upsert(db: Session, buyer_id: int, content: str, expected_version: int) -> bool:
    existing = get_by_buyer(db, buyer_id)
    if existing is None:
        mem = BuyerMemory(buyer_id=buyer_id, content=content, version=1)
        db.add(mem)
        db.commit()
        return True
    if existing.version != expected_version:
        return False
    existing.content = content
    existing.version += 1
    db.commit()
    return True


def list_all(db: Session, limit: int = 50) -> list[BuyerMemory]:
    return db.query(BuyerMemory).order_by(BuyerMemory.updated_at.desc()).limit(limit).all()
