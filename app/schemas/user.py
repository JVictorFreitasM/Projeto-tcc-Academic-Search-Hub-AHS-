"""Esquemas de usuário e autenticação."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_EMAIL_LENGTH = 254
MIN_PASSWORD = 10
MAX_PASSWORD = 128


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > MAX_EMAIL_LENGTH or not _EMAIL_RE.match(email):
        raise ValueError("e-mail inválido")
    return email


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=MIN_PASSWORD, max_length=MAX_PASSWORD)
    accept_privacy_policy: bool

    @field_validator("full_name")
    @classmethod
    def _name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("informe o nome completo")
        return value

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("accept_privacy_policy")
    @classmethod
    def _consent(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("é preciso aceitar a Política de Privacidade")
        return value

    @model_validator(mode="after")
    def _password_rules(self) -> Self:
        if not any(c.isalpha() for c in self.password) or not any(
            c.isdigit() for c in self.password
        ):
            raise ValueError("a senha deve ter ao menos uma letra e um número")
        if self.email in self.password.lower():
            raise ValueError("a senha não pode conter o e-mail")
        return self


class LoginIn(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=MAX_PASSWORD)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return value.strip().lower()


class UserOut(BaseModel):
    """Dados da conta. Nunca inclui `password_hash`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    created_at: datetime
    consent_at: datetime
    consent_policy_version: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 (tipo do esquema OAuth, não é segredo)
    expires_in: int = Field(description="Validade do token em segundos")
    consent_required: bool = False
