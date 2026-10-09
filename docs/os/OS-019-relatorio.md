# Relatório da OS-019 — Exportação (BibTeX, RIS, JSON, CSV)

**Data:** 2026-10-09

## O que foi feito
- `app/services/export_service.py`: `to_bibtex`, `to_ris`, `to_json`, `to_csv` (geradores próprios), escape do BibTeX, chaves de citação únicas e neutralização de fórmulas no CSV.
- `app/api/v1/export.py`: `GET /api/v1/favorites/export?format=` (login; registra o evento `data_exported`) e `POST /api/v1/export` (até 100 registros, sem login), com `Content-Type` e `Content-Disposition` corretos. Incluída antes de `/favorites/{id}`.
- 49 testes (31 unitários, com ida e volta do RIS, do JSON e do CSV, e 18 de integração).
- Arquivos de exemplo em `docs/evidencias/os-019/`.

## Decisões tomadas
Em `docs/DECISOES.md`: formato dos nomes e partículas, apóstrofo no CSV, `@thesis`/`THES`.
Chave de citação: `sobrenome + ano + primeira palavra (3+ letras)`, sem acento; sem autor/ano/palavra usa `anon`/`nd`/`sem`. Duplicatas ganham `a`, `b`, `c`... (depois `aa`, `ab`...).

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde.

## Critérios de aceite
- [x] Os quatro formatos geram saída válida para os casos de borda (`&`, `%`, `{`, autor com acento, registro sem ano/DOI/autores, chaves repetidas, `=HYPERLINK(...)`) — `test_export_service.py`
- [x] Chaves BibTeX únicas — `test_bibtex_keys_are_unique_in_the_file`
- [x] CSV neutraliza fórmulas — `test_csv_neutralizes_formula_injection`, `test_csv_export_neutralizes_formulas_end_to_end`
- [x] Mais de 100 registros em `POST /export` → 422 — `test_more_than_100_records_is_422`
- [x] `Content-Disposition` correto nos quatro formatos — `test_export_search_results_without_login`, `test_export_favorites_requires_login_and_returns_only_own`

## Evidência para o TCC
`docs/evidencias/os-019/` (exemplos com dados fictícios). **Pendente (desenvolvedor):** importar o `.bib` e o `.ris` no Zotero ou Mendeley e registrar o resultado em `docs/evidencias/os-019/LEIA-ME.md`.
