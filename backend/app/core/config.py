from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 后端代码目录的绝对路径（backend/），所有持久化路径锚定此处，避免依赖启动时的 cwd
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _default_db_url() -> str:
    data_dir = BASE_DIR / ".data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(data_dir / 'ec-main.sqlite3').as_posix()}"


class Settings(BaseSettings):
    database_url: str = _default_db_url()
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    jwt_secret: str = "dev-secret-key-change-in-production"
    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "bge-m3:latest"
    ollama_num_ctx: int = 8192
    rag_min_vector_score: float = 0.45
    ai_context_window_tokens: int = 8192
    ai_history_reserved_tokens: int = 2048
    ai_history_keep_recent_tokens: int = 2048
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:5000"
    ai_memory_budget_tokens: int = 1024

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), env_prefix="")


settings = Settings()
