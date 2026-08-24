import pytest

from app.core.config import Settings


def test_settings_load_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "Test API")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("API_V1_PREFIX", "/api/v1")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://cricket:cricket@localhost:5433/cricket_db",
    )
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")

    monkeypatch.setenv("JWT_SECRET_KEY", "replace-me-with-a-long-random-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")

    settings = Settings()

    assert settings.app_name == "Test API"
    assert settings.app_env == "test"
    assert settings.debug is False
    assert settings.jwt_secret_key == "replace-me-with-a-long-random-secret"
    assert settings.access_token_expire_minutes == 15
    assert settings.refresh_token_expire_days == 30
    assert settings.cors_origin_list == [
        "http://localhost:3000",
        "http://localhost:8080",
    ]
