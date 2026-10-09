# Relatório da OS-022 — Tela de busca e resultados

**Data:** 2026-10-09

## O que foi feito
- `frontend/index.html`: formulário `role="search"` com rótulo visível, ajuda sobre aspas e `-termo`, e áreas de resultados, paginação e estado das fontes.
- `frontend/js/search.js`: consulta a `GET /api/v1/search`, cartões de resultado (título com link seguro, autores até 5 e "e mais N", ano, tipo, idioma, selos de fonte com nome, resumo com "Ler mais"/"Ler menos", PDF), estados (carregando com esqueleto e anúncio, vazio, erro total com estado por fonte, erro parcial), resumo "Cerca de N resultados (estimativa)", paginação e botão de favorito.
- `frontend/js/query.js`: leitura e escrita dos parâmetros da URL (`q`, `page` e os filtros da OS-023), validação da consulta.
- URL por `history.pushState`: voltar do navegador restaura a busca; link compartilhado executa a busca; nova busca cancela a anterior.
- 21 testes e2e (`tests/e2e/test_search_page.py`), com a API simulada por interceptação de rede.

## Decisões tomadas
- Todo texto da API entra por `textContent`; links só viram `<a>` se forem `http`/`https` (defesa em profundidade além da validação do servidor).
- O botão de favorito aparece **desabilitado** ("Entre para salvar", `aria-disabled="true"`) até a OS-025 ligá-lo à sessão; não há tela de login falsa.
- A consulta curta (menos de 2 caracteres) é barrada no navegador, com mensagem ligada ao campo (`aria-describedby`, `aria-invalid`) e sem requisição.
- Fontes desabilitadas ("Fonte ainda não colhida") aparecem como nota discreta, não como alerta.
- Erro 429 mostra "Muitas buscas em pouco tempo..."; erro de rede e de tempo limite têm mensagens próprias.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde.

## Critérios de aceite
- [x] Busca com resposta simulada renderiza os cartões — `test_results_are_rendered_as_cards`
- [x] Erro parcial mostra o aviso com as fontes que falharam — `test_partial_failure_shows_warning_listing_failed_sources`
- [x] Resultados vêm de `textContent`; título com `<img onerror>` não executa — `test_malicious_title_is_shown_as_text_and_never_executed`
- [x] Voltar do navegador restaura a busca anterior — `test_browser_back_restores_previous_search`
- [x] Foco e leitura por teclado — `test_enter_key_submits_and_keyboard_reaches_results`, `test_pagination_updates_request_url_and_focus` (a leitura real com leitor de tela é passo manual da OS-031)

## Evidência para o TCC
As capturas "busca vazia", "resultados", "erro parcial" e "sem resultados" são geradas por script na OS-032 (`scripts/capture_screens.py`); uma prévia visual foi conferida nesta OS.
