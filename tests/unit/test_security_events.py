from types import SimpleNamespace
from typing import Any

import pytest
from starlette.requests import Request

from app.core.config import Settings
from app.services.security_events import record_event

pytestmark = pytest.mark.unit


class FakeSession:
    def __init__(self) -> None:
        self.added: list[Any] = []

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        return None


def make_request(ip: str = "203.0.113.9") -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "client": (ip, 5000),
        "app": SimpleNamespace(
            state=SimpleNamespace(settings=Settings(_env_file=None, secret_key="k" * 40))  # type: ignore[call-arg]
        ),
    }
    return Request(scope)


@pytest.mark.parametrize(
    "details",
    [
        {"email": "a@b.com"},
        {"Email": "x"},
        {"password": "x"},
        {"token": "x"},
        {"name": "Maria"},
        {"ip": "x"},
        {"user_agent": "Mozilla"},
        {"outer": {"inner": {"email": "x"}}},
        {"lista": [{"token": "x"}]},
        {"qualquer": "maria@exemplo.com"},
        {"qualquer": "veio de 203.0.113.9"},
        {"lista": ["ok", "x@y.com"]},
    ],
)
async def test_personal_data_in_details_is_refused(details: dict[str, Any]) -> None:
    session = FakeSession()
    with pytest.raises(ValueError, match="details"):
        await record_event(session, "login_failed", details=details)  # type: ignore[arg-type]
    assert session.added == []  # nada foi gravado


async def test_harmless_details_are_accepted() -> None:
    session = FakeSession()
    await record_event(session, "rate_limited", details={"path": "/api/v1/auth/login", "n": 3})  # type: ignore[arg-type]
    assert session.added[0].details == {"path": "/api/v1/auth/login", "n": 3}


async def test_unknown_event_type_is_refused() -> None:
    with pytest.raises(ValueError, match="desconhecido"):
        await record_event(FakeSession(), "algo_novo")  # type: ignore[arg-type]


async def test_ip_hash_is_computed_from_the_request_and_never_clear() -> None:
    session = FakeSession()
    await record_event(session, "login_failed", request=make_request())  # type: ignore[arg-type]
    event = session.added[0]
    assert event.ip_hash and len(event.ip_hash) == 64
    assert "203.0.113.9" not in event.ip_hash
    other = FakeSession()
    await record_event(other, "login_failed", request=make_request("198.51.100.4"))  # type: ignore[arg-type]
    assert other.added[0].ip_hash != event.ip_hash


async def test_event_without_request_has_no_ip_hash_and_user_is_optional() -> None:
    session = FakeSession()
    await record_event(session, "account_deleted")  # type: ignore[arg-type]
    event = session.added[0]
    assert event.ip_hash is None and event.user_id is None and event.details == {}
