# Relatório da OS-004 — Modelos de dados e migração inicial

**Data:** 2026-10-08

## O que foi feito
- Modelos em `app/models/`: `User`, `Favorite`, `SearchHistory`, `SecurityEvent`, `OaiRecord`, `HarvestRun`; enum `RecordType` em `app/schemas/common.py`.
- Migração `0002_tabelas_dominio` (gerada por autogenerate e revisada à mão), com o gatilho de `search_vector`.
- `tests/factories.py` e `tests/integration/test_models.py` (23 testes).

## Decisões tomadas
- `search_vector` é mantido por **gatilho** (opção prevista na OS): uma coluna gerada não consegue achatar o JSONB de palavras-chave com funções imutáveis. Pesos: título A, palavras-chave B, resumo C. O gatilho dispara em INSERT e em UPDATE de `title`, `abstract` e `keywords`.
- `type` (oai_records), `status` (harvest_runs) e `event_type` usam `TEXT` + `CHECK` em vez de enum nativo do PostgreSQL (mais simples de migrar).
- `ip_hash` aceita nulo (eventos sem IP, como os da CLI).
- `search_vector` no modelo é `deferred`, para não ser carregado nas consultas comuns.
- Teste `alembic check` garante que modelos e migração não divergem.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check`: ruff, format, mypy e 62 testes passando (23 novos).

## Critérios de aceite
- [x] `upgrade head` cria as seis tabelas e `downgrade` as remove — `test_all_six_tables_exist`, `test_downgrade_to_0001_removes_the_six_tables`
- [x] Dois favoritos iguais para o mesmo usuário falham — `test_duplicate_favorite_fails`
- [x] Excluir usuário apaga favoritos e histórico e mantém `security_events` — `test_deleting_user_cascades_but_keeps_security_events`
- [x] E-mail com maiúscula rejeitado pelo banco — `test_uppercase_email_is_rejected_by_database`
- [x] `to_tsquery('pt_unaccent','educacao')` encontra "Educação" — `test_search_vector_finds_title_without_accent`; uso do índice GIN com 3.000 linhas — `test_gin_index_is_usable_for_search` (com `enable_seqscan=off` só no teste, para tornar o plano determinístico)

## Evidência para o TCC
`docs/evidencias/os-004-er.md` (diagrama Mermaid `erDiagram`).
