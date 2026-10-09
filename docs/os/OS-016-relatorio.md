# Relatório da OS-016 — Rota de busca

**Data:** 2026-10-09

## O que foi feito
- `app/api/v1/search.py`: `GET /api/v1/search` (parâmetros de 6.4, com descrição em português, `BackgroundTasks` para o histórico, limite `RATE_LIMIT_SEARCH`) e `GET /api/v1/sources`.
- `SearchService`: `describe_sources()`, `build_default_service()` e `favorite_lookup` por chamada; `Connector.kind` (`api`/`oai`); `SourceInfo` em `app/schemas/search.py`.
- `app/core/errors.py`: tradução para o português das mensagens de validação do FastAPI/Pydantic (campo obrigatório, inteiro, mínimos e máximos...).
- Serviço criado na primeira busca e fechado no `lifespan`.
- 25 testes de integração.

## Decisões tomadas
- Esta é a OS-016 **completa** (não a reduzida da Fatia 1): há usuário opcional, `is_favorite` e ponto de chamada do histórico.
- O histórico é chamado por `app.state.history_recorder` (padrão: não faz nada); a OS-018 liga o gravador real. A chamada roda **depois** da resposta e uma falha nela é só registrada em log.
- `page_size` ausente usa `DEFAULT_PAGE_SIZE`; o máximo (`MAX_PAGE_SIZE`) é validado no `SearchParams`.
- `/sources` devolve `slug`, `name`, `kind`, `enabled`, `status` e `message` (motivo, como "Fonte ainda não colhida"); nenhuma URL, chave ou contagem.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde.

## Critérios de aceite
- [x] Busca de visitante devolve resultados com `is_favorite=false` — `test_visitor_search_returns_results_without_favorites`
- [x] Parâmetros inválidos → 422 no formato 6.5 — `test_invalid_parameters_give_422_in_standard_format`, `test_one_character_query_message_is_in_portuguese`
- [x] Todas as fontes falhando → 502 com `sources_status` — `test_all_sources_failing_gives_502_with_sources_status`
- [x] `/api/v1/sources` não vaza chaves nem URLs internas — `test_sources_endpoint_lists_state_without_leaking`
- [x] O OpenAPI descreve todos os parâmetros e a resposta — `test_openapi_describes_parameters_and_response`

## Evidência para o TCC
`docs/evidencias/os-016-exemplo.json`: requisição e resposta **com dados fictícios** (conectores falsos; o arquivo avisa). Pendente (desenvolvedor): um exemplo real com as chaves configuradas.
