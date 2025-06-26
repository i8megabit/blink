from app.core.config import settings


def test_settings_defaults():
    assert settings.database_url.startswith("postgresql")
    assert settings.redis_url.startswith("redis")
