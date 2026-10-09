"""API simulada, com estado em memória, para os testes de interface logados."""

from __future__ import annotations

import json
import uuid
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from playwright.sync_api import Page, Route

USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "full_name": "Maria de Souza",
    "email": "maria@exemplo.com",
    "created_at": "2026-10-09T10:00:00Z",
    "consent_at": "2026-10-09T10:00:00Z",
    "consent_policy_version": "1.0",
}
SOURCES = [
    {
        "slug": "openalex",
        "name": "OpenAlex",
        "kind": "api",
        "enabled": True,
        "status": "ok",
        "message": None,
    },
    {
        "slug": "bdtd",
        "name": "BDTD (IBICT)",
        "kind": "oai",
        "enabled": False,
        "status": "disabled",
        "message": "Fonte ainda não colhida",
    },
]
TOKEN = "tok-123"


def record(n: int, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": f"doi:10.1234/r{n}",
        "title": f"Letramento digital na escola número {n}",
        "authors": [{"name": f"Autor {n}", "orcid": None}],
        "abstract": "Resumo curto do trabalho.",
        "year": 2020 + n,
        "doi": f"10.1234/r{n}",
        "url": f"https://exemplo.org/trabalho/{n}",
        "pdf_url": None,
        "type": "article",
        "language": "pt",
        "keywords": [],
        "sources": [{"source": "openalex", "source_id": f"W{n}", "url": None}],
        "is_favorite": False,
    }
    return {**data, **overrides}


class FakeApi:
    def __init__(self, page: Page, *, logged_in: bool = True) -> None:
        self.favorites: list[dict[str, Any]] = []
        self.history: list[dict[str, Any]] = []
        self.search_results: list[dict[str, Any]] = [record(1), record(2), record(3)]
        self.search_total = 3
        self.calls: list[dict[str, Any]] = []
        self.fail: dict[str, tuple[int, dict[str, Any]]] = {}
        self.user: dict[str, Any] = dict(USER)
        self.password = "Senha12345"
        self.policy_version = "1.0"
        self.login_consent_required = False
        self.deleted = False
        self.taken_email = "ocupado@exemplo.com"
        if logged_in:
            page.add_init_script(f"sessionStorage.setItem('ash.token', '{TOKEN}')")
        page.route("**/api/v1/**", self._route)

    # ---- util ----
    def add_favorite(self, rec: dict[str, Any], note: str | None = None) -> dict[str, Any]:
        item = {
            "id": str(uuid.uuid4()),
            "record": {**rec, "is_favorite": True},
            "note": note,
            "created_at": "2026-10-09T10:00:00Z",
        }
        self.favorites.insert(0, item)
        return item

    def add_history(
        self, query: str, filters: dict[str, Any] | None = None, total: int | None = 10
    ) -> dict[str, Any]:
        entry = {
            "id": str(uuid.uuid4()),
            "query": query,
            "filters": filters
            or {
                "sources": None,
                "year_from": None,
                "year_to": None,
                "types": None,
                "sort": "relevance",
            },
            "result_count_estimated": total,
            "created_at": "2026-10-09T10:00:00Z",
        }
        self.history.insert(0, entry)
        return entry

    def calls_to(self, method: str, suffix: str) -> list[dict[str, Any]]:
        return [c for c in self.calls if c["method"] == method and c["path"].endswith(suffix)]

    # ---- roteamento ----
    def _route(self, route: Route) -> None:
        request = route.request
        parts = urlsplit(request.url)
        path = parts.path.removeprefix("/api/v1")
        params = dict(parse_qsl(parts.query))
        body = json.loads(request.post_data) if request.post_data else None
        call = {
            "method": request.method,
            "path": path,
            "params": params,
            "body": body,
            "auth": request.headers.get("authorization"),
        }
        self.calls.append(call)
        key = f"{request.method} {path}"
        if key in self.fail:
            status, payload = self.fail[key]
            return route.fulfill(status=status, json=payload)
        status, payload, headers = self.dispatch(request.method, path, params, body, call["auth"])
        if isinstance(payload, bytes):
            return route.fulfill(status=status, body=payload, headers=headers)
        if payload is None:
            return route.fulfill(status=status)
        return route.fulfill(status=status, json=payload, headers=headers)

    def dispatch(
        self, method: str, path: str, params: dict[str, str], body: Any, auth: str | None
    ) -> tuple[int, Any, dict[str, str]]:
        no: dict[str, str] = {}
        if path == "/sources":
            return 200, SOURCES, no
        if path.startswith("/me") or path in ("/privacy", "/auth/login", "/auth/register"):
            return self.account(method, path, body, auth)
        if path == "/search":
            return 200, self.search_body(params), no
        if path == "/favorites" and method == "POST":
            rec = body["record"]
            existing = next((f for f in self.favorites if f["record"]["id"] == rec["id"]), None)
            if existing:
                return 200, existing, no
            return 201, self.add_favorite(rec, body.get("note")), no
        if path == "/favorites" and method == "GET":
            return 200, self.favorites_page(params), no
        if path == "/favorites/export":
            fmt = params["format"]
            data = f"EXPORT-FAVORITOS-{fmt}\n".encode()
            return (
                200,
                data,
                {
                    "Content-Type": "text/plain",
                    "Content-Disposition": f'attachment; filename="exportacao-20261009.{fmt}"',
                },
            )
        if path.startswith("/favorites/"):
            fav_id = path.rsplit("/", 1)[1]
            item = next((f for f in self.favorites if f["id"] == fav_id), None)
            if item is None:
                return (
                    404,
                    {"error": {"code": "not_found", "message": "Favorito não encontrado."}},
                    no,
                )
            if method == "PATCH":
                item["note"] = (body.get("note") or "").strip() or None
                return 200, item, no
            self.favorites.remove(item)
            return 204, None, no
        if path == "/export":
            fmt = body["format"]
            data = f"EXPORT-{fmt}-{len(body['records'])}\n".encode()
            return (
                200,
                data,
                {
                    "Content-Type": "text/plain",
                    "Content-Disposition": f'attachment; filename="exportacao-20261009.{fmt}"',
                },
            )
        if path == "/history" and method == "GET":
            size = int(params.get("page_size", 20))
            page = int(params.get("page", 1))
            items = self.history[(page - 1) * size : page * size]
            return (
                200,
                {"items": items, "page": page, "page_size": size, "total": len(self.history)},
                no,
            )
        if path == "/history" and method == "DELETE":
            self.history.clear()
            return 204, None, no
        if path.startswith("/history/") and method == "DELETE":
            entry_id = path.rsplit("/", 1)[1]
            self.history[:] = [h for h in self.history if h["id"] != entry_id]
            return 204, None, no
        return (
            404,
            {"error": {"code": "not_found", "message": f"sem rota simulada: {method} {path}"}},
            no,
        )

    def search_body(self, params: dict[str, str]) -> dict[str, Any]:
        page = int(params.get("page", 1))
        ids = {f["record"]["id"] for f in self.favorites}
        results = [{**r, "is_favorite": r["id"] in ids} for r in self.search_results]
        return {
            "query": params.get("q", ""),
            "page": page,
            "page_size": 20,
            "total_estimated": self.search_total,
            "total_is_estimate": True,
            "results": results,
            "sources_status": {
                "openalex": {
                    "status": "ok",
                    "count": len(results),
                    "total": self.search_total,
                    "message": None,
                }
            },
        }

    def favorites_page(self, params: dict[str, str]) -> dict[str, Any]:
        size = int(params.get("page_size", 20))
        page = int(params.get("page", 1))
        q = (params.get("q") or "").lower()
        items = [
            f
            for f in self.favorites
            if not q or q in f["record"]["title"].lower() or q in (f["note"] or "").lower()
        ]
        return {
            "items": items[(page - 1) * size : page * size],
            "page": page,
            "page_size": size,
            "total": len(items),
        }

    # ---- conta (OS-026) ----
    def account(
        self, method: str, path: str, body: Any, auth: str | None
    ) -> tuple[int, Any, dict[str, str]]:
        no: dict[str, str] = {}
        unauthorized = (401, {"error": {"code": "unauthorized", "message": "Sessão inválida."}}, no)
        wrong = (
            403,
            {"error": {"code": "invalid_password", "message": "Senha atual incorreta."}},
            no,
        )
        if path == "/privacy":
            return (
                200,
                {"version": self.policy_version, "content": "# Política de Privacidade\n\nTexto."},
                no,
            )
        if path == "/auth/login":
            if body["password"] != self.password:
                return (
                    401,
                    {"error": {"code": "unauthorized", "message": "E-mail ou senha inválidos."}},
                    no,
                )
            return (
                200,
                {
                    "access_token": TOKEN,
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "consent_required": self.login_consent_required,
                },
                no,
            )
        if path == "/auth/register":
            return 201, self.user, no
        if auth != f"Bearer {TOKEN}" or self.deleted:
            return unauthorized
        if path == "/me" and method == "GET":
            return 200, self.user, no
        if path == "/me" and method == "PATCH":
            if body.get("email") and body["email"] != self.user["email"]:
                if body.get("current_password") != self.password:
                    return wrong
                if body["email"] == self.taken_email:
                    return (
                        409,
                        {
                            "error": {
                                "code": "conflict",
                                "message": "Não foi possível atualizar os dados.",
                            }
                        },
                        no,
                    )
                self.user["email"] = body["email"]
            if body.get("full_name"):
                self.user["full_name"] = body["full_name"]
            return 200, self.user, no
        if path == "/me/password":
            if body["current_password"] != self.password:
                return wrong
            self.password = body["new_password"]
            return 204, None, no
        if path == "/me/data-export":
            data = json.dumps(
                {"account": self.user, "favorites": self.favorites, "search_history": self.history}
            ).encode()
            headers = {
                "Content-Type": "application/json",
                "Content-Disposition": 'attachment; filename="meus-dados-20261009.json"',
            }
            return 200, data, headers
        if path == "/me/consent":
            self.user["consent_policy_version"] = self.policy_version
            return 200, self.user, no
        if path == "/me" and method == "DELETE":
            if body.get("password") != self.password:
                return wrong
            self.deleted = True
            return 204, None, no
        return 404, {"error": {"code": "not_found", "message": "sem rota"}}, no
