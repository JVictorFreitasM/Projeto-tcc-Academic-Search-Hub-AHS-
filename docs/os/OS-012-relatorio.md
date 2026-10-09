# Relatório da OS-012 — Orquestrador de busca

**Data:** 2026-10-09

## O que foi feito
- `app/schemas/search.py`: `SearchParams` (validações de 6.4), `SourceStatusOut`, `SearchResponse`.
- `app/services/search_service.py`: `SearchService.search` (disponibilidade, divisão `ceil(page_size/k)`, `asyncio.gather`, tempo limite global, intercalação, `deduplicate`, corte, ordenação por ano, favoritos).
- `app/services/favorite_service.py`: `favorite_ids_for` (ponto de extensão com implementação real; a OS-017 completa o serviço).
- `AppError.extra` (chaves ao lado de `error`) para devolver `sources_status` no 502.
- 29 testes novos com conectores falsos.

## Decisões tomadas
- O 502 leva `sources_status` como chave irmã de `error` (contrato 6.4), além de `details` com um resumo textual.
- Fonte não selecionada em `sources` aparece como `disabled` / "Fonte não selecionada.".
- `year_desc`: a página combinada é sempre ordenada por ano (nulos por último, ordenação estável); fontes sem suporte (`supports_year_sort = False`, hoje o CORE) recebem a nota na `message`.
- `GLOBAL_TIMEOUT_MARGIN = 2 s` é constante do módulo (para os testes poderem zerá-la).
- **Bug encontrado e corrigido pelos testes:** o serviço alterava `is_favorite` nos objetos do conector; agora trabalha com cópias.

## Desvios em relação à OS
`SearchParams` valida `page_size` contra `MAX_PAGE_SIZE` lendo `get_settings()`; a validação de `sources` contra os slugs registrados fica no serviço (`ValidationAppError`), pois depende dos conectores.

## Comandos executados e resultados
`ruff`, `mypy` e os testes da OS passam.

## Critérios de aceite
- [x] Conector lento não atrasa além do limite global — `test_slow_connector_does_not_delay_beyond_global_limit`
- [x] Fonte com erro não impede as demais — `test_failing_source_does_not_stop_the_others`
- [x] Todas falhando → 502 com `sources_status` — `test_all_failing_raises_502_with_sources_status`, `test_all_disabled_raises_502`
- [x] Duplicata entre fontes vira um registro com duas entradas em `sources` — `test_duplicate_between_sources_becomes_one_record_with_two_sources`
- [x] `total_is_estimate` sempre `true` — `test_all_ok_splits_page_interleaves_and_sums_totals`

## Evidência para o TCC
`docs/evidencias/os-012-sequencia.md` (diagrama Mermaid `sequenceDiagram`).
