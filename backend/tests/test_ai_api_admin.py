from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


class TestFaqUpload:

    UPLOAD_PATH = "/api/v1/admin/ai/faq/upload"

    def test_upload_faq_success(self) -> None:
        with patch(
            "app.api.admin.ai_faq.FaqIndexService.ingest_markdown",
            return_value=5,
        ):
            response = client.post(
                self.UPLOAD_PATH,
                files={"file": ("test.md", "# Hello\n\nFAQ content", "text/markdown")},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.md"
        assert data["chunk_count"] == 5
        assert data["id"] > 0

    def test_upload_rejects_non_md(self) -> None:
        response = client.post(
            self.UPLOAD_PATH,
            files={"file": ("test.txt", "plain text", "text/plain")},
        )
        assert response.status_code == 400

    def test_upload_rejects_oversized(self) -> None:
        with patch(
            "app.api.admin.ai_faq.FaqIndexService.ingest_markdown",
            return_value=5,
        ):
            response = client.post(
                self.UPLOAD_PATH,
                files={
                    "file": (
                        "big.md",
                        "x" * (5 * 1024 * 1024 + 1),
                        "text/markdown",
                    )
                },
            )
        assert response.status_code == 400


class TestFaqDocuments:

    LIST_PATH = "/api/v1/admin/ai/faq/documents"

    def test_list_documents_empty(self) -> None:
        response = client.get(self.LIST_PATH)
        assert response.status_code == 200
        assert response.json() == {"documents": []}

    def test_list_documents_with_data(self) -> None:
        with patch(
            "app.api.admin.ai_faq.FaqIndexService.ingest_markdown",
            return_value=3,
        ):
            client.post(
                "/api/v1/admin/ai/faq/upload",
                files={"file": ("a.md", "aaa", "text/markdown")},
            )
            client.post(
                "/api/v1/admin/ai/faq/upload",
                files={"file": ("b.md", "bbb", "text/markdown")},
            )

        response = client.get(self.LIST_PATH)
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        filenames = {d["filename"] for d in data["documents"]}
        assert filenames == {"a.md", "b.md"}


class TestFaqDelete:

    def test_delete_existing(self) -> None:
        with patch(
            "app.api.admin.ai_faq.FaqIndexService.ingest_markdown",
            return_value=3,
        ):
            upload_resp = client.post(
                "/api/v1/admin/ai/faq/upload",
                files={"file": ("del.md", "delete me", "text/markdown")},
            )
        doc_id = upload_resp.json()["id"]

        with patch(
            "app.api.admin.ai_faq.FaqIndexService.delete_document",
            return_value=True,
        ):
            response = client.delete(
                f"/api/v1/admin/ai/faq/documents/{doc_id}"
            )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_nonexistent(self) -> None:
        response = client.delete("/api/v1/admin/ai/faq/documents/9999")
        assert response.status_code == 200
        assert response.json()["success"] is False


class TestAdminConversations:

    LIST_PATH = "/api/v1/admin/ai/conversations"

    def test_list_empty(self) -> None:
        response = client.get(self.LIST_PATH)
        assert response.status_code == 200
        assert response.json() == {"conversations": []}

    def test_list_with_data(self) -> None:
        from app.domain.ai.models.conversation_repo import (
            ConversationRepository,
        )
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            ConversationRepository.create(db, buyer_id=10)
            ConversationRepository.create(db, buyer_id=20)
        finally:
            db.close()

        response = client.get(self.LIST_PATH)
        assert response.status_code == 200
        data = response.json()
        assert len(data["conversations"]) == 2

    def test_list_filter_waiting_human(self) -> None:
        from app.domain.ai.models.conversation_repo import (
            ConversationRepository,
        )
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            ConversationRepository.create(db, buyer_id=1)
            c2 = ConversationRepository.create(db, buyer_id=2)
            ConversationRepository.update_status(db, c2.id, "waiting_human")
        finally:
            db.close()

        response = client.get(
            self.LIST_PATH, params={"status": "waiting_human"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["id"] == 2

    def test_get_messages_empty(self) -> None:
        from app.domain.ai.models.conversation_repo import (
            ConversationRepository,
        )
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            conv = ConversationRepository.create(db, buyer_id=1)
            cid = conv.id
        finally:
            db.close()

        response = client.get(
            f"/api/v1/admin/ai/conversations/{cid}/messages"
        )
        assert response.status_code == 200
        assert response.json() == {"messages": []}

    def test_get_messages_with_data(self) -> None:
        from app.domain.ai.models.conversation_repo import (
            ConversationRepository,
            MessageRepository,
        )
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            conv = ConversationRepository.create(db, buyer_id=1)
            cid = conv.id
            MessageRepository.create(db, cid, "user", "Hello")
            MessageRepository.create(db, cid, "bot", "Hi there")
        finally:
            db.close()

        response = client.get(
            f"/api/v1/admin/ai/conversations/{cid}/messages"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][1]["content"] == "Hi there"

    def test_reply_message(self) -> None:
        from app.domain.ai.models.conversation_repo import (
            ConversationRepository,
        )
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            conv = ConversationRepository.create(db, buyer_id=1)
            cid = conv.id
        finally:
            db.close()

        response = client.post(
            f"/api/v1/admin/ai/conversations/{cid}/reply",
            params={"content": "Admin reply"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"]["sender"] == "admin"
        assert data["message"]["content"] == "Admin reply"
