# Acessibilidade

> Documento vivo. A OS-021 registra as decisões de base e o contraste; a OS-031 acrescenta o
> checklist WCAG 2.1 e os resultados do axe, e **nunca** afirma "conformidade WCAG 2.1 AA": usa a
> expressão "atende aos critérios verificados", listando-os.

## Decisões de base (OS-021)

- HTML semântico: `<html lang="pt-BR">`, um `<h1>` por página, pontos de referência (`header`,
  `nav`, `main`, `footer`), link "Pular para o conteúdo" como primeiro item da ordem de Tab.
- Foco visível em todos os elementos interativos: anel de 3 px (`--focus-width`) com afastamento de
  2 px, em cor com contraste mínimo de 3:1 sobre o fundo (tabela abaixo).
- Menu de navegação por teclado: botão "Menu" com `aria-expanded` e `aria-controls` no celular;
  `Esc` fecha e devolve o foco ao botão. Em telas de 600 px ou mais o menu fica sempre visível.
- Alvos de toque de pelo menos 44×44 px (`--touch-min`). WCAG 2.5.5 é nível AAA; adotado como boa
  prática.
- Tamanhos em `rem`; sem rolagem horizontal a 320 px nem com texto a 200% (testes e2e).
- `prefers-reduced-motion` respeitado; links sempre sublinhados e avisos sempre com texto, para a
  cor nunca ser o único sinal (1.4.1).
- Sem tema escuro (fora do escopo).
- Região `aria-live` (`#announcer`) para anunciar estados (busca em andamento, erros, resultados).
## Contraste das cores (calculado por `scripts/contrast_check.py`)

<!-- contraste:inicio -->
| Primeiro plano | Fundo | Razão calculada | Mínimo | Resultado | Uso |
|---|---|---|---|---|---|
| `--color-text` #1a1f26 | `--color-bg` #ffffff | 16.56:1 | 4.5:1 | passa | texto comum sobre o fundo |
| `--color-text` #1a1f26 | `--color-surface` #f3f5f8 | 15.16:1 | 4.5:1 | passa | texto comum sobre superfícies |
| `--color-text-muted` #475161 | `--color-bg` #ffffff | 8.02:1 | 4.5:1 | passa | texto secundário sobre o fundo |
| `--color-text-muted` #475161 | `--color-surface` #f3f5f8 | 7.35:1 | 4.5:1 | passa | texto secundário sobre superfícies |
| `--color-primary` #1d4ed8 | `--color-bg` #ffffff | 6.70:1 | 4.5:1 | passa | links e texto na cor primária |
| `--color-primary` #1d4ed8 | `--color-surface` #f3f5f8 | 6.14:1 | 4.5:1 | passa | links sobre superfícies |
| `--color-on-primary` #ffffff | `--color-primary` #1d4ed8 | 6.70:1 | 4.5:1 | passa | texto de botão primário |
| `--color-on-primary` #ffffff | `--color-primary-hover` #1e3a8a | 10.36:1 | 4.5:1 | passa | botão primário em foco/hover |
| `--color-danger` #b42318 | `--color-bg` #ffffff | 6.57:1 | 4.5:1 | passa | mensagens de erro |
| `--color-danger` #b42318 | `--color-danger-bg` #fef3f2 | 6.05:1 | 4.5:1 | passa | erro sobre aviso de erro |
| `--color-success` #067647 | `--color-bg` #ffffff | 5.69:1 | 4.5:1 | passa | mensagens de sucesso |
| `--color-success` #067647 | `--color-success-bg` #ecfdf3 | 5.40:1 | 4.5:1 | passa | sucesso sobre aviso de sucesso |
| `--color-warning-text` #7a4b00 | `--color-warning-bg` #fff4d6 | 6.76:1 | 4.5:1 | passa | texto de aviso |
| `--color-info-text` #1e3a8a | `--color-info-bg` #e8efff | 8.99:1 | 4.5:1 | passa | texto informativo |
| `--color-badge-text` #1e3a8a | `--color-badge-bg` #e8efff | 8.99:1 | 4.5:1 | passa | selos de fonte e tipo |
| `--color-border-strong` #6b7685 | `--color-bg` #ffffff | 4.61:1 | 3:1 | passa | borda de campos e botões |
| `--color-border-strong` #6b7685 | `--color-surface` #f3f5f8 | 4.22:1 | 3:1 | passa | borda de campos sobre superfícies |
| `--color-focus` #b45309 | `--color-bg` #ffffff | 5.02:1 | 3:1 | passa | anel de foco sobre o fundo |
| `--color-focus` #b45309 | `--color-surface` #f3f5f8 | 4.60:1 | 3:1 | passa | anel de foco sobre superfícies |
<!-- contraste:fim -->

## Verificação automática com axe (OS-031)

- Ferramenta: axe-core, pelo pacote `axe-playwright-python`, no Chromium (Playwright). Teste:
  `tests/a11y/test_axe.py`; rodar com `python tasks.py test-a11y`.
- Cobertura: 16 telas e estados × 2 larguras (celular 360 px e computador 1280 px) = 32 execuções.
  Estados: busca vazia, com resultados, sem resultados, com erro parcial de fonte, filtros abertos,
  filtros ativos, seleção para exportar, favoritos (com itens e vazio), diálogo de remover favorito,
  entrar, entrar com erros de validação, criar conta, minha conta, diálogo de excluir conta e
  política de privacidade.
- Regra do teste: falha em violação de impacto `serious` ou `critical`; `minor` e `moderate` são
  registradas, sem reprovar.
- Resultado medido na última execução: nenhuma violação, de qualquer impacto, nos 32 casos. A saída
  fica em `docs/evidencias/os-031-axe.txt` (regerada a cada execução do teste).
- Sanidade do instrumento: um teste injeta uma imagem sem texto alternativo, um campo sem rótulo e
  um botão sem nome, e exige que o axe aponte as três falhas. Assim "zero violações" não vem de um
  axe que não detecta nada.
- A API simulada nos testes devolve dados fictícios; as telas reais com dados das fontes não foram
  varridas pelo axe.

## Checklist por critério WCAG 2.1

Legenda: **Atende** = verificado como descrito na observação; **PENDENTE (desenvolvedor)** = depende
de teste humano que a IA não pode simular. Nenhum critério foi marcado "Atende" sem o método de
verificação indicado.

| Critério | Resultado | Observação (como foi verificado) |
|---|---|---|
| 1.1.1 Conteúdo não textual | Atende | O frontend não tem `<img>` nem `<svg>`; ícones não existem (só texto). Regras de alternativa textual do axe sem violações nos 32 casos. |
| 1.3.1 Informações e relações | Atende | Axe sem violações (rótulos, landmarks, listas, tabelas, ordem de títulos); cada campo tem `<label>` ou `aria-describedby`; um `<h1>` por página (OS-021). |
| 1.4.1 Uso de cor | Atende | Links sublinhados (`base.css`, `layout.css`, `components.css`); avisos e erros têm prefixo textual ("Aviso:"), conferido nos testes e2e do erro parcial. |
| 1.4.3 Contraste mínimo | Atende | Razões calculadas por `scripts/contrast_check.py` (tabela acima, todas ≥ 4,5:1 para texto) e regra `color-contrast` do axe sem violações nos 32 casos. O axe não avalia texto sobre imagem ou gradiente; não há nenhum no frontend. |
| 1.4.4 Redimensionar texto | Atende (parcial) | Teste e2e: texto a 200% sem rolagem horizontal (`test_no_horizontal_scroll_with_200_percent_zoom`). Zoom do navegador real a 200%: PENDENTE (desenvolvedor). |
| 1.4.10 Reflow | Atende (parcial) | Teste e2e: sem rolagem horizontal a 320 px, 768 px e 1280 px. Zoom de 400% no navegador real: PENDENTE (desenvolvedor). |
| 2.1.1 Teclado | PENDENTE (desenvolvedor) | Os testes e2e usam teclado em partes (menu com Esc, diálogos, link de pular). Percorrer todas as telas só com teclado é teste manual. |
| 2.1.2 Sem armadilha de teclado | PENDENTE (desenvolvedor) | Diálogos prendem o foco de propósito e devolvem o foco ao fechar com Esc ou Cancelar (e2e). Ausência de armadilha em todas as telas depende do teste manual. |
| 2.4.1 Ignorar blocos | Atende | Primeiro item da ordem de Tab é "Pular para o conteúdo" e leva o foco ao `<main>` (testes e2e `test_skip_link_moves_focus_to_main`). |
| 2.4.3 Ordem do foco | PENDENTE (desenvolvedor) | A ordem do link de pular, marca e busca é testada; o foco volta ao botão de origem ao fechar diálogo (e2e). A ordem lógica em todas as telas depende do teste manual. |
| 2.4.7 Foco visível | Atende | Teste e2e mede o contorno do foco (sólido, ≥ 3 px) e o contraste do anel está na tabela acima (≥ 3:1). Visibilidade em modo de alto contraste do sistema: PENDENTE (desenvolvedor). |
| 3.1.1 Idioma da página | Atende | `<html lang="pt-BR">` nas quatro páginas; regra `html-has-lang` do axe sem violações. |
| 3.3.1 Identificação do erro | Atende | Erros de campo aparecem como texto, com `aria-invalid="true"` e `aria-describedby` (estado "entrar com erros de validação" varrido pelo axe e testado no e2e). |
| 3.3.2 Rótulos ou instruções | Atende | Todos os campos têm rótulo visível; regras de senha e ajuda da busca ligadas por `aria-describedby`; axe sem violações de rótulo. |
| 4.1.2 Nome, função, valor | Atende | Regras ARIA do axe sem violações; botões alternáveis usam `aria-expanded`/`aria-pressed`; diálogos são `<dialog>` modais (`showModal()`) com nome por `aria-labelledby`. Anúncio real por leitor de tela: PENDENTE (desenvolvedor). |
| 4.1.3 Mensagens de status | PENDENTE (desenvolvedor) | Existem regiões `aria-live` (`#announcer`, contagens) e `role="alert"` nos erros; que o leitor de tela as anuncie no momento certo só se confirma com NVDA ou VoiceOver. |

Critérios fora da lista mínima (por exemplo 1.2.x de mídia temporizada) não se aplicam: o sistema não
tem áudio nem vídeo.

## Testes manuais para o desenvolvedor (a IA não os simula)

Anote o resultado em cada linha (data, navegador, o que observou). Enquanto estiverem em branco,
os critérios ligados a eles seguem como PENDENTE.

| # | Teste | Como fazer | Resultado |
|---|---|---|---|
| M1 | Só teclado, todas as telas | Sem mouse, percorrer busca, resultados, filtros, favoritos, conta e política: Tab, Shift+Tab, Enter, Espaço, Esc. Conferir foco sempre visível, ordem lógica, nenhum ponto sem saída. | PENDENTE (desenvolvedor) |
| M2 | Leitor de tela | NVDA (Windows) ou VoiceOver (macOS): fazer uma busca, ouvir resultados e avisos (erro parcial), favoritar, abrir e fechar um diálogo, errar um campo no cadastro. | PENDENTE (desenvolvedor) |
| M3 | Zoom 200% | Ampliar o navegador a 200% em cada tela; nada cortado, sem rolagem horizontal. | PENDENTE (desenvolvedor) |
| M4 | Zoom 400% | Idem a 400% (equivale a 320 px de largura); rolagem só vertical. | PENDENTE (desenvolvedor) |
| M5 | Alto contraste | Ativar o modo de alto contraste do Windows; conferir bordas, foco e botões. | PENDENTE (desenvolvedor) |

## Correções feitas nesta OS

Nenhuma. O axe não encontrou violações nas telas e estados varridos, então nenhum código do
frontend precisou ser alterado. Isso não significa que não haja problemas: ver os limites abaixo.

## Limites da avaliação

- Ferramentas automáticas detectam apenas parte dos problemas de acessibilidade; as regras do axe
  cobrem o que pode ser decidido por código (atributos, contraste calculado, estrutura). Não
  avaliam se um texto alternativo é bom, se a ordem de leitura faz sentido, se uma mensagem é
  compreensível ou se o fluxo é usável por quem depende de tecnologia assistiva. Esse limite é
  discutido por Nagaraju, Chawla e Rana (2019) como desafio prático de avaliar acessibilidade.
- A varredura cobre os estados listados, em duas larguras, num só navegador (Chromium), com dados
  fictícios. Outros navegadores, outras larguras e conteúdo real das fontes não foram verificados.
- O checklist manual cobre os 16 critérios pedidos; não é uma auditoria completa de todos os
  critérios A e AA.
- Por isso este documento não afirma conformidade com a WCAG 2.1 AA. O que se afirma é que o sistema
  **atende aos critérios verificados**, os marcados "Atende" acima, pelos métodos descritos em cada
  linha, e que os itens PENDENTE (desenvolvedor) ainda não foram verificados.
