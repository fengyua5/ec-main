import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.config import settings
from app.domain.ai.rag.index_service import FaqIndexService

logger = logging.getLogger(__name__)

_CJK_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]")


class BM25Index:

    def __init__(self, index_service: FaqIndexService):
        self._index_service = index_service
        self._bm25 = None
        self._chunks = []

    def _ensure_built(self):
        if self._bm25 is not None:
            return
        from rank_bm25 import BM25Okapi

        chunks = self._index_service.get_all_chunks()
        self._chunks = chunks

        if not chunks:
            logger.info("BM25 索引: 语料为空，跳过构建")
            return

        tokenized = [self._tokenize(c["text"]) for c in chunks]
        self._bm25 = BM25Okapi(tokenized)
        logger.info("BM25 索引: 构建完成, %d 个 chunk", len(chunks))

    def _tokenize(self, text: str) -> list[str]:
        """中文感知分词：拉丁词/数字保持完整，中文字符逐字切分，避免空白分词失效。"""
        return _CJK_RE.findall(text.lower())

    def search(self, query: str, top_k: int) -> list[dict]:
        self._ensure_built()

        if not self._chunks:
            return []

        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        scored = [(i, scores[i]) for i in range(len(scores))]
        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored[:top_k]:
            results.append({
                "id": self._chunks[idx]["id"],
                "content": self._chunks[idx]["text"],
                "score": float(score),
                "source": self._chunks[idx]["metadata"].get("file_path", ""),
            })
        return results


class FaqRetriever:

    TOP_K = 50
    TOP_N = 3
    RRF_K = 60
    # CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-4-v2"

    def __init__(self, index_service: FaqIndexService):
        self._index_service = index_service
        self._bm25_index: BM25Index | None = None
        # self._cross_encoder = None

    @property
    def _min_vector_score(self) -> float:
        return settings.rag_min_vector_score

    def retrieve(self, query: str) -> list[dict]:
        vector_results, bm25_results = self._parallel_retrieve(query)

        logger.info(
            "RAG 检索: query='%s' 向量召回 %d 条, BM25 召回 %d 条",
            query[:50], len(vector_results), len(bm25_results),
        )

        if not self._is_relevant(vector_results):
            logger.info(
                "RAG 检索: 最高向量分 %.4f < 阈值 %.2f，判定无相关 FAQ",
                vector_results[0]["score"] if vector_results else 0,
                self._min_vector_score,
            )
            return []

        fused = self._rrf_fuse(vector_results, bm25_results)
        logger.info("RAG RRF 融合后 %d 条", len(fused))

        # reranked = self._cross_encoder_rerank(query, fused)
        # logger.info(
        #     "RAG 精排后 %d 条（最高分 %.4f）",
        #     len(reranked), reranked[0]["score"] if reranked else 0,
        # )

        return fused[:self.TOP_N]

    def _is_relevant(self, vector_results: list[dict]) -> bool:
        if not vector_results:
            return True
        return vector_results[0]["score"] >= self._min_vector_score

    def _parallel_retrieve(self, query: str) -> tuple[list[dict], list[dict]]:
        # 预热：串行完成共享依赖初始化（chroma 客户端、索引加载、BM25 构建），
        # 避免两个线程同时初始化 chroma 客户端产生竞争导致首次检索失败。
        bm25 = None
        retriever = None
        try:
            bm25 = self._get_bm25_index()
            retriever = self._index_service.get_retriever()
        except Exception as e:
            logger.warning("RAG 检索预热失败: %s", e)

        results = {"vector": None, "bm25": None}

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {}
            if retriever is not None:
                futures[pool.submit(self._vector_search, retriever, query)] = "vector"
            if bm25 is not None:
                futures[pool.submit(self._bm25_search, bm25, query)] = "bm25"
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    logger.warning("RAG %s 检索失败: %s", key, e)
                    results[key] = []

        return (results["vector"] or [], results["bm25"] or [])

    def _vector_search(self, retriever, query: str) -> list[dict]:
        nodes = retriever.retrieve(query)

        results = []
        for node in nodes:
            results.append({
                "id": node.node.node_id,
                "content": node.node.text,
                "score": node.score if node.score is not None else 0.0,
                "source": node.node.metadata.get("file_path", ""),
            })
        return results

    def _get_bm25_index(self) -> BM25Index:
        if self._bm25_index is None:
            self._bm25_index = BM25Index(self._index_service)
        return self._bm25_index

    def _bm25_search(self, bm25: BM25Index, query: str) -> list[dict]:
        return bm25.search(query, top_k=self.TOP_K)

    def _rrf_fuse(self, *ranked_lists: list[dict]) -> list[dict]:
        id_to_result: dict[str, dict] = {}

        for ranked in ranked_lists:
            for rank, result in enumerate(ranked):
                doc_id = result["id"]
                rrf_score = 1.0 / (self.RRF_K + rank + 1)
                if doc_id not in id_to_result:
                    id_to_result[doc_id] = {
                        "id": doc_id,
                        "content": result["content"],
                        "source": result["source"],
                        "rrf_score": 0.0,
                    }
                id_to_result[doc_id]["rrf_score"] += rrf_score

        sorted_results = sorted(
            id_to_result.values(),
            key=lambda x: x["rrf_score"],
            reverse=True,
        )

        for result in sorted_results:
            result["score"] = result["rrf_score"]

        return sorted_results

    def _cross_encoder_rerank(self, query: str, candidates: list[dict]) -> list[dict]:
        # 暂不使用：Cross-Encoder 精排（需 sentence-transformers，后续按需启用）
        # try:
        #     if self._cross_encoder is None:
        #         from sentence_transformers import CrossEncoder
        #         self._cross_encoder = CrossEncoder(self.CROSS_ENCODER_MODEL)
        #
        #     pairs = [[query, c["content"]] for c in candidates]
        #     scores = self._cross_encoder.predict(pairs)
        #
        #     for i, candidate in enumerate(candidates):
        #         candidate["score"] = float(scores[i])
        #
        #     candidates.sort(key=lambda x: x["score"], reverse=True)
        #
        # except Exception as e:
        #     logger.warning("Cross-Encoder 精排失败: %s，使用 RRF 排序结果", e)
        #
        # return candidates
        return candidates

    def has_match(self, query: str) -> bool:
        return len(self.retrieve(query)) > 0
