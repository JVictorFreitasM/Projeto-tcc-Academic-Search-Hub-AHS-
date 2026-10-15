# Como continuar o projeto em outro computador

Atualizado em **15/10/2026** (fim da tarde). Este roteiro diz **onde o projeto está**, **como
preparar outro computador** e **o que ainda falta**, na ordem em que vale a pena fazer.

Repositório: <https://github.com/JVictorFreitasM/Projeto-tcc-Academic-Search-Hub-AHS-> (ramo `main`).

## 1. Onde o projeto está

- **Sistema:** as 37 OS estão feitas, mais a busca por autor e a BDTD pela API REST. Contagem de
  testes e cobertura: `docs/evidencias/os-030-cobertura.txt` (gere de novo com `python tasks.py test-stats`).
- **Fontes que funcionam com dados reais (15/10/2026):** CORE, OpenAlex e **BDTD** (API REST do
  VuFind, sem chave), mais a **UFPE** por OAI-PMH (12.366 registros colhidos). **SciELO, UFPI e
  UESPI não funcionam** por problemas do lado delas (sem OAI, índice vazio, certificado TLS
  incompleto) e ficam desligadas. A raspagem de resumos está ligada no `.env.example`.
- **O TCC está no repositório**, na pasta **`tcc/`** (ver seção 2). Nenhum tempo de busca foi medido.

## 2. O que está na pasta `tcc/`

| Arquivo | O que é |
|---|---|
| `tcc/TCC_COMPLETO_Joao_Victor.docx` | **o arquivo de trabalho do TCC** (com avisos em vermelho e apêndice de notas). É aqui que se edita |
| `tcc/REGRAS_DO_TCC.md` | as regras de escrita (voz de cada seção, citações, números, escopo). **Leia antes de mexer no texto** e peça ao Claude que as siga |
| `tcc/AVISOS_TCC_O_QUE_ALTERAR.md` | o que foi feito no texto e o que só você decide (fontes, UFPE, Nielsen, papel Carta x A4...) |
| `tcc/ORDENS_DE_SERVICO_SISTEMA_v1.2.md` | as 37 ordens de serviço do sistema |
| `tcc/TCC_COMPLETO_Joao_Victor.md` | o `.docx` convertido para leitura (pode ficar desatualizado) |
| `tcc/TCC_COMPLETO_Joao_Victor_PREENCHIDO.md` | rascunho anterior, **substituído** pelo `.docx`; só para consulta |

Antes, esses arquivos ficavam na pasta acima do repositório e não iam para o GitHub. Agora vão:
**edite a cópia de `tcc/`** e faça commit dela. A `TCC_versao_para_o_professor.docx`, se existir,
precisa ser gerada de novo a cada mudança.

**O que não vai para o GitHub (de propósito):** o `.env` (chaves e senha do banco) e o banco de
dados. As chaves do OpenAlex e do CORE você precisa levar por fora (anote ou mande para você mesmo
por um canal privado) e recolocar no `.env` do outro computador. A BDTD não usa chave.

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

### B. Fontes reais (CORE, OpenAlex, BDTD e UFPE já validados)

1. **Chaves e colheita no outro computador:** recoloque no `.env` a chave do OpenAlex
   (`OPENALEX_API_KEY`) e a do CORE (`CORE_API_KEY`); confira `CONTACT_EMAIL` e deixe
   `BDTD_ENABLED=true`. A base de lá começa vazia: rode
   `uv run python -m app.harvest.cli run ufpe` para colher a UFPE de novo (são cerca de 12 mil
   registros; deixe terminar) e confira com `uv run python -m app.harvest.cli status`.
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
   - Em 15/10/2026, UFPI e UESPI também mostraram **cadeia de certificados TLS incompleta**;
   - **BDTD**: já funciona pela **API REST** (sem chave, `BDTD_ENABLED=true`); **SciELO**: nenhum OAI respondeu.
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

- [x] **Capturas com dados reais** (15/10/2026): `docs/evidencias/telas/reais/` (geradas por
  `uv run python scripts/capture_real_screens.py`, com conta de teste fictícia). Já estão no `.docx`.
- [ ] **Importar** os `.bib` e `.ris` exportados no Zotero ou no Mendeley e conferir os campos
  (`docs/evidencias/os-019/LEIA-ME.md`).
- [ ] **Ajustar a coluna "Seção do TCC"** de `docs/evidencias/telas/INDICE.md` ao texto final.

### F. Antes de entregar

- [ ] **Testar o README numa pasta limpa** (clonar de novo e seguir só o README; anotar o que faltou).
  O passo 3 acima já é um bom teste disso.
- [ ] **Ler as 18 divergências** em `docs/CONFORMIDADE_TCC.md` (seção 4) e ajustar o texto do TCC.
- [ ] **Decidir onde o sistema vai rodar.** Se for só na sua máquina para a defesa, o TCC deve dizer
  isso. Se for publicar: `docs/IMPLANTACAO.md` (os exemplos de `deploy/` **não foram executados**).
- [ ] **Texto do TCC e as referências de Nielsen** (`docs/USABILIDADE.md`, seção 7): conferir na fonte.
- [ ] **Etiqueta `v1.0.0`:** só se você quiser (`git tag v1.0.0 && git push --tags`).

## 5. Como continuar com o Claude Code

A conversa desta sessão **não** vai para o outro computador; o que importa está nos arquivos do
repositório. Abra o Claude Code na pasta do projeto e comece com algo assim:

> Leia `docs/CONTINUAR_EM_CASA.md`, `docs/PENDENCIAS_DESENVOLVEDOR.md` e `tcc/AVISOS_TCC_O_QUE_ALTERAR.md`.
> Para mexer no texto do TCC, siga `tcc/REGRAS_DO_TCC.md`. As chaves do OpenAlex e do CORE já estão
> no `.env` e a UFPE já foi colhida.

O arquivo das OS agora está em `tcc/ORDENS_DE_SERVICO_SISTEMA_v1.2.md`. Regras que valem para o
trabalho: um commit por mudança com `python tasks.py check` verde antes, decisões em
`docs/DECISOES.md`, nenhum número que não tenha sido medido, e nada de afirmar "conformidade WCAG 2.1 AA".

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
| O texto do TCC, as regras de escrita e as OS | pasta `tcc/` |

## 7. Armadilhas conhecidas

- **PostgreSQL parado:** testes de banco e de ponta a ponta falham com "connection timeout expired".
  Inicie o banco e espere a recuperação (`pg_isready` deve dizer "aceitando conexões").
- **Disco cheio:** em 15/10/2026 o C: do computador de trabalho ficou sem espaço, e os testes
  pararam com `DiskFull` no PostgreSQL. A pasta de dados do banco foi movida para
  `D:\tcc\pgdata-tcc`; depois de um reinício, ligue com
  `pg_ctl start -D D:\tcc\pgdata-tcc -o "-p 5434" -l D:\tcc\pgdata-tcc.log`. Para os temporários
  dos testes também irem para o D:, antes do `check` rode `$env:TEMP="D:\tcc\temp"; $env:TMP="D:\tcc\temp"`.
- **Windows:** use `python tasks.py ...` (não há `make`); o servidor deve subir por `python tasks.py run`
  (o `uvicorn` direto usa o laço de eventos errado para o psycopg assíncrono).
- **PowerShell:** `$env:X=''` **apaga** a variável (não a deixa vazia); aspas duplas dentro de `psql -c`
  são removidas (use `-f arquivo.sql`); `Remove-Item` perto de caminhos de sistema é bloqueado.
- **Testes de interface** precisam do Chromium do Playwright (`uv run playwright install chromium`).
- **Semgrep** (análise estática) roda num ambiente isolado: `uv venv` numa pasta fora do projeto,
  `uv pip install semgrep` nele e `SEMGREP_BIN=<caminho>\Scripts\semgrep.exe python tasks.py sast`. O
  script agora acusa falha se o semgrep não rodar.
- **O arquivo `.env` nunca vai para o GitHub.** Se perdê-lo, crie outro a partir do `.env.example`.
