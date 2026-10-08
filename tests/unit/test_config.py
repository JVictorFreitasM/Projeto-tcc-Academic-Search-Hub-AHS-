import pytest

from app.core.config import ConfigError, Settings, get_settings

pytestmark = pytest.mark.unit

STRONG_KEY = "k" * 40
ENV_NAMES = [
    "APP_ENV",
    "SECRET_KEY",
    "ALLOWED_ORIGINS",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()


def test_defaults_in_development() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.app_env == "development"
    assert settings.allowed_origins == ["http://localhost:8000"]
    assert settings.scraping_enabled is False


def test_missing_secret_key_in_production_blocks_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(Settings, "model_config", {**Settings.model_config, "env_file": None})
    with pytest.raises(ConfigError) as info:
        get_settings()
    assert "SECRET_KEY" in str(info.value)


def test_short_secret_key_error_does_not_leak_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "curta-demais-123")
    monkeypatch.setattr(Settings, "model_config", {**Settings.model_config, "env_file": None})
    with pytest.raises(ConfigError) as info:
        get_settings()
    assert "SECRET_KEY" in str(info.value)
    assert "curta-demais-123" not in str(info.value)


def test_allowed_origins_parsed_from_comma_list() -> None:
    settings = Settings(_env_file=None, allowed_origins="http://a.com, http://b.com")  # type: ignore[call-arg]
    assert settings.allowed_origins == ["http://a.com", "http://b.com"]


def test_wildcard_origin_rejected_in_production() -> None:
    with pytest.raises(ValueError, match="ALLOWED_ORIGINS"):
        Settings(  # type: ignore[call-arg]
            _env_file=None, app_env="production", secret_key=STRONG_KEY, allowed_origins="*"
        )


def test_wildcard_origin_allowed_in_development() -> None:
    settings = Settings(_env_file=None, allowed_origins="*")  # type: ignore[call-arg]
    assert settings.allowed_origins == ["*"]


def test_max_page_size_must_be_at_least_default() -> None:
    with pytest.raises(ValueError, match="MAX_PAGE_SIZE"):
        Settings(_env_file=None, default_page_size=30, max_page_size=10)  # type: ignore[call-arg]


def test_valid_production_settings() -> None:
    settings = Settings(_env_file=None, app_env="production", secret_key=STRONG_KEY)  # type: ignore[call-arg]
    assert settings.app_env == "production"
