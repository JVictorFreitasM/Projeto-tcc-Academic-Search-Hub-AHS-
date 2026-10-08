# Relatório da OS-002 — Configuração, logging e tratamento de erros

**Data:** 2026-10-08

## O que foi feito
- `app/core/config.py`: `Settings` (pydantic-settings) com todas as variáveis de 5.4, `get_settings()` com cache e `ConfigError` que cita só o nome da variável.
- `app/core/logging.py`: logs JSON no stdout (`timestamp`, `level`, `logger`, `message`, `request_id`) e filtro que mascara `password`, `token`, `authorization`, `api_key`, `secret` na mensagem, nos argumentos e nos campos extras.
- `app/core/errors.py`: `AppError` e subclasses; tratadores para `AppError`, `RequestValidationError`, `HTTPException` (404/405 etc.) e exceção genérica (500 `internal_error`, detalhe só no log).
- `app/core/middleware.py`: `RequestIdMiddleware` (UUID, `X-Request-ID`, contextvar para os logs).
- `app/core/security.py`: `hash_ip` (HMAC-SHA256 com sal derivado de `SECRET_KEY`).

## Decisões tomadas
- Em `development`, `SECRET_KEY` vazia é aceita (registrado em `DECISOES.md`).
- Erros de validação devolvem só campo e motivo, nunca o valor recebido.
- O `request_id` também vai em `request.state`, para sair no cabeçalho das respostas 500 (geradas fora do middleware).
- Tratei também `HTTPException` do Starlette, para que 404/405 também sigam o formato 6.5 (critério "toda resposta de erro").

## Desvios em relação à OS
Nenhum. `app/main.py` não foi criado (é da OS-014); os testes montam um app mínimo.

## Comandos executados e resultados
`python tasks.py check`: ruff, ruff format, mypy (16 arquivos) sem erros; 27 testes passaram. Aviso não bloqueante do Starlette sobre `httpx` no `TestClient`.

## Critérios de aceite
- [x] `password=abc` e `Authorization: Bearer xyz` saem mascarados — `test_logging.py::test_password_is_masked`, `test_authorization_bearer_is_masked`
- [x] exceção qualquer vira 500 genérico sem stack trace — `test_errors.py::test_unexpected_exception_becomes_generic_500`
- [x] falta de `SECRET_KEY` em produção impede a inicialização — `test_config.py::test_missing_secret_key_in_production_blocks_startup`
- [x] toda resposta de erro tem o formato 6.5 — testes de AppError, validação, 404/405 e 500

## Evidência para o TCC
`docs/evidencias/os-002.md` (linha de log e respostas de erro reais).
