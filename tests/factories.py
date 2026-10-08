"""Fábricas simples de objetos de domínio para os testes."""

from __future__ import annotations

import itertools
import uuid
from datetime import UTC, datetime
from typing import Any

from app.models import Favorite, HarvestRun, OaiRecord, SearchHistory, SecurityEvent, User

_counter = itertools.count(1)


def make_user(**overrides: Any) -> User:
    n = next(_counter)
    data: dict[str, Any] = {
        "email": f"usuario{n}@exemplo.com",
        "full_name": f"Usuário {n}",
        "password_hash": "hash-de-teste",
        "consent_at": datetime.now(UTC),
        "consent_policy_version": "1.0",
    }
    return User(**{**data, **overrides})


def make_favorite(user_id: uuid.UUID, **overrides: Any) -> Favorite:
    n = next(_counter)
    data: dict[str, Any] = {
        "user_id": user_id,
        "record_id": f"src:teste:{n}",
        "record_snapshot": {"title": f"Trabalho {n}"},
    }
    return Favorite(**{**data, **overrides})


def make_history(user_id: uuid.UUID, **overrides: Any) -> SearchHistory:
    n = next(_counter)
    data: dict[str, Any] = {"user_id": user_id, "query": f"consulta {n}", "filters": {}}
    return SearchHistory(**{**data, **overrides})


def make_security_event(**overrides: Any) -> SecurityEvent:
    data: dict[str, Any] = {"event_type": "login_failed", "ip_hash": "abc", "details": {}}
    return SecurityEvent(**{**data, **overrides})


def make_oai_record(**overrides: Any) -> OaiRecord:
    n = next(_counter)
    data: dict[str, Any] = {
        "source": "bdtd",
        "oai_identifier": f"oai:exemplo:{n}",
        "title": f"Título {n}",
        "authors": [],
        "keywords": [],
        "raw_types": [],
        "type": "thesis",
        "deleted": False,
    }
    return OaiRecord(**{**data, **overrides})


def make_harvest_run(**overrides: Any) -> HarvestRun:
    data: dict[str, Any] = {"source": "bdtd", "status": "running"}
    return HarvestRun(**{**data, **overrides})
