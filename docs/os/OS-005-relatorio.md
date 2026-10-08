# Relatório da OS-005 — Esquema unificado e normalização

**Data:** 2026-10-08

## O que foi feito
- `app/schemas/record.py`: `AuthorOut`, `SourceRef`, `RecordOut` (Pydantic v2) com validação de `http`/`https`, ano 1000–2100, idioma `^[a-z]{2}$`, título obrigatório e exemplo no OpenAPI.
- `app/services/normalize.py`: `normalize_doi`, `clean_text`, `normalize_title`, `parse_year`, `normalize_author`, `surname`, `normalize_language`, `safe_url`, `build_record_id` (+ `strip_accents`).
- `app/services/type_mapping.py`: constantes `OPENALEX_TYPE_MAP`, `CORE_TYPE_MAP`, tabela embutida de `dc:type` e `map_oai_type`.
- Testes parametrizados (108 casos novos).

## Decisões tomadas
- `map_oai_type`: o `type_map` da fonte tem precedência sobre a tabela embutida; um tipo específico (artigo, tese, livro, preprint) vence um `other` reconhecido (ex.: `bachelorThesis`); se nada for reconhecido, vale o `default_type`.
- `normalize_language` aceita um conjunto fixo de idiomas (os mais prováveis nas fontes); qualquer outro vira `None`.
- `clean_text` só remove tags bem formadas (`<tag ...>`), para não apagar texto como "5 < 7 e 9 > 3"; entidades codificadas como `&lt;script&gt;` também são removidas.
- "Sobrenome, Nome" com sobrenome todo em maiúsculas vira "Nome Sobrenome" com o sobrenome em formato de título.
- A regra de `RecordOut.url` rejeita (e não descarta) endereços inválidos; os conectores usam `safe_url` antes de montar o `RecordOut`.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check`: ruff, format, mypy e 170 testes passando. Cobertura de `normalize.py` e `type_mapping.py`: 100%.

## Critérios de aceite
- [x] `RecordOut` rejeita `url="javascript:alert(1)"` — `test_rejects_non_http_urls`
- [x] Casos de borda (DOI com maiúsculas e espaço, `javascript:`, título com `<i>`, ano `[2019]`, `SILVA, João P.`, `&amp;`, `Dissertação`, `doctoralThesis`, `raw_types` vazio) — `test_normalize.py`, `test_type_mapping.py`
- [x] `build_record_id` → `doi:10.1000/x` e `src:bdtd:abc` — `test_build_record_id`
- [x] Cobertura ≥ 95% — 100% em ambos (`pytest --cov-report=term-missing`)

## Evidência para o TCC
`docs/evidencias/os-005-mapeamento.md` (tabela viva, completada nas OS 007 a 010).
