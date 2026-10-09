# Relatório da OS-025 — Favoritos, histórico e exportação na interface

**Data:** 2026-10-09

## O que foi feito
- **Busca:** botão de favorito em cada cartão (`aria-pressed`, rótulos "Salvar nos favoritos" / "Remover dos favoritos"); visitante vê o link "Entre para salvar", que leva ao login mantendo a busca (`?voltar=`). Caixa "Selecionar para exportar" por resultado (seleção vale entre páginas, até 100), barra com formato (BibTeX, RIS, JSON, CSV) e "Exportar selecionados".
- **`favoritos.html` + `js/favorites.js`:** lista paginada (10 por página) com busca textual, anotação com contador de 1000, remoção com confirmação em `<dialog>`, estado vazio amigável, "Exportar todos" e, na mesma página, o **histórico** (repetir busca com os mesmos filtros, remover item, limpar tudo com confirmação).
- **Módulos novos:** `record-view.js` (peças do cartão, compartilhadas), `favorite-button.js`, `export.js` (download por `Blob` e `<a download>`, sem `innerHTML`), `dialog.js` (diálogo acessível: foco inicial na opção segura, Esc cancela, foco volta a quem abriu).
- 23 testes e2e novos (`tests/e2e/test_favorites_ui.py`) sobre uma API simulada com estado (`tests/e2e/fake_api.py`).

## Decisões tomadas
- Histórico na própria `favoritos.html` (a OS permitia escolher uma).
- Para remover da busca um favorito que veio marcado (`is_favorite=true`) sem o id conhecido, a interface usa `POST /favorites`, que é idempotente e devolve o existente, e depois `DELETE`.
- O visitante recebe um **link** (não um botão desabilitado): leva ao login sem perder a busca. Isso substituiu o botão `aria-disabled` da OS-022.
- A exportação de resultados não envia o token (não exige login); a de favoritos envia.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde; a suíte e2e passou. Conferência visual da página de favoritos e histórico.

## Critérios de aceite
- [x] Salvar, anotar, remover e exportar funcionam de ponta a ponta (API simulada) — `test_toggle_favorite_from_the_results`, `test_edit_note_with_counter`, `test_remove_asks_for_confirmation`, `test_export_all_favorites_downloads_with_auth`
- [x] Exportação baixa arquivo com nome e extensão corretos — `test_all_four_formats_download_with_the_right_extension`, `test_select_results_and_export_selected`
- [x] Remover favorito pede confirmação — `test_remove_asks_for_confirmation` (Cancelar, Esc e Remover)
- [x] Repetir busca do histórico refaz a consulta com os mesmos filtros — `test_repeat_search_goes_back_to_the_search_page_with_same_filters`

## Evidência para o TCC
As capturas "favoritos", "anotação", "seleção para exportar" e "arquivo exportado" saem da OS-032. Os arquivos de exemplo já estão em `docs/evidencias/os-019/`.
