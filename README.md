# academic-search-hub

Aplicação web para busca unificada de trabalhos acadêmicos em repositórios de acesso aberto
(CORE, SciELO, OpenAlex, BDTD, UFPI e UESPI). Projeto do TCC de João Victor de Freitas Martins
(UESPI, Tecnólogo em Sistemas para a Internet).

> Versão mínima. A versão final deste documento vem na OS-034.

## Pré-requisitos

- Python 3.11 ou superior
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL 14 ou superior (a partir da OS-003)

## Comandos

Não há `make` no Windows; os mesmos alvos estão em `tasks.py`:

| Comando | O que faz |
|---|---|
| `python tasks.py install` | cria o `.venv`, instala as dependências e gera o `requirements.lock` |
| `python tasks.py lint` | `ruff check` e `ruff format --check` |
| `python tasks.py format` | corrige e formata com `ruff` |
| `python tasks.py typecheck` | `mypy` (modo estrito em `app/`) |
| `python tasks.py test` | `pytest` com cobertura |
| `python tasks.py run` | sobe o servidor de desenvolvimento |
| `python tasks.py check` | lint + typecheck + test |

Copie `.env.example` para `.env` e preencha os valores. Nunca commite o `.env`.
