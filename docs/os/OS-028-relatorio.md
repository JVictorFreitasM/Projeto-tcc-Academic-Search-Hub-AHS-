# Relatório da OS-028 — Análise estática com mais de uma ferramenta

**Data:** 2026-10-09

## O que foi feito
- `scripts/run_sast.py` (alvo `python tasks.py sast`): roda bandit, pip-audit, semgrep (se encontrado) e ruff com as regras `S` (`--ignore-noqa`), grava as saídas brutas em `docs/evidencias/sast/` com data e versão de cada ferramenta (`versoes.json`). Se o semgrep não for encontrado, diz isso explicitamente e **não** simula.
- `scripts/sast_summary.py` (+ 6 testes): lê as saídas e **calcula** achados por ferramenta e sobreposição por arquivo+linha; grava `RESUMO.md`.
- Triagem e quadro comparativo em `docs/SEGURANCA.md#analise-estatica`.
- Saídas "antes das correções" (commit `d91f62c`) em `docs/evidencias/sast/antes-das-correcoes/`.

## Resultados (09/10/2026)
- **bandit 1.9.4:** 8 achados de severidade baixa (6 × B101 `assert`, 2 × B105).
- **ruff-S 0.16.10:** 9 achados (os mesmos 8 do bandit + S105 em `token_type = "bearer"`).
- **semgrep 1.180.0:** 0 achados (223 regras `p/python` + `p/owasp-top-ten`, 101 arquivos).
- **pip-audit 2.10.1:** 0 vulnerabilidades em 86 dependências.

## Decisões tomadas
- O semgrep rodou em ambiente isolado (`uv venv` em pasta temporária), não como dependência do projeto; o script o localiza por `SEMGREP_BIN` ou pelo PATH.
- O `ruff` com `S` entrou como **quarta** ferramenta (não como substituta do semgrep).
- As justificativas dos falsos positivos ficam **escritas ao lado** do `# nosec`, como a OS exige.
- Para o quadro comparativo ter sentido, as ferramentas foram rodadas também sobre o código anterior às correções.

## Correções feitas
Os 6 `assert` de estreitamento de tipo viraram verificações explícitas (`app/core/errors.py`, `app/core/rate_limit.py`, `app/harvest/harvester.py`); testes dessas áreas continuam passando.

## Desvios em relação à OS
O alvo é `python tasks.py sast` (não `make sast`, que não existe no Windows).

## Critérios de aceite
- [x] As saídas brutas existem e têm data e versão da ferramenta — `docs/evidencias/sast/*.json` e `versoes.json`
- [x] Nenhum achado alto/médio sem decisão — não houve achado alto nem médio; os 8 baixos têm decisão na tabela
- [x] O quadro comparativo é gerado por `scripts/sast_summary.py` — `RESUMO.md` (antes e depois)
- [x] `pip-audit` sem vulnerabilidade conhecida

## Evidência para o TCC
O quadro comparativo e a tabela de triagem (seção 4.6). As quatro ferramentas rodaram; o TCC deve citar as versões e a data.
