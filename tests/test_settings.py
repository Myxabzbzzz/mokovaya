from config.settings import Settings


def test_settings_reads_env_vars(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token-123")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host/db")

    settings = Settings(_env_file=None)

    assert settings.bot_token == "test-token-123"
    assert settings.database_url == "postgresql+asyncpg://u:p@host/db"


def test_settings_has_sane_defaults():
    settings = Settings(_env_file=None)

    assert settings.bot_token == ""
    assert "postgresql+asyncpg" in settings.database_url
