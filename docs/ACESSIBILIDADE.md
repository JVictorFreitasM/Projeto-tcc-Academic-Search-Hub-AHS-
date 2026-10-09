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
