from unittest.mock import MagicMock, patch

import pytest

from app.domain.ai.rag import FaqIndexService, FaqRetriever, FaqDocumentRepository
from app.domain.ai.rag.index_service import _split_faq
from app.domain.ai.rag.retriever import BM25Index
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

    def test_split_faq_splits_per_qa_pair(self) -> None:
        text = (
            "# FAQ\n\n"
            "Q: 忘记登录密码怎么办？\nA: 通过手机验证码或邮箱重置密码。\n\n"
            "Q: 订单多久发货？\nA: 现货一般48小时内发货。\n\n"
            "Q: 怎么开发票？\nA: 在订单详情申请电子发票。"
        )
        chunks = _split_faq(text, FaqIndexService.CHUNK_SIZE)
        assert len(chunks) == 3
        assert "忘记登录密码" in chunks[0]
        assert "订单多久发货" in chunks[1]
        assert "怎么开发票" in chunks[2]

    def test_split_faq_drops_header_without_qa(self) -> None:
        text = "# FAQ\n\nQ: 商品缺货怎么办？\nA: 支持预约到货通知。"
        chunks = _split_faq(text, FaqIndexService.CHUNK_SIZE)
        assert len(chunks) == 1
        assert "# FAQ" not in chunks[0]

    def test_split_faq_supports_numbered_questions(self) -> None:
        text = (
            "一、账户与登录\n"
            "Q1. 如何注册电商平台账号？\nA：通过手机号或邮箱注册。注册成功后建议绑定手机号。\n\n"
            "Q3. 忘记登录密码怎么办？\nA：在登录页面点击忘记密码按钮，通过绑定手机号接收验证码重置。\n"
            "若未绑定手机和邮箱，请联系人工客服进行身份核实后重置。"
        )
        chunks = _split_faq(text, FaqIndexService.CHUNK_SIZE)
        assert len(chunks) == 2
        assert "如何注册电商平台账号" in chunks[0]
        assert chunks[1].startswith("Q3.")
        assert "身份核实后重置" in chunks[1]
        assert "一、账户与登录" not in "".join(chunks)

    def test_split_faq_groups_by_markdown_headings(self) -> None:
        text = (
            "# 账户与登录\n\n"
            "## 密码问题\nQ1. 忘记登录密码怎么办？\nA：通过手机验证码或邮箱重置。\n\n"
            "## 发票问题\nQ2. 怎么开发票？\nA：在订单详情申请电子发票。"
        )
        chunks = _split_faq(text, FaqIndexService.CHUNK_SIZE)
        assert len(chunks) == 2
        assert "密码问题" in chunks[0] and "忘记登录密码" in chunks[0]
        assert "发票问题" in chunks[1] and "怎么开发票" in chunks[1]

    def test_split_faq_drops_empty_heading_shell(self) -> None:
        text = (
            "# 外层标题\n\n"
            "## 内层标题\nQ1. 如何注册？\nA：通过手机号或邮箱。"
        )
        chunks = _split_faq(text, FaqIndexService.CHUNK_SIZE)
        assert len(chunks) == 1
        assert "外层标题" not in "".join(chunks)

    def test_split_faq_cleans_markdown_syntax(self) -> None:
        text = "# 标题\n\n**加粗内容** 和 [链接](https://x.com) 及 `代码` 与 ~~删除线~~"
        chunks = _split_faq(text, FaqIndexService.CHUNK_SIZE)
        joined = "".join(chunks)
        assert "**" not in joined
        assert "加粗内容" in joined
        assert "https://x.com" not in joined
        assert "代码" in joined

    def test_split_faq_merges_long_text_with_overlap(self) -> None:
        text = "。".join(["句子内容编号%d测试文本填充用于验证" % i for i in range(1, 21)])
        chunks = _split_faq(text, 100, 20)
        assert len(chunks) >= 2
        assert all(len(c.strip()) > 0 for c in chunks)
        # 相邻块应共享 chunks[0] 的最后一句（overlap 生效）
        tail = chunks[0].rsplit("。", 2)[-2] + "。"
        assert tail in chunks[1]

    def test_split_faq_falls_back_to_sentences_without_qa(self) -> None:
        text = "这是没有 Q 标记的普通正文内容，用于验证兜底切分逻辑是否正常工作。"
        chunks = _split_faq(text, FaqIndexService.CHUNK_SIZE)
        assert chunks
        assert all(c.strip() for c in chunks)


class TestBM25ChineseTokenize:

    def test_tokenize_chinese_into_characters(self) -> None:
        bm25 = BM25Index(MagicMock())
        tokens = bm25._tokenize("商品缺货怎么办")
        assert "商" in tokens
        assert "缺" in tokens
        assert "货" in tokens
        assert tokens == ["商", "品", "缺", "货", "怎", "么", "办"]

    def test_tokenize_keeps_latin_words_intact(self) -> None:
        bm25 = BM25Index(MagicMock())
        tokens = bm25._tokenize("订单号 abc123 发货")
        assert "abc123" in tokens
        assert "订" in tokens


class TestFaqRetriever:

    def _make_fake_node(self, text: str, score: float, node_id: str, source: str = "") -> MagicMock:
        node = MagicMock()
        node.node_id = node_id
        node.text = text
        node.metadata = {"file_path": source}

        wrapper = MagicMock()
        wrapper.node = node
        wrapper.score = score
        return wrapper

    def test_rrf_fuses_rankings(self) -> None:
        svc = MagicMock()
        retriever = FaqRetriever(svc)

        list_a = [
            {"id": "1", "content": "A", "source": "", "score": 0.9},
            {"id": "2", "content": "B", "source": "", "score": 0.8},
        ]
        list_b = [
            {"id": "2", "content": "B", "source": "", "score": 0.7},
            {"id": "3", "content": "C", "source": "", "score": 0.6},
        ]

        fused = retriever._rrf_fuse(list_a, list_b)

        assert fused[0]["id"] == "2"
        assert fused[1]["id"] == "1"
        assert fused[2]["id"] == "3"

    def test_retrieve_limits_to_top_n(self) -> None:
        svc = MagicMock()

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            self._make_fake_node(f"chunk{i}", 1.0 - i * 0.01, f"id{i}")
            for i in range(20)
        ]
        svc.get_retriever.return_value = mock_retriever
        svc.get_all_chunks.return_value = []

        with patch.object(FaqRetriever, "_cross_encoder_rerank", side_effect=lambda q, c: c):
            retriever = FaqRetriever(svc)
            results = retriever.retrieve("test")

        assert len(results) == retriever.TOP_N

    def test_retrieve_empty_when_no_results(self) -> None:
        svc = MagicMock()

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        svc.get_retriever.return_value = mock_retriever
        svc.get_all_chunks.return_value = []

        with patch.object(FaqRetriever, "_cross_encoder_rerank", side_effect=lambda q, c: c):
            retriever = FaqRetriever(svc)
            results = retriever.retrieve("test")

        assert results == []

    def test_retrieve_empty_when_below_similarity_threshold(self) -> None:
        svc = MagicMock()

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            self._make_fake_node("irrelevant chunk", 0.35, "id1"),
            self._make_fake_node("another irrelevant", 0.2, "id2"),
        ]
        svc.get_retriever.return_value = mock_retriever
        svc.get_all_chunks.return_value = []

        with patch.object(FaqRetriever, "_cross_encoder_rerank", side_effect=lambda q, c: c):
            retriever = FaqRetriever(svc)
            results = retriever.retrieve("test")

        assert results == []

    def test_has_match_returns_true_when_results_exist(self) -> None:
        svc = MagicMock()

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            self._make_fake_node("match", 0.9, "id1"),
        ]
        svc.get_retriever.return_value = mock_retriever
        svc.get_all_chunks.return_value = []

        with patch.object(FaqRetriever, "_cross_encoder_rerank", side_effect=lambda q, c: c):
            retriever = FaqRetriever(svc)
            assert retriever.has_match("test") is True

    def test_has_match_returns_false_when_no_results(self) -> None:
        svc = MagicMock()

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        svc.get_retriever.return_value = mock_retriever
        svc.get_all_chunks.return_value = []

        with patch.object(FaqRetriever, "_cross_encoder_rerank", side_effect=lambda q, c: c):
            retriever = FaqRetriever(svc)
            assert retriever.has_match("test") is False

    def test_one_retriever_fails_gracefully(self) -> None:
        svc = MagicMock()

        svc.get_retriever.side_effect = RuntimeError("vector store unavailable")
        svc.get_all_chunks.return_value = []

        with patch.object(FaqRetriever, "_cross_encoder_rerank", side_effect=lambda q, c: c):
            retriever = FaqRetriever(svc)
            results = retriever.retrieve("test")

        assert results == []
