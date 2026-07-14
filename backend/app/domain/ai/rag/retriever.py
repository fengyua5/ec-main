from app.domain.ai.rag.index_service import FaqIndexService


class FaqRetriever:

    SIMILARITY_THRESHOLD = 0.6
    TOP_K = 3

    def __init__(self, index_service: FaqIndexService):
        self._index_service = index_service

    def retrieve(self, query: str) -> list[dict]:
        retriever = self._index_service.get_retriever()
        nodes = retriever.retrieve(query)

        results = []
        for node in nodes:
            score = node.score if node.score is not None else 0.0
            if score < self.SIMILARITY_THRESHOLD:
                continue
            results.append({
                "content": node.node.text,
                "score": score,
                "source": node.node.metadata.get("file_path", ""),
            })
        return results

    def has_match(self, query: str) -> bool:
        return len(self.retrieve(query)) > 0
