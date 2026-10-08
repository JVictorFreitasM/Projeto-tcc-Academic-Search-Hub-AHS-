"""Funções de segurança compartilhadas."""

from __future__ import annotations

import hashlib
import hmac


def hash_ip(ip: str, secret_key: str) -> str:
    """Devolve o hash do IP com sal derivado de `SECRET_KEY` (o IP nunca vai em claro aos logs)."""
    salt = hashlib.sha256(b"ip-hash-salt:" + secret_key.encode()).digest()
    return hmac.new(salt, ip.encode(), hashlib.sha256).hexdigest()
