# OS-031 — Verificação de acessibilidade (WCAG 2.1)

## O que foi feito

- `tests/a11y/test_axe.py`: axe-core (pacote `axe-playwright-python`, adicionado como dependência de
  desenvolvimento) percorre 16 telas e estados em duas larguras (360 e 1280 px) = 32 execuções;
  falha em violações `serious` e `critical`. Inclui um teste de sanidade que injeta três defeitos
  conhecidos e exige que o axe os detecte.
- `tests/a11y/conftest.py`: reaproveita servidor local e navegador de `tests/e2e`.
- `docs/ACESSIBILIDADE.md`: seção do axe, checklist dos 16 critérios pedidos, testes manuais M1 a M5
  e "Limites da avaliação".
- `python tasks.py test-a11y`; saída do axe em `docs/evidencias/os-031-axe.txt`.

## Resultado medido

- 32 casos de varredura + 1 teste de sanidade: todos passam. O axe não reportou violação de nenhum
  impacto (nem `minor`/`moderate`) nos estados varridos.
- Correções no frontend: nenhuma foi necessária.

## Checklist manual

- Marcados "Atende" com método descrito: 1.1.1, 1.3.1, 1.4.1, 1.4.3, 2.4.1, 2.4.7, 3.1.1, 3.3.1, 3.3.2,
  4.1.2. Parciais (parte automática verificada, parte humana pendente): 1.4.4, 1.4.10.
- `PENDENTE (desenvolvedor)`: 2.1.1, 2.1.2, 2.4.3, 4.1.3 e os testes manuais M1 a M5 (teclado,
  leitor de tela, zoom 200% e 400%, alto contraste).

## Limites

Ferramenta automática cobre só parte dos problemas; um navegador, dados fictícios, duas larguras. O
documento não afirma conformidade WCAG 2.1 AA; usa "atende aos critérios verificados".
