"""Aplicação FastAPI: API REST em /api/v1, documentação OpenAPI e frontend estático."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app import __version__
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.core.rate_limit import limiter, rate_limit_handler
from app.core.security_headers import SecurityHeadersMiddleware, docs_csp
from app.db import session as db_session

API_PREFIX = "/api/v1"
DOCS_PATH = "/api/docs"
OPENAPI_PATH = "/api/openapi.json"
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
TITLE = "Academic Search Hub"
DESCRIPTION = (
    "API pública, em JSON e sem estado, para buscar trabalhos acadêmicos em uma única consulta "
    "nas fontes CORE, SciELO, OpenAlex, BDTD (IBICT), UFPI e UESPI. Os resultados são unificados, "
    "sem duplicatas, e podem ser filtrados por ano e tipo de publicação."
)
CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
CORS_HEADERS = ["Authorization", "Content-Type"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    service = getattr(app.state, "search_service", None)
    if service is not None:
        await service.aclose()
    if db_session.get_engine.cache_info().currsize:
        await db_session.get_engine().dispose()


def _build_openapi(app: FastAPI) -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=[{"url": "/", "description": "Servidor atual"}],
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": (
            "Token obtido em POST /api/v1/auth/login, enviado como `Authorization: Bearer <token>`."
        ),
    }
    app.openapi_schema = schema
    return schema


def create_app(settings: Settings | None = None) -> FastAPI:
    """Monta a aplicação. Sem argumento, lê a configuração do ambiente."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=TITLE,
        description=DESCRIPTION,
        version=__version__,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=OPENAPI_PATH if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.state.limiter = limiter
    app.state.session_factory = None  # padrão: db.session.get_sessionmaker() (testes podem trocar)
    app.openapi = lambda: _build_openapi(app)  # type: ignore[method-assign]

    register_exception_handlers(app)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    docs_policy: str | None = None
    if settings.docs_enabled:
        page = get_swagger_ui_html(openapi_url=OPENAPI_PATH, title=f"{TITLE} — documentação")
        html = bytes(page.body).decode()
        docs_policy = docs_csp(html)

        @app.get(DOCS_PATH, include_in_schema=False)
        async def swagger_ui() -> HTMLResponse:
            return HTMLResponse(html)

    # Ordem: o último adicionado é o mais externo (RequestId > SecurityHeaders > CORS).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=CORS_METHODS,
        allow_headers=CORS_HEADERS,
        allow_credentials=False,
    )
    app.add_middleware(
        SecurityHeadersMiddleware,
        production=settings.app_env == "production",
        docs_path=DOCS_PATH if settings.docs_enabled else None,
        docs_policy=docs_policy,
    )
    app.add_middleware(RequestIdMiddleware)

    app.include_router(api_router, prefix=API_PREFIX)
    # O frontend é montado por último: as rotas da API têm prioridade.
    if FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


@lru_cache
def _default_app() -> FastAPI:
    return create_app()


def __getattr__(name: str) -> FastAPI:
    """`uvicorn app.main:app`: a aplicação só é criada quando alguém a pede."""
    if name == "app":
        return _default_app()
    raise AttributeError(name)
