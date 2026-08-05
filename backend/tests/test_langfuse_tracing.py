def test_langfuse_config_defaults() -> None:
    from app.core.config import settings
    assert settings.langfuse_public_key == ""
    assert settings.langfuse_secret_key == ""
    assert settings.langfuse_host == "http://localhost:5000"
