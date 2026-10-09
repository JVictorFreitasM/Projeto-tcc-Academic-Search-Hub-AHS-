# Relatório da OS-013 — Raspagem complementar de resumo

**Data:** 2026-10-09

## O que foi feito
- `app/scraping/polite_scraper.py`: `PoliteScraper` (`robots.txt` com cache, pausa de 2 s por domínio, redirecionamentos conferidos, 1 MB, só HTML).
- `app/scraping/abstract_extractor.py`: `extract_abstract` na ordem de preferência definida.
- `app/scraping/completion.py`: `complete_abstracts` (máx. 5 por busca, falhas silenciosas, tempo total limitado).
- Integração em `SearchService` (só com `SCRAPING_ENABLED=true`; raspador único por serviço e `aclose()`).
- Fixtures HTML (`tests/fixtures/html/`), `scripts/measure_scraping.py` e 43 testes.

## Decisões tomadas
- Biblioteca de HTML: **`beautifulsoup4`** (com `html.parser`), em vez de `selectolax`: sem extensão compilada, instalação simples no Windows. É a segunda adição permitida fora da seção 4 (a primeira foi `pyyaml`).
- Entre vários `citation_abstract` ou `DC.description` (idiomas), vale o mais longo.
- Redirecionamentos são tratados à mão para que o destino também passe por `robots.txt`.
- `robots.txt` com 4xx = permitido; 5xx/erro de rede/outros = proibido (prudência).

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`ruff`, `mypy` e os 43 testes da OS passam.

## Critérios de aceite
- [x] Com `SCRAPING_ENABLED=false` nenhuma chamada de raspagem acontece — `test_scraping_disabled_makes_no_call`
- [x] Páginas bloqueadas por `robots.txt` não são requisitadas — `test_disallow_all_never_requests_the_page` e afins
- [x] A pausa por domínio é respeitada (relógio simulado) — `test_minimum_pause_per_domain_is_respected`
- [x] Extração segue a ordem de preferência — `test_order_of_preference_dc_over_og_and_jsonld`
- [x] Nenhuma raspagem em registro que já tem resumo — `test_only_records_without_abstract_are_scraped`

## Evidência para o TCC
`docs/evidencias/os-013-raspagem.md`. **Pendente (desenvolvedor):** rodar `scripts/measure_scraping.py` numa busca real; nenhum número foi escrito sem essa medição.
