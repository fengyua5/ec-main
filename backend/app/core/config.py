from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./.data/ec-main.sqlite3"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    jwt_secret: str = "dev-secret-key-change-in-production"
    ollama_base_url: str = "http://localhost:11434"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="")


settings = Settings()
