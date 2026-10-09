# Relatório da OS-023 — Filtros (ano, tipo, fontes e ordenação)

**Data:** 2026-10-09

## O que foi feito
- `frontend/js/filters.js`: painel de filtros com ano inicial e final, tipos (caixas), fontes (caixas montadas a partir de `/api/v1/sources`; as indisponíveis ficam desabilitadas, com o motivo) e ordenação (Relevância / Mais recentes); botões "Aplicar" e "Limpar"; filtros ativos como etiquetas removíveis; contagem no botão ("Filtros (3)").
- `frontend/js/labels.js` (rótulos compartilhados) e integração em `search.js`: aplicar volta à página 1, atualiza a URL e a requisição; o painel espelha a consulta em exibição (link compartilhado, voltar do navegador).
- `frontend/index.html`: painel acessível (botão com `aria-expanded`/`aria-controls`, `fieldset`/`legend`), aviso sobre registros sem ano.
- 16 testes e2e novos (`tests/e2e/test_filters.py`).

## Decisões tomadas
- O painel é uma **seção recolhível** (botão + região), mais simples e acessível que um `<dialog>`; fecha ao aplicar e o foco vai ao título dos resultados.
- Validação no navegador: anos inteiros entre 1900 e (ano atual + 1) e `ano inicial ≤ ano final`; mensagem em `#erro-anos`, ligada aos dois campos por `aria-describedby` e `aria-invalid`; nada é enviado enquanto houver erro.
- Enter em qualquer campo do painel envia a busca já com os filtros.
- Nenhum filtro além de ano, tipo, fonte e ordenação (idioma não está no TCC).

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde; a suíte e2e passou com 55 testes. Ao incluir o botão "Filtros" na ordem de Tab, atualizei o teste de teclado da OS-022.

## Critérios de aceite
- [x] Filtros refletem na URL e na requisição — `test_apply_filters_goes_to_url_request_and_active_tags`
- [x] `year_from > year_to` bloqueia o envio com mensagem acessível — `test_invalid_year_range_blocks_submission_with_accessible_message`
- [x] "Limpar" remove tudo e refaz a busca — `test_clear_removes_everything_and_repeats_the_search`
- [x] Utilizável só com teclado, em celular e em computador — `test_keyboard_only_flow`, `test_open_panel_has_no_horizontal_scroll`, `test_touch_targets_in_the_panel`

## Evidência para o TCC
As capturas "filtros abertos" e "filtros ativos" saem da OS-032 (`scripts/capture_screens.py`). Uma prévia visual do painel foi conferida a 360 px e 1280 px.
