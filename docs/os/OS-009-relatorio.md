# Relatório da OS-009 — Colheita OAI-PMH multi-fonte

**Data:** 2026-10-08

## O que foi feito
- `config/oai_sources.yml` com as quatro fontes (todas `enabled: false`, `base_url: TODO-VERIFICAR`) e `app/harvest/oai_sources.py` (validação Pydantic, `safe_load`).
- `app/harvest/oai_client.py`: `identify`, `list_sets`, `list_records` (segue o `resumptionToken`, limite de páginas), `get_record`, `fetch_raw`; `defusedxml` com `forbid_dtd=True`; espera por HTTP 503 (3 tentativas); pausa entre requisições; erros do protocolo.
- `app/harvest/mapping.py`: `parse_oai_dc` (função pura) e `parse_datestamp`.
- `app/harvest/harvester.py`: `harvest_source` (incremental/`full`, `limit`, `dry-run`, lotes de 500, upsert, cabeçalho `deleted`, `harvest_runs`).
- `app/harvest/cli.py` (`identify`, `sets`, `dump`, `run`, `run-all`, `status`) e `app/core/loop.py`.
- Fixtures sintéticas em `tests/fixtures/oai/synthetic/` e 69 testes novos (unitários e de integração).

## Decisões tomadas
Em `docs/DECISOES.md`: `pyyaml` e stubs de tipos; fixtures sintéticas; resultado da validação real; colheita limitada termina como `partial`; comando extra `dump`.

## Desvios em relação à OS
- **Passo manual 0 não concluído:** nenhuma fonte devolveu OAI-PMH válido a este ambiente (BDTD e UESPI com desafio anti-robô/HTML, UFPI com 502, SciELO sem OAI nos caminhos testados). Não se contornou proteção alguma. Fontes ficam desabilitadas; ver `docs/evidencias/os-009-fontes.md`.
- Consequência para os critérios abaixo: eles foram provados com fixtures sintéticas e servidor falso (`respx`); **a colheita real ainda não foi exercitada**.

## Comandos executados e resultados
`python tasks.py check` verde (ruff, format, mypy e toda a suíte).

## Critérios de aceite
- [x] Duas páginas com `resumptionToken` trazem todos os registros — `test_two_pages_following_resumption_token`
- [x] `noRecordsMatch` não é erro — `test_no_records_match_is_not_an_error`
- [x] XML com DTD/entidade externa é recusado — `test_dtd_and_external_entities_are_refused`, `test_xxe_response_marks_run_as_error`
- [x] Rodar duas vezes não duplica — `test_running_twice_does_not_duplicate`
- [x] `deleted` marca `deleted=true` (a ausência nas buscas é testada na OS-010) — `test_deleted_header_marks_record_deleted`
- [x] `run` sem `CONTACT_EMAIL` recusa — `test_contact_email_is_required`, `test_run_refuses_without_contact_email`
- [x] `status` mostra contagens por fonte — `test_run_then_status_shows_counts`
- [x] Nenhum teste usa rede real

## Evidência para o TCC
`docs/evidencias/os-009-fontes.md` (sem totais: nada foi colhido de fonte real).
