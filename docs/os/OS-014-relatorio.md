# Relatório da OS-014 — FastAPI base, OpenAPI, saúde, CORS e cabeçalhos

**Data:** 2026-10-09

## O que foi feito
- `app/main.py`: `create_app()` (erros 6.5, `X-Request-ID`, CORS restrita, cabeçalhos de segurança, `slowapi`, rotas `/api/v1`, OpenAPI em `/api/openapi.json`, Swagger em `/api/docs`, frontend estático em `/` por último). `app.main:app` é criado sob demanda.
- `app/core/security_headers.py`, `app/core/rate_limit.py` (429 no formato padrão, com `Retry-After`).
- `app/api/v1/health.py` (`{"status","database","version"}`), `app/api/v1/router.py` (respostas 422/429/500 com `ErrorResponse` em todas as rotas) e `ErrorResponse` em `app/schemas/common.py`.
- `app/run.py` (`python -m app.run`, um processo, `SelectorEventLoop` no Windows, `proxy_headers` só de 127.0.0.1) e alvo `run` do `tasks.py`.
- `docs/SEGURANCA.md` com as limitações (limite em memória; CSP do `/api/docs`).
- 19 testes de integração.

## Decisões tomadas
- A página `/api/docs` é servida por rota própria, com CSP separada (script embutido liberado por hash, CDN do Swagger liberado); o resto mantém a política estrita, sem `unsafe-inline`.
- `DOCS_ENABLED=false` já desliga `/api/docs` e `/api/openapi.json` (a OS-027 só confere).
- Limitação do limite em memória registrada em `docs/SEGURANCA.md` e em `docs/DECISOES.md`.

## Desvios em relação à OS
Nenhum. O alvo para subir é `python -m app.run` (equivalente ao `uvicorn app.main:app`, mas com o loop de eventos correto no Windows); `uvicorn app.main:app` também funciona no Linux.

## Comandos executados e resultados
`python tasks.py check` verde. Servidor real iniciado com `python -m app.run`: `/api/v1/health` → 200 com `database: ok`; `/api/docs` → 200 (`docs/evidencias/os-014-cabecalhos.txt`).

## Critérios de aceite
- [x] `GET /api/v1/health` 200 com banco ok; 200 com `database:"error"` sem detalhes se o banco cair — `test_health_with_database_ok`, `test_health_with_database_down_has_no_details`
- [x] `GET /api/openapi.json` é OpenAPI 3.x com as chaves obrigatórias — `test_openapi_document`
- [x] Origem fora da lista não recebe `Access-Control-Allow-Origin` — `test_cors_foreign_origin_gets_no_header`
- [x] Todos os cabeçalhos presentes — `test_security_headers_on_every_response`, `test_hsts_only_in_production`
- [x] O servidor sobe e `/api/docs` abre — execução real registrada na evidência (a renderização visual da página será conferida na OS-032)

## Evidência para o TCC
`docs/evidencias/os-014-cabecalhos.txt` (cabeçalhos reais). A captura de `/api/docs` fica para a OS-032.
