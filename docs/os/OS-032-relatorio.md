# OS-032 — Testes de ponta a ponta e capturas para o TCC

## O que foi feito

- `tests/e2e/test_flows.py`: cinco fluxos no Chromium contra a aplicação **real** (servidor local, API
  sem interceptação, PostgreSQL de teste) com **conectores falsos** de dados fixos e fictícios
  (dois conectores, uma duplicata por DOI para exercitar a fusão):
  (a) visitante busca e exporta resultados (CSV lido do arquivo baixado);
  (b) cadastro, login, busca, favorita, anota (a anotação sobrevive a recarregar a página, vinda do
  banco) e exporta favoritos;
  (c) filtros de ano e tipo reduzem os resultados e aparecem na URL;
  (d) histórico gravado em segundo plano e "Repetir a busca";
  (e) baixar dados, excluir conta e confirmar que o login falha.
- `scripts/capture_screens.py`: gera 16 telas em duas larguras (computador 1280 px, celular 390 px)
  = 32 PNGs em `docs/evidencias/telas/`, com nomes `4.1-NN-<tela>-<largura>.png`, e o `INDICE.md`.
  Usa dados de demonstração (todo título começa com `[DEMONSTRAÇÃO]`; e-mail em `example.org`).
- `docs/evidencias/telas/INDICE.md` (gerado) mapeia cada captura à seção 4.1 do TCC;
  `ROTEIRO_REAIS.md` descreve as capturas com dados reais (passo do desenvolvedor).
- `tests/unit/test_capture_screens_plan.py`: lista de telas completa e na ordem, nomes únicos,
  dados de demonstração marcados.

## Defeito encontrado e corrigido

O fluxo (d) falhava de forma intermitente. Causa, em `frontend/js/search.js`: ao terminar de carregar
as fontes, o código executava `ui.input.value = initial.q` e apagava o texto que a pessoa já tinha
digitado (quando a URL não trazia consulta). Numa conexão lenta, quem digita rápido perdia o texto.
Correção: só preencher o campo quando há consulta na URL. Teste de regressão em
`tests/e2e/test_search_page.py`: falha com o código antigo e passa com o novo (verificado).

## Verificação

- Os cinco fluxos passaram em três execuções seguidas (5 passed em cada).
- O script gerou as 32 capturas sem intervenção; conferi visualmente resultados, erro parcial,
  documentação da API e o diálogo de excluir conta (este passou a ser capturado só na janela visível,
  para o fundo escurecer por inteiro).
- A captura de `/api/docs` carrega o Swagger UI de uma CDN: precisa de internet.

## Pendências do desenvolvedor

- Capturas com dados reais das fontes (`ROTEIRO_REAIS.md`), com chave e e-mail reais removidos.
- Ajustar a subseção do TCC na coluna "Seção do TCC" do índice ao texto final.
