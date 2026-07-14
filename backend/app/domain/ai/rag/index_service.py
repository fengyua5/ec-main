import os
import logging

import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain_ollama import OllamaEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)


class FaqIndexService:

    CHUNK_SIZE = 256
    CHUNK_OVERLAP = 50
    CHROMA_PATH = ".data/chroma_db"
    COLLECTION_NAME = "faq_knowledge"

    def __init__(self):
        self._index: VectorStoreIndex | None = None

    def _build_embed_model(self) -> LangchainEmbedding:
        return LangchainEmbedding(
            OllamaEmbeddings(
                model="nomic-embed-text",
                base_url=settings.ollama_base_url,
            )
        )

    def _build_vector_store(self) -> ChromaVectorStore:
        os.makedirs(self.CHROMA_PATH, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=self.CHROMA_PATH)
        chroma_collection = chroma_client.get_or_create_collection(self.COLLECTION_NAME)
        return ChromaVectorStore(chroma_collection=chroma_collection)

    def ingest_markdown(self, file_path: str, doc_id: str) -> int:
        logger.info("RAG 索引: 开始处理文档 file=%s doc_id=%s", file_path, doc_id)
        vector_store = self._build_vector_store()
        embed_model = self._build_embed_model()

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        logger.info("RAG 索引: 文档长度 %d 字符", len(text))

        splitter = SentenceSplitter(
            chunk_size=self.CHUNK_SIZE,
            chunk_overlap=self.CHUNK_OVERLAP,
        )
        nodes = splitter.get_nodes_from_documents(
            [type("_Doc", (), {"text": text, "metadata": {}})()]
        )

        index = VectorStoreIndex(
            nodes=nodes,
            embed_model=embed_model,
            vector_store=vector_store,
            show_progress=False,
        )
        self._index = index
        logger.info("RAG 索引: 完成，生成 %d 个 chunk", len(nodes))
        return len(nodes)

    def delete_document(self, collection_id: str) -> bool:
        try:
            chroma_client = chromadb.PersistentClient(path=self.CHROMA_PATH)
            chroma_collection = chroma_client.get_or_create_collection(self.COLLECTION_NAME)
            chroma_collection.delete(ids=[collection_id])
            logger.info("RAG 索引: 删除文档 collection_id=%s 成功", collection_id)
            return True
        except Exception as e:
            logger.warning("RAG 索引: 删除文档 collection_id=%s 失败: %s", collection_id, e)
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

    def get_retriever(self):
        index = self.get_index()
        logger.debug("RAG 索引: 创建 retriever top_k=3")
        return index.as_retriever(similarity_top_k=3)
