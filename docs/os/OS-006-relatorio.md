# Relatório da OS-006 — Contrato de conectores e cliente HTTP resiliente

**Data:** 2026-10-08

## O que foi feito
- `app/connectors/base.py`: `SourceStatus`, `SourceQuery`, `SourcePage`, `Connector` (Protocol).
- `app/connectors/http.py`: `make_client`, `get_json` (tentativas, 429, limite de 5 MB, log sem chave) e as exceções `UpstreamTimeoutError`, `UpstreamHttpError`, `ResponseTooLargeError`.
- `app/connectors/registry.py`: `build_connectors` (lista vazia por ora; os conectores entram nas OS-007, 008 e 010) e a ordem fixa das fontes.
- `RateLimitedError` ganhou `retry_after`; `app.__version__`.

## Decisões tomadas
- `get_json` aceita `sleep` injetável, para testar a espera sem atraso real.
- O log leva só o endereço sem consulta; a mascaração por regex continua valendo como segunda barreira.
- **Achado:** o logger do `httpx` vazava a chave em INFO; `configure_logging` agora limita `httpx` e `httpcore` a WARNING.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde (ruff, format, mypy, testes). 23 testes novos em `tests/unit/test_http_client.py`.

## Critérios de aceite
- [x] Os seis cenários de `respx` passam (sucesso, timeout, 503→200, 404 sem repetição, 429 com `Retry-After`, resposta grande) — `test_http_client.py`
- [x] Nenhum teste faz chamada de rede real — todos usam `respx`
- [x] O log de uma chamada com `api_key=SEGREDO` não contém `SEGREDO` — `test_production_log_never_contains_api_key`, `test_app_log_record_never_contains_api_key`

## Evidência para o TCC
`docs/evidencias/os-006.md`.
