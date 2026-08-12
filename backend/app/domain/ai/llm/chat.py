from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.core.config import settings


def get_chat_llm(*, temperature: float = 0.0, streaming: bool = False) -> ChatOllama:
    return ChatOllama(
        model="qwen2.5:7b",
        base_url=settings.ollama_base_url,
        temperature=temperature,
        streaming=streaming,
        num_ctx=settings.ollama_num_ctx,
    )


def get_embedding_model() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=settings.ollama_base_url,
    )
