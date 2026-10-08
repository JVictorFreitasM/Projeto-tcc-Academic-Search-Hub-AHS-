# Relatório da OS-001 — Repositório, ambiente e ferramentas de qualidade

**Data:** 2026-10-08

## O que foi feito
Criado `academic-search-hub/` (dentro de `projeto tcc/`) com a árvore da seção 5.3, `pyproject.toml` (ruff, mypy estrito em `app/`, pytest com cobertura), `.gitignore`, `.env.example` (todas as variáveis de 5.4), `README.md` mínimo, `tasks.py`, `docs/DECISOES.md`, modelo de relatório e teste de fumaça. `git init` no próprio projeto.

## Decisões tomadas
- `tasks.py` no lugar do `Makefile` (sem `make` no Windows).
- `uv` como gerenciador; `requirements.lock` exportado por `uv export` (e `uv.lock` versionado).
- `semgrep` não foi instalado agora (a seção 4 diz "se disponível"; tratar na OS-029).
- `PyYAML` não adicionado (fora da seção 4); a decidir na OS-005. Registrado em `docs/DECISOES.md`.

## Desvios em relação à OS
- `make install`/`make check` viram `python tasks.py install`/`check`.
- O repositório git foi criado em `academic-search-hub/`, que fica dentro de um repositório git maior (a pasta do usuário). Os dois são independentes.

## Comandos executados e resultados
`python tasks.py install` — ok. `python tasks.py check` — ruff, ruff format, mypy (11 arquivos) e pytest (1 passou) sem erros. Saída completa em `docs/evidencias/os-001.txt`.

## Critérios de aceite
- [x] install cria o ambiente do zero — `uv sync` + lock gerado
- [x] check passa — ver evidência
- [x] `.env` ignorado (`git check-ignore .env` → `.env`) e `.env.example` sem segredo
- [x] árvore confere com 5.3 — lista em `docs/evidencias/os-001.txt` (`tree` do Windows não separa ignorados; usei `git ls-files`)
- [x] `docs/DECISOES.md` e modelo de relatório existem

## Evidência para o TCC
`docs/evidencias/os-001.txt`.
