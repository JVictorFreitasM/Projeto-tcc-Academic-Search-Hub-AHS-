# Como executar o projeto

Do banco ao servidor, na ordem. A instalação resumida está no `README.md`; a implantação em
servidor (serviço, proxy reverso, colheita agendada e backup) está em `docs/IMPLANTACAO.md`.
Não é preciso Docker nem Redis.

Ordem: **1.** banco → **2.** `.env` → **3.** migrações → **4.** colheita das fontes OAI →
**5.** servidor.

## 1. Banco de dados (PostgreSQL 14 ou superior)

### 1.1 Passo único, feito por superusuário

Criar o usuário da aplicação (**sem** privilégio de superusuário), os bancos e as extensões:

```sql
CREATE USER app_user WITH PASSWORD 'troque-esta-senha';
CREATE DATABASE academic_search OWNER app_user;
CREATE DATABASE academic_search_test OWNER app_user;   -- só para testes de integração
\c academic_search
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- repetir as três extensões em academic_search_test
```

Com `createdb`: `createdb -O app_user academic_search`.

As três extensões são "confiáveis" a partir do PostgreSQL 13, de modo que o dono do banco consegue
criá-las pela migração `0001`; ainda assim, criá-las antes como superusuário evita surpresas.

### 1.2 Windows: loop de eventos

O `psycopg` assíncrono não funciona com o `ProactorEventLoop`, que é o padrão do Windows. O
`migrations/env.py`, o `tests/conftest.py` e o servidor (`python -m app.run`) já usam o
`SelectorEventLoop`. Por isso, no Windows, suba o servidor por `python tasks.py run` (ou
`python -m app.run`) e não direto pelo comando `uvicorn`.

## 2. Configuração (`.env`)

Copie `.env.example` para `.env` (nunca faça commit dele) e preencha. A tabela completa das
variáveis está no `README.md`. O mínimo:

```
SECRET_KEY=<32 caracteres ou mais, aleatórios>
DATABASE_URL=postgresql+psycopg://app_user:SENHA@127.0.0.1:5432/academic_search
TEST_DATABASE_URL=postgresql+psycopg://app_user:SENHA@127.0.0.1:5432/academic_search_test
OPENALEX_API_KEY=
CORE_API_KEY=
CONTACT_EMAIL=
```

- Gerar a chave: `uv run python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- Sem `TEST_DATABASE_URL`, os testes de integração e os de ponta a ponta com banco são **pulados**.
  O banco de teste é recriado do zero a cada execução (`alembic downgrade base` + `upgrade head`):
  **não** aponte para um banco com dados que importam.
- Sem `OPENALEX_API_KEY` e `CORE_API_KEY`, essas fontes aparecem como indisponíveis.
- `CONTACT_EMAIL` vai no `User-Agent` da colheita e da raspagem, para os administradores das fontes
  saberem com quem falar.

## 3. Migrações

```
uv run alembic upgrade head      # aplica
uv run alembic downgrade base    # desfaz tudo
uv run alembic current           # revisão atual
```

A migração `0001` cria as extensões, a função `immutable_unaccent(text)` e a configuração de busca
`pt_unaccent` (ver `docs/DECISOES.md`); a `0002` cria as tabelas e o gatilho do índice de texto.

## 4. Colheita das fontes OAI-PMH

As fontes SciELO, BDTD, UFPI e UESPI só respondem com o que foi colhido. Passo a passo:

1. Confirmar o endereço de cada fonte em `config/oai_sources.yml` (campos `TODO-VERIFICAR`):
   ```
   uv run python -m app.harvest.cli identify <fonte>
   uv run python -m app.harvest.cli sets <fonte>
   ```
2. Teste sem gravar: `uv run python -m app.harvest.cli run <fonte> --limit 50 --dry-run`
3. Habilitar (`enabled: true`) e colher:
   ```
   uv run python -m app.harvest.cli run <fonte>          # incremental
   uv run python -m app.harvest.cli run <fonte> --full   # ignora a última colheita
   uv run python -m app.harvest.cli run-all              # todas as habilitadas
   ```
4. Conferir: `uv run python -m app.harvest.cli status` (última colheita e total de registros por
   fonte).

Como a colheita funciona:

- É **incremental** por padrão: pede só o que mudou desde o início da última colheita com status
  `ok`. `--full` ignora isso.
- Respeita `OAI_HARVEST_DELAY_SECONDS` entre requisições ao mesmo servidor e o `Retry-After` quando
  o servidor responde 503 (até 3 tentativas).
- Cada colheita é registrada em `harvest_runs` com o status `running`, `ok`, `error` ou `partial`,
  as contagens e a mensagem de erro, se houver.
- Registros apagados na origem ficam marcados como `deleted` e deixam de aparecer na busca.
- A colheita também pode rodar com o servidor no ar; ela só escreve em `oai_records` e
  `harvest_runs`.

Se uma fonte falhar (por exemplo, desafio anti-robô ou erro 502 do servidor), a colheita dela
termina com erro registrado; no `run-all` as outras fontes seguem e o comando termina com código de
saída de erro (útil para o agendador avisar). Não contorne desafios anti-robô: escreva ao administrador
da fonte.

Agendamento periódico (cron do sistema): ver `docs/IMPLANTACAO.md`.

## 5. Servidor

### 5.1 Desenvolvimento

```
python tasks.py run        # equivale a: uv run python -m app.run
```

Sobe em <http://127.0.0.1:8000> com **um processo** (o limite de requisições é em memória). Não há
recarga automática: reinicie depois de mudar o código.

### 5.2 Produção simples (sem Docker)

O mesmo comando, com `APP_ENV=production`, uma `SECRET_KEY` de 32 caracteres ou mais e
`ALLOWED_ORIGINS` com o endereço público (sem `*`; em produção a aplicação recusa iniciar de outro
modo). O servidor escuta **só** em `127.0.0.1:8000` e confia nos cabeçalhos `X-Forwarded-*` apenas
de `127.0.0.1`: ele deve ficar **atrás de um proxy reverso** (Nginx ou Caddy) na mesma máquina, que
cuida do HTTPS. Em produção a resposta passa a enviar `Strict-Transport-Security`.

Pontos de atenção:

- **Um único processo** do Uvicorn: o limite de requisições não é compartilhado entre processos.
- Decida `DOCS_ENABLED`: `true` mantém `/api/docs` público; `false` o desliga.
- Os logs saem em JSON na saída padrão; o proxy ou o gerenciador de serviço os guarda.
- Verificação de saúde: `GET /api/v1/health` (responde 200 mesmo com o banco fora; veja o campo
  `database`).
- Atualizar uma instalação: obter o código novo, `uv sync`, `uv run alembic upgrade head` e reiniciar.

O serviço de exemplo (systemd), o proxy reverso, a colheita agendada e o backup do banco estão em
`docs/IMPLANTACAO.md`.

## 6. Desenvolvimento e testes

Veja `docs/TESTES.md` e o `README.md`: `python tasks.py install`, `check`, `test`.

Se o PostgreSQL local cair (por exemplo, depois de reiniciar a máquina), os testes de banco e os
fluxos de ponta a ponta falham por "connection timeout expired": inicie o banco e espere a
recuperação terminar (`pg_isready` deve responder "aceitando conexões").
