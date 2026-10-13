"""Erros da aplicação e conversão para o formato padrão de erro (6.5)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Erro previsto, com código, mensagem para o usuário e status HTTP."""

    code = "app_error"
    status_code = 400
    default_message = "Não foi possível concluir a operação."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: list[dict[str, str]] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.details = details
        self.extra = extra  # chaves acrescentadas ao lado de "error" (ex.: sources_status no 502)
        super().__init__(self.message)


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404
    default_message = "Recurso não encontrado."


class ConflictError(AppError):
    code = "conflict"
    status_code = 409
    default_message = "A operação conflita com o estado atual."


class AuthError(AppError):
    code = "unauthorized"
    status_code = 401
    default_message = "Autenticação necessária ou inválida."


class ForbiddenError(AppError):
    code = "forbidden"
    status_code = 403
    default_message = "Você não tem permissão para esta operação."


class ValidationAppError(AppError):
    code = "validation_error"
    status_code = 422
    default_message = "Dados inválidos."


class UpstreamError(AppError):
    code = "upstream_error"
    status_code = 502
    default_message = "Uma fonte externa falhou."


class RateLimitedError(AppError):
    code = "rate_limited"
    status_code = 429
    default_message = "Muitas requisições. Tente novamente em instantes."

    def __init__(self, message: str | None = None, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


_HTTP_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    429: "rate_limited",
}
_HTTP_MESSAGES = {
    404: "Recurso não encontrado.",
    405: "Método não permitido.",
}


def error_body(
    code: str, message: str, details: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    """Monta o corpo no formato 6.5."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


def _response(request: Request, status_code: int, body: dict[str, Any]) -> JSONResponse:
    response = JSONResponse(body, status_code=status_code)
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):
        raise exc
    body = error_body(exc.code, exc.message, exc.details)
    if exc.extra:
        body.update(exc.extra)
    return _response(request, exc.status_code, body)


def translate_validation_message(err: dict[str, Any]) -> str:
    """Mensagem em português para os erros de validação mais comuns do Pydantic/FastAPI."""
    ctx = err.get("ctx") or {}
    kind = err.get("type", "")
    table = {
        "missing": "campo obrigatório",
        "int_parsing": "deve ser um número inteiro",
        "int_from_float": "deve ser um número inteiro",
        "bool_parsing": "deve ser verdadeiro ou falso",
        "string_type": "deve ser um texto",
        "greater_than_equal": f"deve ser maior ou igual a {ctx.get('ge')}",
        "less_than_equal": f"deve ser menor ou igual a {ctx.get('le')}",
        "greater_than": f"deve ser maior que {ctx.get('gt')}",
        "less_than": f"deve ser menor que {ctx.get('lt')}",
        "string_too_short": f"deve ter ao menos {ctx.get('min_length')} caracteres",
        "string_too_long": f"deve ter no máximo {ctx.get('max_length')} caracteres",
        "too_short": f"deve ter ao menos {ctx.get('min_length')} itens",
        "too_long": f"deve ter no máximo {ctx.get('max_length')} itens",
        "json_invalid": "JSON inválido",
        "model_attributes_type": "formato inválido",
        "dict_type": "formato inválido",
        "list_type": "deve ser uma lista",
        "url_parsing": "endereço inválido",
        "enum": "valor não permitido",
    }
    message = table.get(kind)
    if message is not None:
        return message
    return str(err["msg"]).removeprefix("Value error, ")


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    # Só campo e motivo: o valor recebido pode ser sensível e não é devolvido.
    details = [
        {
            "field": ".".join(str(part) for part in err["loc"] if part not in ("query", "body")),
            "issue": translate_validation_message(err),
        }
        for err in exc.errors()
    ]
    body = error_body("validation_error", "Dados inválidos.", details)
    return _response(request, 422, body)


async def _handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    code = _HTTP_CODES.get(exc.status_code, "http_error")
    message = _HTTP_MESSAGES.get(exc.status_code, "Não foi possível concluir a operação.")
    return _response(request, exc.status_code, error_body(code, message))


async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    # O detalhe (com traceback) vai só para o log; o cliente recebe mensagem genérica.
    logger.error(
        "Erro não tratado",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={"request_id": request_id},
    )
    body = error_body("internal_error", "Erro interno. Tente novamente mais tarde.")
    return _response(request, 500, body)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os tratadores que devolvem sempre o formato 6.5."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected)
