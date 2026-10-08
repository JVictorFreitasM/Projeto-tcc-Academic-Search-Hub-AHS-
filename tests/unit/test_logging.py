import json
import logging

import pytest

from app.core.logging import JsonFormatter, SensitiveDataFilter, request_id_var
from app.core.security import hash_ip

pytestmark = pytest.mark.unit


def _emit(message: str, *args: object, **extra: object) -> dict[str, object]:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, message, args or None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    SensitiveDataFilter().filter(record)
    return json.loads(JsonFormatter().format(record))  # type: ignore[no-any-return]


def test_password_is_masked() -> None:
    line = _emit("login com password=abc ok")
    assert "abc" not in str(line["message"])
    assert "password=***" in str(line["message"])


def test_authorization_bearer_is_masked() -> None:
    line = _emit("cabecalho Authorization: Bearer xyz")
    assert "xyz" not in str(line["message"])
    assert "Authorization: ***" in str(line["message"])


def test_masks_values_passed_as_format_args() -> None:
    line = _emit("dados %s", "api_key=segredo123")
    assert "segredo123" not in str(line["message"])


def test_masks_sensitive_extra_fields() -> None:
    line = _emit("evento", token="abc", headers={"Authorization": "Bearer xyz", "ok": "1"})
    assert line["token"] == "***"
    assert line["headers"] == {"Authorization": "***", "ok": "1"}


def test_json_fields_and_request_id() -> None:
    token = request_id_var.set("req-1")
    try:
        line = _emit("olá")
    finally:
        request_id_var.reset(token)
    assert {"timestamp", "level", "logger", "message", "request_id"} <= set(line)
    assert line["request_id"] == "req-1"
    assert line["message"] == "olá"


def test_hash_ip_is_stable_salted_and_not_plain() -> None:
    first = hash_ip("203.0.113.9", "s" * 32)
    assert first == hash_ip("203.0.113.9", "s" * 32)
    assert first != hash_ip("203.0.113.9", "t" * 32)
    assert "203.0.113.9" not in first
