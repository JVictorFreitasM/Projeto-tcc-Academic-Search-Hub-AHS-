# Como continuar o projeto em outro computador

Escrito em 14/10/2026, no fim da sessão em que as 37 Ordens de Serviço (OS-001 a OS-037) foram
executadas. Este roteiro diz **onde o projeto está**, **como preparar outro computador** e **o que
ainda falta**, na ordem em que vale a pena fazer.

Repositório: <https://github.com/JVictorFreitasM/Projeto-tcc-Academic-Search-Hub-AHS-> (ramo `main`).

## 1. Onde o projeto está

- **Todas as 37 OS estão feitas e commitadas.** A suíte completa passa (1191 testes, 2 pulados),
  com 98% de cobertura de `app/`; `ruff`, `mypy` estrito e a análise estática estão limpos.
- **O que falta não é código: é o que só você pode fazer** (chaves, fontes reais, pessoas para testar,
  medição, servidor). A matriz do TCC (`docs/CONFORMIDADE_TCC.md`) tem 8 itens `Atende` e 7
  `Atende parcialmente`, e os parciais são justamente esses.
- **OpenAlex e CORE foram validados com dados reais** e a **UFPE foi colhida por OAI-PMH** (15/10/2026); UFPI/UESPI estão desligadas (OAI vazio e certificado incompleto no servidor deles). Nenhum número de tempo foi medido.

## 2. Antes de sair deste computador

| O quê | Por quê |
|---|---|
| `git push` feito (o último commit local deve aparecer no GitHub) | O outro computador só enxerga o que está no GitHub |
| Copiar o arquivo **`ORDENS_DE_SERVICO_SISTEMA_v1.2.md`** | Ele está na pasta **acima** do repositório (`projeto tcc\`), **não foi enviado** ao GitHub, e tem as especificações (inclusive os "passos manuais" das fontes). Leve por pendrive, e-mail ou nuvem |
| Anotar a senha do banco e a `SECRET_KEY` do `.env` **só se for reutilizá-las** | O `.env` não vai para o GitHub (de propósito). No outro computador crie um `.env` novo; a `SECRET_KEY` pode ser outra |
| Guardar as chaves do OpenAlex e do CORE, se já tiver | Também só ficam no `.env` |

O banco de dados local **não precisa ser levado**: ele é recriado do zero pelas migrações.

## 3. Preparar o outro computador

Requisitos: Git, Python 3.11 ou mais novo (o projeto foi feito em 3.14), [uv](https://docs.astral.sh/uv/)
e PostgreSQL 14 ou mais novo. Os comandos abaixo valem no Windows, no Linux e no macOS.

```
git clone https://github.com/JVictorFreitasM/Projeto-tcc-Academic-Search-Hub-AHS-.git academic-search-hub
cd academic-search-hub
python tasks.py install                    # cria o .venv e instala as dependências
uv run playwright install chromium         # só para os testes de interface
```

**Banco de dados** (como superusuário do PostgreSQL; detalhes em `docs/EXECUCAO.md`, seção 1):

```sql
CREATE USER app_user WITH PASSWORD 'escolha-uma-senha';
CREATE DATABASE academic_search OWNER app_user;
CREATE DATABASE academic_search_test OWNER app_user;
\c academic_search
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- repita as três extensões em academic_search_test
```

**Configuração:** copie `.env.example` para `.env` e preencha `SECRET_KEY` (32 caracteres ou mais; para
gerar: `uv run python -c "import secrets; print(secrets.token_urlsafe(48))"`), `DATABASE_URL` e
`TEST_DATABASE_URL` com a senha escolhida e a porta do seu PostgreSQL (a padrão é 5432; neste
computador era 5434). Nunca faça commit do `.env`.

```
uv run alembic upgrade head                # cria as tabelas
python tasks.py check                      # confere tudo (leva uns 7 a 10 minutos)
python tasks.py run                        # sobe o site em http://127.0.0.1:8000
```

Se o `check` terminar verde, o outro computador está igual a este. Sem `TEST_DATABASE_URL` os testes
que precisam de banco são **pulados** (não falham). `python tasks.py test-unit` roda só os rápidos.

## 4. O que está pendente, em ordem

A lista completa e detalhada, com caixas para marcar, está em
**`docs/PENDENCIAS_DESENVOLVEDOR.md`**. Aqui está a ordem sugerida e o primeiro passo de cada uma.

### A. Decisões rápidas (minutos)

- [x] **Contato do responsável na política de privacidade:** preenchido em 15/10/2026 (nome e e-mail em
  `app/content/privacy_pt.md`; o teste `test_privacy_policy_is_public` confere). Falta só o aviso
  sobre as cópias de segurança, se você for manter backups (seção F). Se um dia mudar o texto da
  política, suba `PRIVACY_POLICY_VERSION` (o mesmo teste e outros esperam a versão `1.0`, então
  ajuste-os juntos) para as pessoas aceitarem de novo.
- [ ] **Nomes de 4 rotas da API** (`/auth/register`, `/auth/login`, `/favorites/export`, `/export`):
  manter e escrever no TCC, ou renomear. Ver `docs/API.md#conformidade-rest`.
- [ ] **Caixa "Manter conectado nesta aba" marcada por padrão:** confirmar ou reverter (como reverter
  em `docs/USABILIDADE.md`, seção 4).
- [ ] **Ampliar as fontes além das seis do TCC?** Ver `docs/FONTES_CANDIDATAS.md`, seção 5.
- [ ] **Conferir o titular do `LICENSE`** (MIT) e perguntar ao orientador se a UESPI tem regra sobre
  licença de TCC.

### B. Fontes reais (o que mais pesa: nenhuma foi validada)

1. **Chaves gratuitas:** a do **OpenAlex já foi usada e validada** (15/10/2026), mas ela só existe no
   `.env` do computador de onde você saiu: **recoloque-a em `OPENALEX_API_KEY` no `.env` de casa**. A do
   CORE também foi validada: **recoloque-a em `CORE_API_KEY`**; confira `CONTACT_EMAIL`. Para a UFPE, rode `uv run python -m app.harvest.cli run ufpe` (a base de casa começa vazia).
2. **Gravar respostas reais** no lugar das fixtures sintéticas:
   - OpenAlex: **já feito** (`tests/fixtures/openalex/search_ok.json` é resposta real);
   - CORE: **já feito** (`search_ok.json` é resposta real). Antes era: salvar a resposta de `GET /v3/search/works/?q=educação&limit=5` (com a chave, como o
     conector monta em `app/connectors/core_api.py`) em `tests/fixtures/core/search_ok.json`;
   - OAI: `uv run python -m app.harvest.cli dump <fonte>` grava o `Identify` e uma página de registros.
   - Depois: `STRICT_FIXTURES=1 uv run pytest tests/contract` lista o que ainda é sintético, e
     `python tasks.py check` mostra se algum conector precisa de ajuste. Se divergir, registre em
     `docs/DECISOES.md`.
3. **Fontes OAI** (`config/oai_sources.yml`, hoje `enabled: false` e `TODO-VERIFICAR`):
   - **UFPI** (`https://repositorio.ufpi.br/oai/request`) e **UESPI**
     (`https://repositorio.uespi.br/oai/request`) respondem, mas **sem registros** (14/10/2026): peça
     ao administrador para reindexar o OAI e teste com
     `uv run python -m app.harvest.cli run uespi --limit 50 --dry-run`;
   - **BDTD**: desafio anti-robô (não contornar); **SciELO**: nenhum OAI respondeu.
   - Alternativas que **já funcionam** só com configuração: **UFPE** e **UFMG** (ver
     `docs/FONTES_CANDIDATAS.md`, com um exemplo de `type_map`).
4. **Colher:** `uv run python -m app.harvest.cli run-all` e conferir com `... status`.

### C. Medição de tempo (sem ela o TCC não pode afirmar redução de tempo)

1. Escrever as **5 consultas** em `docs/evidencias/medicao/consultas.txt` e o **critério de "resultado
   útil"** em `docs/evidencias/medicao/ROTEIRO_MANUAL.md`.
2. Medição **manual**: seguir o roteiro, preencher a planilha e rodar
   `uv run python scripts/summarize_manual.py <planilha>.csv`.
3. Medição da **aplicação**: com o servidor no ar e as fontes colhidas,
   `uv run python scripts/measure_search.py --base-url http://127.0.0.1:8000 --runs 5`. (A duração
   por fonte só aparece com `APP_ENV=development`.)
4. Copiar os números **exatamente como saíram** para `docs/evidencias/medicao/RELATORIO.md`.
   **Se não for medir, remova do TCC qualquer afirmação de redução de tempo.**

### D. Testes com pessoas

- [ ] **Acessibilidade (M1 a M5 em `docs/ACESSIBILIDADE.md`):** só teclado, leitor de tela (NVDA no
  Windows ou VoiceOver no macOS), zoom de 200% e 400%, alto contraste. Anote o resultado na tabela.
- [ ] **Usabilidade com 3 a 5 colegas** (opcional): roteiro de 4 tarefas em `docs/USABILIDADE.md`,
  seção 6, sem medir tempo e sem calcular porcentagem.

### E. Capturas e importações

- [ ] **Capturas com dados reais** das fontes: `docs/evidencias/telas/ROTEIRO_REAIS.md` (sem chave e
  sem e-mail verdadeiros nas imagens).
- [ ] **Importar** os `.bib` e `.ris` exportados no Zotero ou no Mendeley e conferir os campos
  (`docs/evidencias/os-019/LEIA-ME.md`).
- [ ] **Ajustar a coluna "Seção do TCC"** de `docs/evidencias/telas/INDICE.md` ao texto final.

### F. Antes de entregar

- [ ] **Testar o README numa pasta limpa** (clonar de novo e seguir só o README; anotar o que faltou).
  O passo 3 acima já é um bom teste disso.
- [ ] **Ler as 17 divergências** em `docs/CONFORMIDADE_TCC.md` (seção 4) e ajustar o texto do TCC.
- [ ] **Decidir onde o sistema vai rodar.** Se for só na sua máquina para a defesa, o TCC deve dizer
  isso. Se for publicar: `docs/IMPLANTACAO.md` (os exemplos de `deploy/` **não foram executados**).
- [ ] **Texto do TCC e as referências de Nielsen** (`docs/USABILIDADE.md`, seção 7): conferir na fonte.
- [ ] **Etiqueta `v1.0.0`:** só se você quiser (`git tag v1.0.0 && git push --tags`).

## 5. Como continuar com o Claude Code

A conversa desta sessão **não** vai para o outro computador; o que importa está nos arquivos do
repositório. Abra o Claude Code na pasta do projeto e comece com algo assim:

> Leia `docs/CONTINUAR_EM_CASA.md` e `docs/PENDENCIAS_DESENVOLVEDOR.md`. As 37 OS estão feitas. Quero
> continuar pela seção B (fontes reais): já tenho as chaves do OpenAlex e do CORE no `.env`.

Se for pedir mudanças que dependam do texto das OS, copie o `ORDENS_DE_SERVICO_SISTEMA_v1.2.md` para a
pasta **acima** do repositório (ou diga o caminho). Regras que valem para o trabalho: um commit por
mudança com `python tasks.py check` verde antes, decisões em `docs/DECISOES.md`, nenhum número que não
tenha sido medido, e nada de afirmar "conformidade WCAG 2.1 AA".

## 6. Onde achar cada coisa

| Quero... | Arquivo |
|---|---|
| Ver o que cada OS fez | `docs/os/OS-0XX-relatorio.md` |
| Saber o que o TCC exige e se o sistema atende | `docs/CONFORMIDADE_TCC.md` |
| Todas as decisões e divergências, com data e motivo | `docs/DECISOES.md` |
| A lista de pendências detalhada | `docs/PENDENCIAS_DESENVOLVEDOR.md` |
| O que sustenta cada seção 4.1 a 4.6 do TCC | `docs/evidencias/PACOTE.md` |
| Instalar, configurar e rodar | `README.md`, `docs/EXECUCAO.md` |
| Colocar no ar, backup e restauração | `docs/IMPLANTACAO.md` |
| Rotas da API e a autoavaliação REST | `docs/API.md` |
| Segurança (OWASP) e análise estática | `docs/SEGURANCA.md` |
| LGPD | `docs/LGPD.md` |
| Fontes que dá para adicionar | `docs/FONTES_CANDIDATAS.md` |

## 7. Armadilhas conhecidas

- **PostgreSQL parado:** testes de banco e de ponta a ponta falham com "connection timeout expired".
  Inicie o banco e espere a recuperação (`pg_isready` deve dizer "aceitando conexões").
- **Windows:** use `python tasks.py ...` (não há `make`); o servidor deve subir por `python tasks.py run`
  (o `uvicorn` direto usa o laço de eventos errado para o psycopg assíncrono).
- **PowerShell:** `$env:X=''` **apaga** a variável (não a deixa vazia); aspas duplas dentro de `psql -c`
  são removidas (use `-f arquivo.sql`); `Remove-Item` perto de caminhos de sistema é bloqueado.
- **Testes de interface** precisam do Chromium do Playwright (`uv run playwright install chromium`).
- **Semgrep** (análise estática) roda num ambiente isolado: `uv venv` numa pasta fora do projeto,
  `uv pip install semgrep` nele e `SEMGREP_BIN=<caminho>\Scripts\semgrep.exe python tasks.py sast`. O
  script agora acusa falha se o semgrep não rodar.
- **O arquivo `.env` nunca vai para o GitHub.** Se perdê-lo, crie outro a partir do `.env.example`.
