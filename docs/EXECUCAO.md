# Como executar o projeto

> Este documento cresce a cada OS. A revisão final é da OS-034.

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

### 1.2 Configuração

No `.env` (nunca commitado):

```
DATABASE_URL=postgresql+psycopg://app_user:SENHA@127.0.0.1:5432/academic_search
TEST_DATABASE_URL=postgresql+psycopg://app_user:SENHA@127.0.0.1:5432/academic_search_test
```

Sem `TEST_DATABASE_URL`, os testes de integração são **pulados** (não falham).

### 1.3 Migrações

```
uv run alembic upgrade head      # aplica
uv run alembic downgrade base    # desfaz tudo
uv run alembic current           # revisão atual
```

A migração `0001` cria as extensões, a função `immutable_unaccent(text)` e a configuração de busca
`pt_unaccent` (ver `docs/DECISOES.md`).

### 1.4 Windows: loop de eventos

O `psycopg` assíncrono não funciona com o `ProactorEventLoop`, que é o padrão do Windows. O
`migrations/env.py` e o `tests/conftest.py` já usam o `SelectorEventLoop`. O servidor faz o mesmo
(OS-014).

## 2. Ambiente de desenvolvimento

Veja o `README.md`: `python tasks.py install`, `check`, `test`.
