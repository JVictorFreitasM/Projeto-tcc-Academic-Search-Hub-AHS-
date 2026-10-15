# Relatório da OS-008 — Conector CORE

**Data:** 2026-10-08

## O que foi feito
- `app/connectors/core_api.py`: `CoreConnector`, `work_to_record`, `build_query_string`.
- Registrado em `build_connectors`; `supports_year_sort` declarado nos dois conectores de API.
- Fixture sintética `tests/fixtures/core/search_ok.json` (4 resultados: completo, mínimo, sem título, com endereços perigosos) e 13 testes.

## Decisões tomadas
Registradas em `docs/DECISOES.md`: fixture sintética (pendência), sintaxe `[VERIFICAR]` dos filtros em `q`, ausência de ordenação por ano, filtro local para `preprint` e `other`.
A consulta do usuário vai entre parênteses, para que os filtros acrescentados com `AND` não mudem o sentido dela; caracteres não imprimíveis são removidos.

## Desvios em relação à OS
Passo manual 0 não executado (sem chave): fixture sintética, como a OS permite.

## Comandos executados e resultados
`python tasks.py check` verde; mypy sem erros.

## Critérios de aceite
- [x] Com `respx` e a fixture, devolve `RecordOut` válidos e o total correto (4321) — `test_search_returns_valid_records_total_and_ignored_count`
- [x] Sem chave, devolve `disabled` e não faz requisição — `test_disabled_without_key`
- [x] 429 e timeout tratados — `test_rate_limited_mentions_retry_after`, `test_timeout`
- [x] Resultado sem título é ignorado e contado — mensagem "1 resultados sem título foram ignorados."

## Evidência para o TCC
Mapeamento do CORE em `docs/evidencias/os-005-mapeamento.md` (a conferir com resposta real). **Pendente (desenvolvedor):** busca real em `docs/evidencias/os-008-busca-real.json`, sem a chave.

## Adendo de validação — 15/10/2026

A pendência acima foi resolvida depois da OS original. Uma chave válida foi usada somente no
ambiente local e não foi gravada no repositório. A fixture `tests/fixtures/core/search_ok.json` foi
substituída por uma resposta real da API v3. Foram confirmados, com respostas reais, os filtros de
ano e tipo, a consulta por autor, a paginação e o limite de 100 resultados. A saída da validação está
em `docs/evidencias/core-validacao-real.txt`. Os totais pertencem ao instante da consulta e podem
mudar.
