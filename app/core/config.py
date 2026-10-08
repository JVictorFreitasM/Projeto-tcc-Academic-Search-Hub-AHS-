"""Configuração central da aplicação, lida de variáveis de ambiente e do `.env`."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

MIN_SECRET_KEY_LENGTH = 32


class ConfigError(RuntimeError):
    """Configuração inválida. A mensagem cita nomes de variáveis, nunca valores."""


class Settings(BaseSettings):
    """Variáveis de ambiente da seção 5.4, com tipos e validações."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "production"] = "development"
    secret_key: str = ""
    database_url: str = "postgresql+psycopg://user:pass@localhost:5432/academic_search"
    access_token_expire_minutes: int = Field(default=60, gt=0)
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:8000"]
    openalex_api_key: str = ""
    core_api_key: str = ""
    oai_sources_file: str = "config/oai_sources.yml"
    contact_email: str = ""
    oai_harvest_delay_seconds: float = Field(default=1, ge=0)
    scraping_enabled: bool = False
    source_timeout_seconds: float = Field(default=10, gt=0)
    default_page_size: int = Field(default=20, ge=1)
    max_page_size: int = Field(default=50, ge=1)
    rate_limit_search: str = "60/minute"
    rate_limit_auth: str = "5/minute"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    docs_enabled: bool = True
    test_database_url: str = ""
    privacy_policy_version: str = "1.0"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Aceita a lista separada por vírgulas do `.env`."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _check_rules(self) -> Settings:
        if self.max_page_size < self.default_page_size:
            raise ValueError("MAX_PAGE_SIZE deve ser maior ou igual a DEFAULT_PAGE_SIZE")
        if self.app_env != "development" and len(self.secret_key) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY é obrigatória e precisa ter ao menos {MIN_SECRET_KEY_LENGTH} "
                "caracteres"
            )
        if self.app_env == "production" and "*" in self.allowed_origins:
            raise ValueError("ALLOWED_ORIGINS não pode conter '*' em produção")
        return self


def _describe(error: ValidationError) -> str:
    """Resume o erro citando só o nome da variável, nunca o valor recebido."""
    parts = []
    for item in error.errors():
        message = _safe_message(item["type"], item["msg"])
        loc = item["loc"]
        # Regras de modelo (loc vazio) já citam a variável no próprio texto.
        parts.append(f"{str(loc[0]).upper()}: {message}" if loc else message)
    return "; ".join(parts)


def _safe_message(error_type: str, message: str) -> str:
    """Mensagens de `value_error` vêm dos nossos validadores e não carregam valores."""
    if error_type == "value_error":
        return message.removeprefix("Value error, ")
    return "valor inválido ou ausente"


@lru_cache
def get_settings() -> Settings:
    """Devolve a configuração única; falha com `ConfigError` se for inválida."""
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigError(f"Configuração inválida. {_describe(exc)}") from None
