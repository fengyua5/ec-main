from app.db.session import SessionLocal
from app.models.faq_document import FAQDocument
from app.domain.ai.rag.index_service import FaqIndexService


class FaqDocumentRepository:

    def __init__(self):
        self._index_service = FaqIndexService()

    def create(self, filename: str, chunk_count: int, chroma_collection_id: str) -> FAQDocument:
        with SessionLocal() as db:
            doc = FAQDocument(
                filename=filename,
                chunk_count=chunk_count,
                chroma_collection_id=chroma_collection_id,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            return doc

    def get_all(self) -> list[FAQDocument]:
        with SessionLocal() as db:
            return db.query(FAQDocument).order_by(FAQDocument.created_at.desc()).all()

    def get_by_id(self, id: int) -> FAQDocument | None:
        with SessionLocal() as db:
            return db.query(FAQDocument).filter(FAQDocument.id == id).first()

    def delete(self, id: int) -> bool:
        with SessionLocal() as db:
            doc = db.query(FAQDocument).filter(FAQDocument.id == id).first()
            if not doc:
                return False
            if doc.chroma_collection_id:
                self._index_service.delete_document(doc.chroma_collection_id)
            db.delete(doc)
            db.commit()
            return True
