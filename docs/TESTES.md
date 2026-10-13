# Testes

Todos os comandos usam `python tasks.py <alvo>` (não há `make` no Windows).

## Como rodar

| Alvo | O que roda |
|---|---|
| `python tasks.py check` | `ruff`, `ruff format --check`, `mypy` (estrito) e toda a suíte com cobertura (limiar 80%) |
| `python tasks.py test` | toda a suíte, com cobertura e o limiar de 80% de linhas em `app/` |
| `python tasks.py test-unit` | só `unit` (sem banco, sem navegador) |
| `python tasks.py test-integration` | só `integration` (PostgreSQL de teste) |
| `python tasks.py test-contract` | só `contract` (fixtures dos conectores) |
| `python tasks.py test-e2e` | `e2e` e `a11y` (Chromium via Playwright) |
| `python tasks.py test-a11y` | só `a11y` (axe; regrava `docs/evidencias/os-031-axe.txt`) |
| `python tasks.py test-stats` | conta testes por marcador e resume a cobertura (grava `docs/evidencias/os-030-cobertura.txt`) |
| `STRICT_FIXTURES=1 uv run pytest tests/contract` | lista as fixtures sintéticas ainda não trocadas por respostas reais |

## Marcadores (um por pasta; atribuído automaticamente por `tests/conftest.py`)

| Marcador | Pasta | Precisa de | O que cobre |
|---|---|---|---|
| `unit` | `tests/unit/` | nada | funções puras, conectores com `respx`, serviços com dados falsos, varreduras de código |
| `integration` | `tests/integration/` | PostgreSQL de teste (`TEST_DATABASE_URL`) | modelos, migrações, colheita, API HTTP com banco, segurança (OWASP) |
| `contract` | `tests/contract/` | nada | cada fixture de fonte produz `RecordOut`/linhas válidas |
| `e2e` | `tests/e2e/` | Chromium (`playwright install chromium`) | telas no navegador, com a API simulada por interceptação de rede |
| `a11y` | `tests/a11y/` | Chromium | verificação com axe (OS-031) |

Sem `TEST_DATABASE_URL`, os testes `integration` são **pulados** (não falham).

## Banco de teste

Crie o banco `academic_search_test` e as extensões (ver `docs/EXECUCAO.md`) e defina
`TEST_DATABASE_URL` no `.env`. O banco é recriado do zero a cada execução (`alembic downgrade
base` + `upgrade head`). **Não** aponte para um banco com dados que importam.

## Nenhum teste usa a internet

`tests/conftest.py` bloqueia (fixture automática de sessão) toda conexão e resolução de nome para
endereços que não sejam o próprio computador. Só o banco local e o servidor de teste do Playwright
passam. Os conectores são testados com fixtures e `respx`. Quem tentar a rede recebe
`NetworkBlockedError`. O teste `test_httpx_to_an_external_host_is_blocked` prova o bloqueio com um
`httpx` real. (O navegador do Playwright é outro processo e só acessa o servidor local, porque as
chamadas à API são interceptadas.)

## Fixtures sintéticas

Enquanto o desenvolvedor não grava respostas reais (passo manual das OS-007 a OS-010), os conectores
usam fixtures **sintéticas**, marcadas (`"_synthetic": true` nos JSON; comentário `SINTÉTICA` nos
XML). O teste de contrato garante que toda fixture sintética esteja marcada, e `STRICT_FIXTURES=1`
faz a suíte falhar listando as que faltam trocar.

## O que é manual (a suíte não cobre)

- validação com chaves reais (OpenAlex, CORE) e com as fontes OAI reais;
- importação dos `.bib`/`.ris` no Zotero ou Mendeley;
- leitor de tela, teclado em todas as telas, zoom de 200% e 400% (OS-031);
- medição manual de tempo de busca (OS-033) e teste de usabilidade (OS-036);
- restauração de backup e verificação da implantação (OS-037).

## Cobertura

Medida com `pytest-cov` sobre `app/` (linhas). O limiar de **80%** só foi ligado depois de medir:
o valor medido está em `docs/evidencias/os-030-cobertura.txt`, gerado por
`python tasks.py test-stats` (os números vêm do `coverage.xml` da última execução).
