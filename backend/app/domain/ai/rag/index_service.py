import os
import re
import logging

import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.schema import Document
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain_ollama import OllamaEmbeddings

from app.core.config import settings, BASE_DIR

logger = logging.getLogger(__name__)


def _zh_tokenizer(text: str) -> list[str]:
    """中文感知分词：中文字符每字 1 个 token，连续英文/数字算 1 个 token。"""
    return re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9]+", text)


def _zh_sentence_splitter(text: str) -> list[str]:
    """按中英文句末标点切句，保证 chunk 边界完整。"""
    parts = re.split(r"(?<=[。！？；!?;])", text)
    return [p for p in parts if p.strip()]


_FAQ_QUESTION_RE = re.compile(r"(?=\nQ\s*\d*\s*[.、:：])")
_HEADING_RE = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)


def _clean_markdown(text: str) -> str:
    """清洗 markdown：去除语法标记（链接、加粗、行内代码、列表符号等），保留文字。

    标题行（# 开头）原样保留，用于后续按标题切分。
    """
    lines = []
    in_code = False
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("```") or s.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^\|?[\s\-:|]+\|?$", s):
            continue
        if s.startswith("#"):
            lines.append(s)
            continue
        cleaned = s
        cleaned = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", cleaned)
        cleaned = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cleaned)
        cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
        cleaned = re.sub(r"(\*\*|__|~~)(.+?)\1", r"\2", cleaned)
        cleaned = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", cleaned)
        cleaned = re.sub(r"^>\s*", "", cleaned)
        cleaned = re.sub(r"^[-*+]\s+", "", cleaned)
        cleaned = re.sub(r"^\d+[.、]\s+", "", cleaned)
        if cleaned.strip():
            lines.append(cleaned.strip())
    return "\n".join(lines)


def _split_by_headings(text: str) -> list[str]:
    """按 markdown 标题切分，每个标题及其后续内容独立成块。"""
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [text]
    blocks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip("\n")
        if block.strip():
            blocks.append(block)
    return blocks


def _strip_heading_markers(block: str) -> str:
    """去掉标题行的 # 标记，保留标题文字。"""
    lines = [re.sub(r"^#{1,6}\s*", "", line) for line in block.split("\n")]
    return "\n".join(lines).strip()


def _merge_sentences(sentences: list[str], chunk_size: int, overlap: int) -> list[str]:
    """将句子合并为不超过 chunk_size 的块，相邻块间保留约 overlap 字的重叠。"""
    chunks = []
    i = 0
    n = len(sentences)
    while i < n:
        buf = sentences[i]
        j = i + 1
        while j < n and len(_zh_tokenizer(buf + sentences[j])) <= chunk_size:
            buf += sentences[j]
            j += 1
        chunks.append(buf)
        if j >= n:
            break
        acc = ""
        k = j - 1
        while k >= i and len(acc) < overlap:
            acc = sentences[k] + acc
            k -= 1
        next_i = k + 1
        i = next_i if next_i > i else j
    return chunks


def _split_long_block(block: str, chunk_size: int, overlap: int) -> list[str]:
    sentences = [s for s in _zh_sentence_splitter(block) if s.strip()]
    if not sentences:
        return [block]
    return _merge_sentences(sentences, chunk_size, overlap)


def _split_faq(text: str, chunk_size: int, overlap: int = 50) -> list[str]:
    """清洗 markdown 并按结构切分：

    1. 优先按 markdown 标题（#）切分，每个标题块独立成 chunk；
    2. 无标题或单标题文档按 Q 标记切分，保证每条 FAQ（问题+答案）完整；
    3. 仍超长的块按句子二次切分并合并到 chunk_size（带 overlap）。
    """
    cleaned = _clean_markdown(text)

    sections = _split_by_headings(cleaned)
    if len(sections) > 1:
        chunks = []
        for section in sections:
            content_lines = [
                line for line in section.split("\n")
                if line.strip() and not re.match(r"^#{1,6}\s+", line)
            ]
            if not content_lines:
                continue
            section_text = _strip_heading_markers(section)
            if len(_zh_tokenizer(section_text)) <= chunk_size:
                chunks.append(section_text)
            else:
                chunks.extend(_split_long_block(section_text, chunk_size, overlap))
        return chunks

    qa_blocks = [
        b.strip("\n").strip()
        for b in _FAQ_QUESTION_RE.split(cleaned)
        if re.match(r"^Q\s*\d*\s*[.、:：]", b.strip("\n").strip())
    ]
    if qa_blocks:
        chunks = []
        for qa in qa_blocks:
            if len(_zh_tokenizer(qa)) <= chunk_size:
                chunks.append(qa)
            else:
                chunks.extend(_split_long_block(qa, chunk_size, overlap))
        return chunks

    sentences = [s for s in _zh_sentence_splitter(cleaned) if s.strip()]
    return _merge_sentences(sentences, chunk_size, overlap) or [cleaned]


class FaqIndexService:

    CHUNK_SIZE = 300
    CHUNK_OVERLAP = 50
    CHROMA_PATH = str(BASE_DIR / ".data" / "chroma_db")
    COLLECTION_NAME = "faq_knowledge"

    def __init__(self):
        self._index: VectorStoreIndex | None = None

    def _build_embed_model(self) -> LangchainEmbedding:
        return LangchainEmbedding(
            OllamaEmbeddings(
                model=settings.ollama_embed_model,
                base_url=settings.ollama_base_url,
            )
        )

    def _build_vector_store(self) -> ChromaVectorStore:
        os.makedirs(self.CHROMA_PATH, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_PATH)
        chroma_collection = chroma_client.get_or_create_collection(self.COLLECTION_NAME)
        return ChromaVectorStore(chroma_collection=chroma_collection)

    def ingest_markdown(self, file_path: str, doc_id: str, filename: str = "") -> int:
        logger.info("RAG 索引: 开始处理文档 file=%s doc_id=%s", file_path, doc_id)
        vector_store = self._build_vector_store()
        embed_model = self._build_embed_model()

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        logger.info("RAG 索引: 文档长度 %d 字符", len(text))

        chunks = _split_faq(text, self.CHUNK_SIZE, self.CHUNK_OVERLAP)
        documents = [
            Document(id_=doc_id, text=chunk, metadata={"file_path": filename})
            for chunk in chunks
        ]

        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_documents(
            documents,
            embed_model=embed_model,
            storage_context=storage_context,
            show_progress=False,
            transformations=[],
        )
        self._index = index
        logger.info("RAG 索引: 完成，生成 %d 个 chunk", len(chunks))
        return len(chunks)

    def delete_document(self, collection_id: str) -> bool:
        try:
            chroma_client = chromadb.PersistentClient(path=self.CHROMA_PATH)
            chroma_collection = chroma_client.get_or_create_collection(self.COLLECTION_NAME)
            chroma_collection.delete(where={"doc_id": collection_id})
            logger.info("RAG 索引: 删除文档 doc_id=%s 成功", collection_id)
            return True
        except Exception as e:
            logger.warning("RAG 索引: 删除文档 doc_id=%s 失败: %s", collection_id, e)
            return False

    def get_index(self) -> VectorStoreIndex:
        if self._index is None:
            logger.info("RAG 索引: 从 ChromaDB 加载索引（collection=%s）", self.COLLECTION_NAME)
            vector_store = self._build_vector_store()
            embed_model = self._build_embed_model()
            self._index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=embed_model,
            )
        else:
            logger.debug("RAG 索引: 复用已缓存的索引")
        return self._index

    def get_all_chunks(self) -> list[dict]:
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_PATH)
        collection = chroma_client.get_or_create_collection(self.COLLECTION_NAME)
        data = collection.get(include=["documents", "metadatas"])

        if not data["ids"]:
            return []

        chunks = []
        metadatas = data["metadatas"] or [{}] * len(data["ids"])
        for i in range(len(data["ids"])):
            chunks.append({
                "id": data["ids"][i],
                "text": data["documents"][i],
                "metadata": metadatas[i],
            })
        return chunks

    def get_retriever(self):
        index = self.get_index()
        logger.debug("RAG 索引: 创建 retriever top_k=50")
        return index.as_retriever(similarity_top_k=50)
