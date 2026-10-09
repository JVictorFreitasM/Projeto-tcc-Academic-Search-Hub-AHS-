# Relatório da OS-010 — Conectores sobre o índice local

**Data:** 2026-10-09

## O que foi feito
- `app/connectors/oai_local.py`: `OaiLocalConnector(slug, name, session_factory, enabled)` com `websearch_to_tsquery('pt_unaccent', :q)`, filtros de ano e tipo, ordenação por relevância (`ts_rank_cd`) ou por ano (nulos por último), paginação, total por `COUNT(*)` e conversão para `RecordOut`.
- `Connector.availability()` (novo no contrato) em OpenAlex, CORE e OAI local.
- `app/connectors/registry.py`: um conector por fonte do YAML, ordem fixa das fontes.
- 19 testes de integração em `tests/integration/test_oai_local.py`.

## Decisões tomadas
Em `docs/DECISOES.md`: `availability()`, registro de todas as fontes do YAML, registros sem ano fora do filtro de ano, evidência de `EXPLAIN` provisória.
Consulta só com palavras comuns demais (`numnode = 0`): página vazia, `status=ok`, com mensagem.

## Desvios em relação à OS
`is_enabled()` devolve só o `enabled` do YAML; o "tem ao menos um registro" ficou em `availability()`/`search()` porque exige consulta ao banco (assíncrona).

## Comandos executados e resultados
`ruff` e `mypy` limpos; 19 testes novos passando.

## Critérios de aceite
- [x] "educacao" encontra "Educação" (e "educação" dá o mesmo resultado) — `test_accent_and_no_accent_give_same_result`
- [x] Filtros de ano e tipo; `deleted=true` nunca aparece — `test_year_and_type_filters`, `test_deleted_records_never_appear`
- [x] Duas fontes no mesmo banco não se misturam — `test_two_sources_do_not_mix`
- [x] `year_desc` coloca nulos por último — `test_year_desc_puts_nulls_last_and_relevance_orders_title_first`
- [x] `'; DROP TABLE users;--` não causa erro de SQL — `test_malicious_text_causes_no_sql_error`
- [x] Fonte sem registros devolve `disabled` com a mensagem — `test_source_without_records_is_disabled_with_message`

## Evidência para o TCC
`docs/evidencias/os-010-explain.txt`: **com dados sintéticos** (30.000 registros, removidos ao final); o próprio arquivo avisa. Execução da busca com filtro de ano: ~36 ms (consulta) e ~18 ms (contagem) neste computador; não é desempenho de produção nem de dados reais.
