# Relatório da OS-021 — Base do frontend

**Data:** 2026-10-09

## O que foi feito
- `frontend/css/`: `tokens.css` (cores com contraste conferido), `base.css`, `layout.css` (móvel primeiro; ajustes em 37,5rem e 60rem), `components.css` (botões, campos, cartões, avisos, selos, esqueleto de carregamento).
- `frontend/js/`: `dom.js` (`el`, `clear`, `announce`), `api.js` (cliente com formato de erro 6.5, tempo limite e tratamento de 401), `state.js` (token em memória/`sessionStorage`), `a11y.js`, `shell.js` (cabeçalho, menu acessível, rodapé, região `aria-live`) e `main.js`.
- `frontend/index.html` provisório (a OS-022 o preenche).
- `scripts/contrast_check.py`: calcula as razões de contraste dos tokens e grava a tabela em `docs/ACESSIBILIDADE.md`.
- `tests/e2e/`: servidor real em thread + Chromium (Playwright); 14 testes.

## Decisões tomadas
Em `docs/DECISOES.md`: token fora do `localStorage`, fontes do sistema, par de foco, loops de eventos nos testes e2e.
Sem CDN, sem `innerHTML` e sem `style`/`script` embutidos (a CSP da OS-014 não bloqueia nada: o teste de console/CSP passa).

## Defeitos encontrados e corrigidos pelos testes
- O botão "Menu" ficava visível em telas largas: o `display` de `.btn` (carregado depois) vencia o `display:none` do layout. Corrigido com `.btn.nav-toggle`.
- Um teste meu injetava `<style>`; a própria CSP o bloqueou (prova de que ela funciona). O teste passou a usar o CSSOM.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde. `uv run python scripts/contrast_check.py`: todos os pares conferidos passam.

## Critérios de aceite
- [x] Página provisória abre sem erro de console — `test_home_opens_without_console_or_csp_errors`
- [x] Sem rolagem horizontal em 320 px (e com texto a 200%) — `test_no_horizontal_scroll`, `test_no_horizontal_scroll_with_200_percent_zoom`
- [x] Tab percorre o cabeçalho na ordem lógica e o foco é visível — `test_keyboard_order_and_visible_focus_on_desktop`
- [x] Tabela de contraste calculada por script em `docs/ACESSIBILIDADE.md` — `scripts/contrast_check.py`
- [x] CSP da OS-014 não bloqueia nada — mesmo teste do console

## Evidência para o TCC
Capturas do esqueleto em 3 larguras (`docs/evidencias/os-021/`) e a tabela de contraste (`docs/ACESSIBILIDADE.md`).
