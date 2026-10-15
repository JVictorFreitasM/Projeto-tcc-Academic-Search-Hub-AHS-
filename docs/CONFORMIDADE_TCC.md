# Conformidade com o TCC

Matriz das exigências do TCC (E1 a E15) contra o que o sistema faz hoje, com o teste que prova cada
uma e uma observação honesta. Revisão final de **14/10/2026** (OS-035), atualizada em **15/10/2026** com a validação real do OpenAlex.

**Status:** `Atende` (provado por teste ou verificação descrita), `Atende parcialmente` (parte
provada, parte pendente ou com ressalva) e `Não atende`. Nenhum item foi marcado `Atende` sem prova.

**Resumo:** 8 `Atende`, 7 `Atende parcialmente`, 0 `Não atende`. Os parciais têm em comum que
dependem de coisas que só o desenvolvedor pode fornecer: chaves e fontes reais, pessoas para testar,
servidor. A lista está em `docs/PENDENCIAS_DESENVOLVEDOR.md`.

## 1. Matriz E1 a E15

| # | O que o TCC exige | OS | Testes e evidência | Status | Observação |
|---|---|---|---|---|---|
| E1 | Busca unificada em **seis fontes** (CORE, SciELO, OpenAlex, BDTD, UFPI, UESPI) | 007, 008, 009, 010, 012 | `tests/unit/test_openalex_connector.py`, `tests/unit/test_core_connector.py`, `tests/integration/test_oai_local.py`, `tests/unit/test_search_service.py`, `tests/integration/test_search_api.py` | **Atende parcialmente** | Os seis conectores existem e são testados com fixtures sintéticas e servidor falso. **Só o OpenAlex foi validado com dados reais** (15/10/2026, `docs/evidencias/os-007-validacao-real.md`); o CORE segue sem chave; BDTD com desafio anti-robô; SciELO sem OAI encontrado; UFPI e UESPI com OAI no ar, mas sem registros (14/10/2026, `docs/FONTES_CANDIDATAS.md`). Todas as fontes OAI estão `enabled: false` |
| E2 | Integração por APIs (CORE, OpenAlex) e **OAI-PMH** (SciELO, BDTD, UFPI, UESPI), com **índice local** | 007 a 010 | `tests/unit/test_oai_client.py`, `tests/unit/test_parse_oai_dc.py`, `tests/unit/test_oai_sources.py`, `tests/integration/test_harvester.py`, `tests/integration/test_harvest_cli.py` | **Atende parcialmente** | Cliente, colheita incremental, CLI e índice local com busca em português sem acento funcionam e foram provados (inclusive um backup e restauração com dados fictícios). **A colheita real nunca foi exercitada** |
| E3 | **Raspagem só como complemento**, respeitando termos, `robots.txt` e frequência | 013 | `tests/unit/test_polite_scraper.py`, `tests/unit/test_abstract_extractor.py`, `tests/unit/test_scraping_integration.py`, `docs/evidencias/os-013-raspagem.md` | **Atende** | Desligada por padrão; respeita `robots.txt`, pausa de 2 s por domínio, só completa resumos que faltam. **Nunca rodou contra sites reais** (`scripts/measure_scraping.py` é passo do desenvolvedor); o `robots.txt` de UFPI e UESPI proíbe raspar a busca |
| E4 | **Normalização** dos campos e **identificação de repetidos** | 005, 006, 011, 012 | `tests/unit/test_normalize.py`, `tests/unit/test_dedup.py`, `tests/unit/test_record_schema.py`, `tests/unit/test_type_mapping.py`, `docs/evidencias/os-005-mapeamento.md`, `docs/evidencias/os-011-exemplo.md` | **Atende** | Duplicatas por DOI e por título, ano e sobrenome do primeiro autor, sem similaridade difusa. Teses e dissertações saem ambas como `thesis`; monografias e TCCs como `other`; preprint e artigo publicado com DOIs diferentes ficam separados |
| E5 | Filtros por **ano** e **tipo** | 010, 012, 017, 022 | `tests/e2e/test_filters.py`, `tests/integration/test_oai_local.py`, `tests/integration/test_search_api.py` | **Atende parcialmente** | Provado nas fontes locais e na interface. **A sintaxe de filtro do OpenAlex foi confirmada com chamada real (15/10/2026); a do CORE não** (`[VERIFICAR]`, sem chave). Com filtro de ano, registros sem ano ficam de fora (avisado na tela) |
| E6 | **Favoritos** com anotação | 017, 025 | `tests/integration/test_favorites.py`, `tests/e2e/test_favorites_ui.py` | **Atende** | Anotação em texto livre (até 1.000 caracteres). **Tags não foram implementadas** (divergência 1) |
| E7 | **Exportação** em BibTeX, RIS, JSON e CSV | 019 | `tests/unit/test_export_service.py`, `tests/integration/test_export_api.py`, `docs/evidencias/os-019/exemplo.bib` | **Atende** | Quatro formatos provados por teste e por exemplos. **A importação no Zotero ou no Mendeley não foi conferida** (passo manual) |
| E8 | **API pública REST** em JSON, **sem estado**, documentada em OpenAPI | 014 a 020, 034 | `tests/integration/test_app_base.py`, `tests/unit/test_api_docs.py`, `docs/API.md` | **Atende parcialmente** | JSON, sem estado (token em cada requisição) e OpenAPI em `/api/docs`. A autoavaliação REST (`docs/API.md#conformidade-rest`) mostra que **4 rotas têm verbo no caminho** (`/auth/register`, `/auth/login`, `/favorites/export`, `/export`) e que `/health` responde 200 com o banco fora |
| E9 | Servidor em **Python + FastAPI**, **PostgreSQL**, interface em **HTML5 + CSS3 + JavaScript sem frameworks** | 001 a 004, 021 | `tests/unit/test_scope_guard.py`, `pyproject.toml`, `uv.lock` | **Atende** | A varredura confere dependências contra a stack fechada, a ausência de bibliotecas de fila, cache, e-mail e 2FA, e que o frontend só usa módulos nativos locais e nenhum endereço externo |
| E10 | Interface **responsiva** | 021 a 026 | `tests/e2e/test_base_page.py` (320, 768 e 1280 px, sem rolagem horizontal), `tests/a11y/test_axe.py` (360 e 1280 px) | **Atende** | Provado em navegador (Chromium) e nessas larguras. **Não foi testado em aparelhos reais** |
| E11 | **Acessibilidade WCAG 2.1** | 021, 031 | `tests/a11y/test_axe.py`, `docs/evidencias/os-031-axe.txt`, `docs/ACESSIBILIDADE.md` | **Atende parcialmente** | axe sem violações em 16 telas e estados × 2 larguras; checklist de 16 critérios. **Pendentes**: teclado em todas as telas, leitor de tela, zoom de 200% e 400%, alto contraste, e os critérios 2.1.1, 2.1.2, 2.4.3 e 4.1.3. **Não se afirma conformidade WCAG 2.1 AA**: o texto é "atende aos critérios verificados" |
| E12 | **LGPD**: cadastro mínimo, consentimento, acesso, correção e eliminação | 020, 026 | `tests/integration/test_me.py`, `tests/e2e/test_account_ui.py`, `docs/LGPD.md` | **Atende parcialmente** | Consentimento, acesso, correção, portabilidade e eliminação funcionam e são testados. O contato do responsável foi preenchido na política (15/10/2026). **Ainda falta** avisar na política que contas excluídas ficam nas cópias de segurança por até 7 dias (só se o autor mantiver backups) e revisar o texto antes de publicar |
| E13 | **Segurança**: OWASP Top 10 (2017) e análise estática com **mais de uma ferramenta** | 014, 015, 027, 028, 029 | `tests/integration/test_security_owasp.py`, `tests/unit/test_code_hygiene.py`, `tests/unit/test_security.py`, `docs/SEGURANCA.md`, `docs/evidencias/sast/RESUMO.md` | **Atende** | Os dez riscos de 2017 têm controle e teste; quatro ferramentas rodaram em 14/10/2026 (bandit 0, semgrep 0, ruff-S 3 falsos positivos justificados, pip-audit 0 em 86 dependências). Limites escritos: JWT sem revogação individual, limite de requisições em memória (um processo), análise estática não é teste de intrusão |
| E14 | **Cadastro, login e histórico de buscas** | 015, 018, 024 | `tests/integration/test_auth.py`, `tests/integration/test_history.py`, `tests/e2e/test_auth_ui.py`, `tests/e2e/test_flows.py` | **Atende** | Provado inclusive de ponta a ponta com banco real. **Não há recuperação de senha** (sem envio de e-mail; o cadastro avisa). O login mantém a sessão na aba por padrão (divergência da OS-021, `docs/DECISOES.md`) |
| E15 | **Evidências** para o capítulo 4 (capturas, medições, relatórios) | 030 a 033, 035 a 037 | `docs/evidencias/PACOTE.md`, `tests/unit/test_evidence_package.py`, `tests/unit/test_capture_screens_plan.py`, `tests/unit/test_measure_scripts.py` | **Atende parcialmente** | Prontos: 32 capturas (com dados de **demonstração**), axe, cobertura medida, análise estática, avaliação de usabilidade, teste de restauração. **Faltam**: a medição de tempo (nenhum número existe), capturas com dados reais, testes de acessibilidade com pessoas, implantação em servidor |

## 2. Varredura de escopo (seção 3 das OS)

Nada fora do escopo foi implementado. O teste `tests/unit/test_scope_guard.py` olha dependências,
importações, configuração, rotas, tabelas e arquivos; as buscas manuais no código e no frontend
também não acharam nada (só comentários que dizem que algo está fora do escopo e uma frase da política de privacidade que recomenda senha exclusiva).

| Fora do escopo | Resultado da varredura |
|---|---|
| Aplicativo móvel nativo | Nenhum código nem pasta; só interface web responsiva |
| Recomendação automática | Nenhuma rota, tabela, biblioteca ou palavra no código |
| Alertas de novas publicações | Nenhuma rota, tabela ou envio de notificação |
| Integração direta com Zotero, Mendeley | Nenhuma; só exportação em arquivo |
| Outros repositórios | Só as seis fontes. Novas fontes OAI-PMH entram **apenas por edição de `config/oai_sources.yml`**; a rota de fontes só lê (`GET /sources`) e não há tela para adicionar. `docs/FONTES_CANDIDATAS.md` só **documenta** candidatas: nada foi adicionado |
| Outros idiomas de interface; 2FA | Nenhuma biblioteca, configuração ou rota |
| Redis, Celery e filas | Ausentes das dependências (inclusive indiretas, no `uv.lock`) e das importações |
| Frameworks JavaScript e bundlers | Nenhum `package.json`, configuração de Webpack ou Vite, nem arquivo `.ts` no projeto; o frontend usa módulos nativos e nenhum endereço externo |
| Docker como requisito | Nenhum `Dockerfile` nem `docker-compose`; `deploy/` usa systemd, cron e proxy |
| Serviço de e-mail | Nenhuma biblioteca nem configuração de e-mail (só `CONTACT_EMAIL`, que vai no `User-Agent`) |
| Painel de estatísticas | Nenhuma rota de administração nem de estatísticas |
| Modo escuro | Nenhum `prefers-color-scheme` no CSS |
| MARCXML | Só `oai_dc` é colhido |

## 3. Dependências contra a stack fechada (seção 4)

As dependências diretas de `pyproject.toml` são as da stack (mais as adições listadas abaixo): FastAPI, Uvicorn, SQLAlchemy
(assíncrono), Alembic, psycopg 3, Pydantic, pydantic-settings, httpx, defusedxml, argon2-cffi, PyJWT
e slowapi. De desenvolvimento: pytest, pytest-asyncio, respx, pytest-cov, ruff, mypy, bandit,
pip-audit, Playwright e axe-playwright-python. O semgrep roda em ambiente isolado, fora do projeto.

**Adições fora da lista da seção 4** (todas registradas em `docs/DECISOES.md`):

- `pyyaml` e `beautifulsoup4`: as duas adições que a própria OS permite (arquivo de fontes OAI e
  extração de resumos na raspagem).
- `types-pyyaml` e `types-defusedxml`: só dicas de tipo para o `mypy` estrito; não entram em execução.

## 4. Divergências entre o TCC e o sistema

Onde o sistema faz algo diferente do que o TCC afirma, ou onde o texto precisa dizer algo que a
implementação impõe. O autor ajusta o texto (ou o sistema).

| # | OS | O que o TCC diz | O que o sistema faz | O que ajustar no texto |
|---|---|---|---|---|
| 1 | 017 | A seção 2.5 cita a organização de itens por **tags** (folksonomia assistida; Santarém Segundo e Vidotti, 2011) | O favorito tem **anotação em texto livre** (até 1.000 caracteres). Tags como entidade própria **não foram implementadas** | Na seção 4.5, descrever a anotação e dizer que as tags não foram implementadas |
| 2 | 007 a 010 | Busca unificada em seis fontes, por APIs e OAI-PMH | O código cobre as seis, mas **só o OpenAlex foi validado com dados reais** (15/10/2026); nenhuma fonte OAI foi colhida e todas estão desligadas. Em 14/10/2026: UFPI e UESPI com OAI no ar mas sem registros, BDTD com desafio anti-robô, SciELO sem OAI encontrado, CORE sem chave | Relatar o estado real de cada fonte e a data da verificação, em vez de afirmar que as seis funcionam |
| 3 | 007, 008 | Integração com as APIs do OpenAlex e do CORE | OpenAlex: **validado com chamadas reais** (15/10/2026). CORE: testado só com **fixture sintética**; a sintaxe de filtros e ordenação não foi confirmada com chamada real | Descrever a validação do OpenAlex (com data); dizer que a do CORE é pendente, ou fazê-la antes de escrever |
| 4 | 004, 019 | Tipos de publicação (artigo, tese, etc.) | Teses e dissertações são ambas `thesis`; monografias e TCCs são `other`; `preprint` e `book` existem; fontes que não informam tipo caem em `other` | Descrever o mapeamento de tipos e que mestrado e doutorado não são distinguidos |
| 5 | 012 | Total de resultados | O total é uma **estimativa** (soma dos totais das fontes, com possíveis duplicatas) | Chamar de "estimado" onde citar contagens |
| 6 | 005, 010 | Filtro por ano | Registros **sem ano ficam de fora** quando há filtro de ano | Mencionar a regra |
| 7 | 014 a 020 | API REST | Quatro rotas têm verbo no caminho; `/health` responde 200 com o banco fora do ar; `duration_ms` por fonte só aparece com `APP_ENV=development` (`docs/API.md`) | Dizer que a API segue REST nos verbos HTTP, no formato e na ausência de estado, **não** na nomeação dessas quatro rotas (ou renomear: decisão do autor) |
| 8 | 021, 036 | Como o token é guardado (se o texto descrever) | Em memória e, **por padrão, em `sessionStorage`** (por aba), nunca em `localStorage`; o usuário pode desmarcar "manter conectado" | Descrever assim, e não como "só em memória" (`docs/USABILIDADE.md`, seção 4) |
| 9 | 026, 036 | Gestão de conta (LGPD) | Não há **recuperação de senha** (sem envio de e-mail) | Registrar como limitação |
| 10 | 031 | Acessibilidade WCAG 2.1 | O axe não achou violações nas telas e estados varridos e o checklist cobre 16 critérios, mas os testes com pessoas estão pendentes | Dizer "atende aos critérios verificados", listando-os; **nunca** "conformidade WCAG 2.1 AA" |
| 11 | 033 | Redução do tempo de busca (se o TCC afirmar) | **Nenhuma medição foi feita**; só existem os instrumentos (`docs/evidencias/medicao/`) | **Remover a afirmação** se a medição manual não for feita; se for, usar os números exatamente como medidos e as limitações |
| 12 | 036 | Avaliação de interfaces (Cybis et al., 2010; Prates e Barbosa, 2003) | A avaliação foi **heurística, com Nielsen**, por um único avaliador (a IA), sem usuários | Citar Nielsen como método; não citar as duas obras como método aplicado |
| 13 | 037 | Disponibilidade da aplicação, proteção dos dados | Serviço, proxy e cron são **exemplos não executados**; só backup e restauração e o modo produção foram verificados, na máquina de desenvolvimento | Se for só rodar na máquina para a defesa, dizer isso; não descrever um ambiente de produção que não existe |
| 14 | 020, 037 | Eliminação dos dados (LGPD, art. 18) | Conta excluída continua nas **cópias de segurança por até 7 dias** | Dizer isso na política e, se descrever a eliminação, mencionar |
| 15 | 013 | Raspagem complementar | Existe e vem desligada; **nunca foi testada contra sites reais** | Dizer que é opcional e não foi medida em fontes reais |
| 16 | 009, 035 | Seis fontes e nada além | `docs/FONTES_CANDIDATAS.md` mostra outras fontes gratuitas verificadas (UFPE, UFMG, DOAJ...), **não adicionadas** | Se o autor quiser ampliar, o escopo do texto muda |

## 5. Como esta matriz foi conferida

- Cada linha aponta arquivos de teste que existem e que passam na suíte completa (`python tasks.py
  check`, ver `docs/os/OS-035-relatorio.md`). O pacote de evidências é conferido por teste
  (`tests/unit/test_evidence_package.py`).
- O que é "pendente" não foi escondido: está na observação de cada linha e em
  `docs/PENDENCIAS_DESENVOLVEDOR.md`.
