import logging

import pytest
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient

from app.core.errors import (
    AppError,
    AuthError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitedError,
    UpstreamError,
    ValidationAppError,
    register_exception_handlers,
)
from app.core.middleware import RequestIdMiddleware

pytestmark = pytest.mark.unit


def build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ok")
    async def ok() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("falha interna: senha do banco é hunter2")

    @app.get("/app-error")
    async def app_error() -> None:
        raise NotFoundError("Trabalho não encontrado.", details=[{"field": "id", "issue": "x"}])

    @app.get("/validate")
    async def validate(q: str = Query(min_length=2)) -> dict[str, str]:
        return {"q": q}

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(build_app(), raise_server_exceptions=False)


def assert_standard_error(body: dict[str, object]) -> dict[str, object]:
    assert set(body) == {"error"}
    error = body["error"]
    assert isinstance(error, dict)
    assert isinstance(error["code"], str)
    assert isinstance(error["message"], str)
    return error


def test_unexpected_exception_becomes_generic_500(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR):
        response = client.get("/boom")
    assert response.status_code == 500
    error = assert_standard_error(response.json())
    assert error["code"] == "internal_error"
    assert "Traceback" not in response.text
    assert "hunter2" not in response.text
    assert "RuntimeError" not in response.text
    # o detalhe fica só no log
    assert any(r.exc_info for r in caplog.records)


def test_app_error_uses_standard_format(client: TestClient) -> None:
    response = client.get("/app-error")
    assert response.status_code == 404
    error = assert_standard_error(response.json())
    assert error["code"] == "not_found"
    assert error["details"] == [{"field": "id", "issue": "x"}]


def test_validation_error_uses_standard_format(client: TestClient) -> None:
    response = client.get("/validate", params={"q": "a"})
    assert response.status_code == 422
    error = assert_standard_error(response.json())
    assert error["code"] == "validation_error"
    assert error["details"][0]["field"] == "q"  # type: ignore[index]
    assert "input" not in response.text


def test_unknown_route_and_wrong_method_use_standard_format(client: TestClient) -> None:
    assert assert_standard_error(client.get("/nao-existe").json())["code"] == "not_found"
    response = client.post("/ok")
    assert response.status_code == 405
    assert assert_standard_error(response.json())["code"] == "method_not_allowed"


def test_request_id_header_on_success_and_error(client: TestClient) -> None:
    assert client.get("/ok").headers["X-Request-ID"]
    assert client.get("/app-error").headers["X-Request-ID"]
    assert client.get("/boom").headers["X-Request-ID"]
    assert client.get("/ok").headers["X-Request-ID"] != client.get("/ok").headers["X-Request-ID"]


@pytest.mark.parametrize(
    ("error_class", "status", "code"),
    [
        (NotFoundError, 404, "not_found"),
        (ConflictError, 409, "conflict"),
        (AuthError, 401, "unauthorized"),
        (ForbiddenError, 403, "forbidden"),
        (ValidationAppError, 422, "validation_error"),
        (UpstreamError, 502, "upstream_error"),
        (RateLimitedError, 429, "rate_limited"),
    ],
)
def test_error_hierarchy(error_class: type[AppError], status: int, code: str) -> None:
    error = error_class()
    assert (error.status_code, error.code) == (status, code)
    assert error.message
