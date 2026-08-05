import logging

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Langfuse | None = None


def is_langfuse_enabled() -> bool:
    return bool(
        settings.langfuse_public_key
        and settings.langfuse_secret_key
        and settings.langfuse_host
    )


def get_langfuse_client() -> Langfuse | None:
    global _client
    if _client is not None:
        return _client
    if not is_langfuse_enabled():
        logger.info("Langfuse 未配置（LANGFUSE_PUBLIC_KEY/SECRET_KEY/HOST），追踪已禁用")
        return None
    _client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    logger.info("Langfuse 追踪已启用，上报地址: %s", settings.langfuse_host)
    return _client


def create_chat_trace() -> tuple[CallbackHandler | None, str | None]:
    """为一次对话请求创建 trace：LLM 调用通过 handler 挂到 trace_id 下。"""
    client = get_langfuse_client()
    if client is None:
        return None, None
    trace_id = client.create_trace_id()
    handler = CallbackHandler(
        public_key=settings.langfuse_public_key,
        trace_context={"trace_id": trace_id},
    )
    return handler, trace_id


def record_retrieval(
    trace_id: str,
    *,
    query: str,
    intent: str | None,
    hits: list[dict],
) -> None:
    """把 RAG 检索结果记录为 trace 下的 retriever 观测节点。"""
    client = get_langfuse_client()
    if client is None:
        return
    span = client.start_observation(
        name="retrieve_faq",
        as_type="retriever",
        trace_context={"trace_id": trace_id},
        input={"query": query},
        output={"hits": hits, "intent": intent},
        metadata={"hit_count": len(hits)},
    )
    span.end()


def _reset_langfuse() -> None:
    """测试辅助：重置客户端单例缓存。"""
    global _client
    _client = None
