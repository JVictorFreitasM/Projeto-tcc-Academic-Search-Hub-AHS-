"""Logs estruturados em JSON, com máscara para dados sensíveis."""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

SENSITIVE_KEYS = ("password", "token", "authorization", "api_key", "secret")
MASK = "***"

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# chave, separador (= ou :, com aspas opcionais), "Bearer " opcional e o valor.
_SENSITIVE_RE = re.compile(
    r"(?P<key>\w*(?:" + "|".join(SENSITIVE_KEYS) + r")\w*)(?P<sep>[\"']?\s*[:=]\s*[\"']?)"
    r"(?:(?:bearer|basic)\s+)?(?P<value>[^\s,;&\"'}]+)",
    re.IGNORECASE,
)
_STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}


def mask_text(text: str) -> str:
    """Mascara valores de campos sensíveis em um texto livre."""
    return _SENSITIVE_RE.sub(lambda m: f"{m['key']}{m['sep']}{MASK}", text)


def _is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(word in lowered for word in SENSITIVE_KEYS)


def _mask_value(key: str, value: Any) -> Any:
    if _is_sensitive(key):
        return MASK
    if isinstance(value, dict):
        return {k: _mask_value(str(k), v) for k, v in value.items()}
    if isinstance(value, str):
        return mask_text(value)
    return value


class SensitiveDataFilter(logging.Filter):
    """Remove dados sensíveis da mensagem e dos campos extras antes de formatar."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = mask_text(record.getMessage())
        record.args = None
        for key in set(record.__dict__) - _STANDARD_ATTRS:
            setattr(record, key, _mask_value(key, record.__dict__[key]))
        return True


class JsonFormatter(logging.Formatter):
    """Formata cada registro como uma linha JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None) or request_id_var.get()
        if request_id:
            payload["request_id"] = request_id
        for key in set(record.__dict__) - _STANDARD_ATTRS - {"request_id"}:
            payload[key] = record.__dict__[key]
        if record.exc_info:
            payload["exception"] = mask_text(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configura o logger raiz para emitir JSON no stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SensitiveDataFilter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
