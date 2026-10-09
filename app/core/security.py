"""Funções de segurança compartilhadas: hash de IP, senhas (Argon2id) e tokens JWT (HS256)."""

from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import ConfigError, Settings
from app.core.errors import AuthError

JWT_ALGORITHM = "HS256"  # fixo: o algoritmo do cabeçalho do token nunca é aceito
JWT_ISSUER = "academic-search-hub"
REQUIRED_CLAIMS = ["sub", "iat", "exp", "iss", "jti"]

# Parâmetros do Argon2id: os padrões da biblioteca argon2-cffi (perfil RFC 9106 de baixa memória),
# sem valores inventados. Registrados em docs/DECISOES.md.
_hasher = PasswordHasher()


def hash_ip(ip: str, secret_key: str) -> str:
    """Devolve o hash do IP com sal derivado de `SECRET_KEY` (o IP nunca vai em claro aos logs)."""
    salt = hashlib.sha256(b"ip-hash-salt:" + secret_key.encode()).digest()
    return hmac.new(salt, ip.encode(), hashlib.sha256).hexdigest()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """`True` só se a senha confere; qualquer falha de verificação devolve `False`."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """O hash foi gerado com parâmetros mais fracos que os atuais?"""
    return _hasher.check_needs_rehash(password_hash)


@lru_cache
def dummy_password_hash() -> str:
    """Hash falso: verificado quando o e-mail não existe, para igualar o tempo de resposta."""
    return hash_password("senha-falsa-para-igualar-o-tempo")


def _require_key(settings: Settings) -> str:
    if not settings.secret_key:
        raise ConfigError("SECRET_KEY não configurada: não é possível emitir nem validar tokens.")
    return settings.secret_key


def create_access_token(user_id: uuid.UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "iss": JWT_ISSUER,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(claims, _require_key(settings), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> uuid.UUID:
    """Valida assinatura, `exp`, `iss` e claims obrigatórios; devolve o id do usuário."""
    try:
        claims = jwt.decode(
            token,
            _require_key(settings),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": REQUIRED_CLAIMS},
        )
        return uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise AuthError("Sessão inválida ou expirada. Entre novamente.") from None
