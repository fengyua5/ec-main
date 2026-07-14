import logging

from app.domain.ai.rag.index_service import FaqIndexService

logger = logging.getLogger(__name__)


class FaqRetriever:

    SIMILARITY_THRESHOLD = 0.6
    TOP_K = 3

    def __init__(self, index_service: FaqIndexService):
        self._index_service = index_service

    def retrieve(self, query: str) -> list[dict]:
        retriever = self._index_service.get_retriever()
        nodes = retriever.retrieve(query)
        logger.info("RAG 检索: query='%s' 召回 %d 条原始结果", query[:50], len(nodes))

        results = []
        for node in nodes:
            score = node.score if node.score is not None else 0.0
            if score < self.SIMILARITY_THRESHOLD:
                logger.debug("RAG 检索: 过滤低分结果 score=%.4f < %.2f", score, self.SIMILARITY_THRESHOLD)
                continue
            results.append({
                "content": node.node.text,
                "score": score,
                "source": node.node.metadata.get("file_path", ""),
            })

        logger.info("RAG 检索: 阈值过滤后 %d 条（最高分 %.4f）", len(results), results[0]["score"] if results else 0)
        return results

    def has_match(self, query: str) -> bool:
        return len(self.retrieve(query)) > 0
