from unittest.mock import MagicMock, patch

import pytest

from app.domain.ai.rag import FaqIndexService, FaqRetriever, FaqDocumentRepository
from app.models.faq_document import Base
from app.models.faq_document import FAQDocument
from app.db.session import engine


Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


class TestFaqDocumentRepository:

    def test_create(self) -> None:
        repo = FaqDocumentRepository()
        doc = repo.create(filename="test.md", chunk_count=5, chroma_collection_id="col_001")
        assert doc.id is not None
        assert doc.filename == "test.md"
        assert doc.chunk_count == 5
        assert doc.chroma_collection_id == "col_001"

    def test_get_all_empty(self) -> None:
        repo = FaqDocumentRepository()
        assert repo.get_all() == []

    def test_get_all(self) -> None:
        repo = FaqDocumentRepository()
        repo.create(filename="a.md", chunk_count=1, chroma_collection_id="c1")
        repo.create(filename="b.md", chunk_count=2, chroma_collection_id="c2")
        all_docs = repo.get_all()
        assert len(all_docs) == 2

    def test_get_by_id(self) -> None:
        repo = FaqDocumentRepository()
        created = repo.create(filename="x.md", chunk_count=3, chroma_collection_id="cx")
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.filename == "x.md"

    def test_get_by_id_not_found(self) -> None:
        repo = FaqDocumentRepository()
        assert repo.get_by_id(999) is None

    def test_delete(self) -> None:
        repo = FaqDocumentRepository()
        created = repo.create(filename="del.md", chunk_count=2, chroma_collection_id="cd")
        assert repo.delete(created.id) is True
        assert repo.get_by_id(created.id) is None

    def test_delete_not_found(self) -> None:
        repo = FaqDocumentRepository()
        assert repo.delete(999) is False


class TestFaqIndexService:

    def test_init_succeeds_without_ollama(self) -> None:
        svc = FaqIndexService()
        assert svc is not None
        assert svc._index is None


class TestFaqRetriever:

    def test_retrieve_filters_below_threshold(self) -> None:
        svc = MagicMock()

        class FakeNode:
            def __init__(self, text: str, score: float, source: str = ""):
                self.node = MagicMock()
                self.node.text = text
                self.score = score
                self.node.metadata = {"file_path": source}

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            FakeNode("high score chunk", 0.85, "doc1.md"),
            FakeNode("below threshold", 0.45, "doc2.md"),
            FakeNode("also below", 0.3, "doc3.md"),
        ]
        svc.get_retriever.return_value = mock_retriever

        retriever = FaqRetriever(svc)
        results = retriever.retrieve("test query")

        assert len(results) == 1
        assert results[0]["content"] == "high score chunk"
        assert results[0]["score"] == 0.85
        assert results[0]["source"] == "doc1.md"

    def test_has_match_empty_when_all_below_threshold(self) -> None:
        svc = MagicMock()

        class FakeNode:
            def __init__(self, text: str, score: float):
                self.node = MagicMock()
                self.node.text = text
                self.score = score
                self.node.metadata = {"file_path": ""}

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            FakeNode("low score", 0.2),
        ]
        svc.get_retriever.return_value = mock_retriever

        retriever = FaqRetriever(svc)
        assert retriever.has_match("test") is False
