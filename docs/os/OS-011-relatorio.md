# Relatório da OS-011 — Deduplicação

**Data:** 2026-10-09

## O que foi feito
`app/services/dedup.py`: `deduplicate` (estável, linear, idempotente), `merge`, `doi_key`, `title_key`. 27 testes em `tests/unit/test_dedup.py`.

## Decisões tomadas
- Dois registros com **DOIs diferentes** nunca se fundem por título (são trabalhos distintos), mesmo com título, ano e autor iguais. A OS não dizia isso; é a leitura mais segura da regra.
- Se um registro casa com um grupo pelo DOI e com outro pelo título, vale o DOI.
- O `id` do resultado é recalculado com `build_record_id` usando a primeira fonte do registro base.
- Entradas não são alteradas (`model_copy`).

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`ruff`, `mypy` e os 27 testes passam.

## Critérios de aceite
- [x] Todos os casos pedidos: mesmo DOI (caixa diferente) em OpenAlex/CORE; mesmo título sem DOI em CORE/UESPI; títulos curtos não fundem; anos diferentes não fundem; três fontes; sem DOI herda DOI — `test_dedup.py`
- [x] 5.000 registros sintéticos terminam sem crescimento quadrático — `test_5000_records_finish_quickly` (só verifica que termina; nenhum tempo é afirmado na documentação)
- [x] Idempotência — `test_idempotent` (10 sementes aleatórias de 300 registros)

## Evidência para o TCC
`docs/evidencias/os-011-exemplo.md`, **ilustrativo com dados fictícios**. Pendente (desenvolvedor): uma fusão real.
