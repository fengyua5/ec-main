import uuid
import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.domain.ai.rag import FaqIndexService, FaqDocumentRepository

router = APIRouter(prefix="/ai/faq")

MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/upload")
async def upload_faq(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Only .md files are accepted")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 5MB limit")

    doc_id = str(uuid.uuid4())
    with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        index_service = FaqIndexService()
        chunk_count = index_service.ingest_markdown(tmp_path, doc_id, filename=file.filename)
    finally:
        os.unlink(tmp_path)

    repo = FaqDocumentRepository()
    doc = repo.create(
        filename=file.filename,
        chunk_count=chunk_count,
        chroma_collection_id=doc_id,
    )

    return {
        "id": doc.id,
        "filename": doc.filename,
        "chunk_count": doc.chunk_count,
    }


@router.get("/documents")
def list_documents():
    repo = FaqDocumentRepository()
    docs = repo.get_all()
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ]
    }


@router.delete("/documents/{document_id}")
def delete_document(document_id: int):
    repo = FaqDocumentRepository()
    result = repo.delete(document_id)
    return {"success": result}
