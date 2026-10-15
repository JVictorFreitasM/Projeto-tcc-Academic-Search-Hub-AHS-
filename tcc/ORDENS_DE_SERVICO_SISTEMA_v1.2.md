# ORDENS DE SERVIÇO — PIPELINE DE DESENVOLVIMENTO DO SISTEMA

**Projeto:** Aplicação web para automação de busca e raspagem de dados em repositórios acadêmicos de acesso aberto
**Autor do TCC:** João Victor de Freitas Martins — UESPI, Tecnólogo em Sistemas para a Internet
**Versão deste arquivo:** 1.2 — 08/10/2026 (inclui BDTD, UFPI e UESPI; acrescenta a Fatia 1 para capturas, a OS-036 e a OS-037)
**Destino:** ser lido por uma IA dentro da IDE, que executará **uma OS por vez**, na ordem, até concluir todo o sistema.

---

## 0. COMO USAR ESTE ARQUIVO (LEIA ANTES DE QUALQUER OS)

### 0.1 Para a IA da IDE: protocolo de execução

Você é uma IA de desenvolvimento. Este arquivo é a única fonte de verdade do que construir. Execute assim:

1. O desenvolvedor dirá qual OS executar (ex.: "Execute a OS-007"). Execute **somente essa**.
2. Leia, nesta ordem: as seções 0 a 6 deste arquivo (regras, escopo, arquitetura, contratos) e depois a OS pedida. Confirme que todas as OS listadas em **Depende de** já têm o relatório `docs/os/OS-XXX-relatorio.md` e que seus critérios de aceite passaram. Se não, **pare** e avise.
3. Escreva um plano de no máximo 10 linhas antes de codar. Depois implemente.
4. Rode os testes, o lint e a checagem de tipos exigidos. Corrija até passar.
5. Percorra a lista **Critérios de aceite** item por item e marque cada um com evidência (comando e resultado).
6. Crie `docs/os/OS-XXX-relatorio.md` com: o que foi feito, decisões tomadas, desvios em relação à OS (e por quê), comandos executados e resultados, evidência para o TCC (quando a OS pedir).
7. Faça **um commit por OS**, com a mensagem indicada na OS. Não faça push sem o desenvolvedor pedir.
8. Pare. Não comece a próxima OS por conta própria.

### 0.2 Regras de ouro (valem para todas as OS)

1. **Não invente comportamento de API externa.** Quando a realidade (resposta real, fixture gravada, documentação oficial) divergir deste arquivo, a realidade vence. Registre a divergência em `docs/DECISOES.md` e ajuste o código e as fixtures.
2. **Itens marcados `[VERIFICAR]`** são pontos que este arquivo não conseguiu confirmar. Verifique na primeira chamada real ou na documentação oficial, e registre o resultado em `docs/DECISOES.md`.
3. **Escopo fechado.** Implemente só o que está na seção 2 (dentro do escopo). O que está na seção 3 (fora do escopo) **não deve ser implementado nem preparado** (nada de "gancho para o futuro").
4. **Stack fechada** (seção 4). Não adicione frameworks, serviços ou linguagens fora da lista. Se achar que falta algo, registre em `docs/DECISOES.md` e pergunte ao desenvolvedor.
5. **Nenhum segredo no repositório.** Chaves, senhas e `SECRET_KEY` só em variáveis de ambiente. Mantenha `.env.example` sem valores reais e `.env` no `.gitignore`.
6. **Nenhum número sem medição.** Não escreva em código, documentação ou relatório afirmações de desempenho, cobertura de fontes ou ganho de tempo que não tenham sido medidas por um script do próprio projeto.
7. **Idioma:** interface, mensagens de erro ao usuário, documentação e relatórios em **português do Brasil**. Identificadores de código (variáveis, funções, classes, campos JSON da API, nomes de tabelas e colunas) em **inglês**. Comentários e docstrings em português.
8. **Qualidade mínima em toda OS:** `ruff check` e `ruff format --check` sem erros; `mypy` sem erros nos módulos novos; testes da OS passando; nenhum teste anterior quebrado.
9. **Testes sem rede.** Nenhum teste automatizado pode chamar a internet. Conectores são testados com **fixtures** (respostas gravadas em `tests/fixtures/`) e com `respx` para simular o HTTP. A validação com chaves reais é um passo **manual** do desenvolvedor, descrito em cada OS de conector.
10. **Segurança desde o início** (OS-027 consolida, mas não deixe para depois): consultas ao banco sempre parametrizadas, XML sempre com `defusedxml`, nada de `pickle`/`eval`/`exec`, nada de `innerHTML` com dados externos no frontend.
11. **Acessibilidade desde o início:** HTML semântico, rótulos em todos os campos, foco visível, contraste mínimo de 4,5:1 para texto comum. A OS-031 verifica, mas não é a primeira vez que se pensa nisso.
12. **Em dúvida, pergunte** ao desenvolvedor em vez de supor, principalmente sobre escopo, nomes de domínio e decisões que mudam o TCC.

### 0.3 Formato de cada OS

Cada OS tem: **Depende de**, **Rastreabilidade no TCC**, **Objetivo**, **Decisões já tomadas**, **Tarefas**, **Arquivos**, **Especificação detalhada**, **Critérios de aceite**, **Testes obrigatórios**, **Proibido nesta OS**, **Evidência para o TCC** e **Commit**.

---

## 1. VISÃO GERAL DO PRODUTO

Uma aplicação web que permite a um estudante de graduação da UESPI buscar trabalhos acadêmicos em **uma única consulta** nas fontes **CORE, SciELO, OpenAlex e nos repositórios institucionais BDTD (IBICT), UFPI e UESPI**, ver os resultados **unificados e sem duplicatas**, filtrá-los por **ano e tipo de publicação**, **salvar favoritos**, **exportar** em formatos de gerenciadores de referências (**BibTeX, RIS, JSON, CSV**) e consumir os mesmos dados por uma **API pública REST em JSON**. A interface é **exclusivamente web**, responsiva (computador, tablet, celular), acessível (WCAG 2.1) e em conformidade com a LGPD.

**Pergunta de pesquisa do TCC:** como uma aplicação web pode contribuir para que estudantes de graduação da UESPI localizem, em uma única consulta, trabalhos acadêmicos disponíveis em múltiplos repositórios de acesso aberto?

---

## 2. DENTRO DO ESCOPO (o que deve existir ao final)

| # | Funcionalidade | Origem no TCC |
|---|---|---|
| E1 | Busca unificada em **seis fontes**: CORE, SciELO, OpenAlex, **BDTD (IBICT), UFPI e UESPI** | Introdução; 2.1; 2.2; 4.2 |
| E2 | Integração por **interfaces programáticas (CORE, OpenAlex) e OAI-PMH (SciELO, BDTD, UFPI, UESPI)**, com colheita para um **índice local** | Introdução; 2.1; 2.2; 3 |
| E3 | **Raspagem de dados apenas como complemento**, com respeito a termos de uso, `robots.txt` e limite de frequência | Introdução; 2.2 (Vargiu e Urru, 2012) |
| E4 | Normalização dos campos (título, autores, resumo, ano, DOI, endereço) em estrutura única e identificação de registros repetidos | 2.2 (Chan e Zeng, 2006; Zeng e Chan, 2006) |
| E5 | Filtros por **ano** e **tipo de publicação** | Introdução |
| E6 | **Favoritos** (com anotação do usuário) | Introdução; 2.5 |
| E7 | **Exportação** em BibTeX, RIS, JSON e CSV | Introdução |
| E8 | **API pública REST** em **JSON**, sem estado (stateless), documentada em OpenAPI | Introdução; 2.3 (Fielding, 2000; Bray, 2017) |
| E9 | Servidor em **Python + FastAPI**, banco **PostgreSQL**, interface em **HTML5 + CSS3 + JavaScript** sem frameworks | 2.4; 3 |
| E10 | Interface **responsiva** | 2.5 (Bader e Hammouri, 2016) |
| E11 | **Acessibilidade WCAG 2.1** | 2.5 (W3C, 2018) |
| E12 | **LGPD:** cadastro mínimo, consentimento, acesso, correção e eliminação dos dados pelo titular | 2.6 (Brasil, 2018, arts. 6º, 18 e 46) |
| E13 | **Segurança:** os dez riscos do **OWASP Top 10 (2017)** tratados, e análise estática com **mais de uma ferramenta** | 2.6 (OWASP, 2017; Nunes et al., 2018) |
| E14 | Cadastro e login (necessários para favoritos e histórico) e **histórico de buscas** | Introdução; 2.5 |
| E15 | Evidências para o capítulo **Resultados e Discussões** (capturas de tela, medições, relatórios) | 4.1 a 4.6 |

## 3. FORA DO ESCOPO (NÃO IMPLEMENTAR NEM PREPARAR)

Estes itens estão declarados no TCC como **trabalhos futuros**. Não crie código, tabelas, rotas, campos ou "ganchos" para eles.

- Aplicativo móvel nativo (Android/iOS).
- Recomendação automática de trabalhos.
- Alertas de novas publicações (e-mail ou notificação).
- Integração **direta** com Zotero, Mendeley ou outros gerenciadores (a exportação em arquivo é suficiente).
- Outros repositórios além de CORE, SciELO, OpenAlex, BDTD, UFPI e UESPI. (A arquitetura aceita novas fontes OAI-PMH **apenas por edição do arquivo de configuração** descrito em 5.5; não construa tela, rota ou ferramenta para isso.)
- Outros idiomas de interface; autenticação em dois fatores.
- Também fora, por não constarem na stack do TCC: **Redis, Celery/filas, frameworks JavaScript/TypeScript, bundlers (Webpack/Vite), Docker como requisito, serviços de e-mail, painéis de estatísticas, modo escuro, MARCXML.**

---

## 4. STACK E DEPENDÊNCIAS (FECHADA)

| Camada | Tecnologia | Observação |
|---|---|---|
| Linguagem do servidor | **Python 3.11 ou superior** | Van Rossum (1991); Menezes (2010) |
| Framework web | **FastAPI** (com Uvicorn) | Ramírez (2018). Usar `async`/`await` nas consultas aos repositórios |
| Banco de dados | **PostgreSQL 14 ou superior** | Stonebraker e Kemnitz (1991) |
| Acesso ao banco | **SQLAlchemy 2.x** (estilo 2.0, assíncrono) + **Alembic** + driver **psycopg 3** | |
| Validação/configuração | **Pydantic v2** e **pydantic-settings** | |
| Cliente HTTP | **httpx** (assíncrono) | |
| XML (OAI-PMH) | **defusedxml** | Previne XXE (OWASP A4) |
| Senhas | **argon2-cffi** (Argon2id) | |
| Token | **PyJWT** (HS256) | Autenticação sem estado |
| Limite de requisições | **slowapi** (armazenamento em memória) | Sem Redis |
| Testes | **pytest**, **pytest-asyncio**, **respx**, **pytest-cov** | |
| Qualidade | **ruff**, **mypy** | |
| Segurança (dev) | **bandit**, **pip-audit**, **semgrep** (se disponível) | Nunes et al. (2018): mais de uma ferramenta |
| Frontend | **HTML5, CSS3, JavaScript (ES2020+, módulos nativos)** | W3C (2014, 2018); Flanagan (2013); Teruel (2014) |
| Testes de interface (dev) | **Playwright** (Python) e **axe-playwright-python** | Somente desenvolvimento |

**Regra de versões:** use a versão estável mais recente de cada pacote no momento da implementação e registre as versões em `requirements.lock` (ou `uv.lock`/`poetry.lock`). Não copie números de versão deste arquivo.

---

## 5. ARQUITETURA

### 5.1 Visão em camadas

```
Navegador (HTML5 + CSS3 + JS)  ──HTTP/JSON──▶  FastAPI (/api/v1)
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    ▼                            ▼                            ▼
              Serviço de busca             Serviços de usuário        Serviço de exportação
              (orquestrador)               (auth, favoritos,          (BibTeX, RIS, JSON, CSV)
                    │                       histórico, conta/LGPD)
        ┌───────────┼─────────────┐                │
        ▼           ▼             ▼                ▼
  Conector      Conector      Conectores OAI   PostgreSQL
  OpenAlex      CORE          locais (SciELO,  (usuários, favoritos, histórico,
  (API REST)    (API REST)    BDTD, UFPI,      eventos de segurança,
                              UESPI) sobre     índice OAI local)
                              o índice local
                                  ▲
                                  │ colheita periódica (CLI)
                            Cliente OAI-PMH ──▶ SciELO, BDTD, UFPI, UESPI (oai_dc)

  Complemento opcional: Raspador polido (resumo faltante) ──▶ páginas HTML públicas
```

### 5.2 Decisões de arquitetura (já tomadas)

- **D1. OpenAlex e CORE são consultados ao vivo** a cada busca, por suas APIs REST.
- **D2. SciELO, BDTD, UFPI e UESPI são colhidos por OAI-PMH e pesquisados localmente.** Todas as fontes OAI-PMH são declaradas em `config/oai_sources.yml` (5.5) e gravadas numa **única tabela** `oai_records`, com a coluna `source`. OAI-PMH é um protocolo de **colheita** (verbs `Identify`, `ListSets`, `ListIdentifiers`, `ListRecords`, `GetRecord`): não existe verbo de busca por palavra-chave. Portanto o sistema colhe os metadados em `oai_dc` e grava no PostgreSQL, e a busca dessas fontes é uma busca de texto completo local (`tsvector`). A colheita é um comando de linha (CLI), não uma rota da API.
- **D3. Paginação combinada** (ver 6.4): cada fonte ativa devolve a página `p` com tamanho `ceil(n / k)`, onde `n` é o tamanho de página pedido e `k` o número de fontes ativas (até seis); o resultado é intercalado e deduplicado. O total é **estimado** (soma dos totais das fontes) e deve ser rotulado como estimado.
- **D4. Falha parcial não derruba a busca.** Se uma fonte falhar ou estourar o tempo, a resposta traz as outras e informa o estado de cada fonte em `sources_status`.
- **D5. Autenticação sem estado:** JWT no cabeçalho `Authorization: Bearer`. Sem sessão no servidor (Fielding, 2000).
- **D6. Sem cache externo (Redis).** Nenhum cache de resultados de busca nesta versão. Medições de desempenho (OS-033) mostram o custo real; otimizações ficam fora.
- **D7. O frontend é estático** (arquivos HTML/CSS/JS servidos pelo próprio FastAPI com `StaticFiles`), sem etapa de build.
- **D8. A raspagem é complementar, desligada por padrão** (`SCRAPING_ENABLED=false`) e só roda para completar o **resumo** de registros que vieram sem ele (OS-013).

### 5.3 Estrutura de pastas (alvo final)

```
academic-search-hub/
├── README.md
├── pyproject.toml            # dependências e configuração de ruff/mypy/pytest
├── requirements.lock         # versões travadas
├── .env.example
├── .gitignore
├── alembic.ini
├── config/
│   └── oai_sources.yml       # fontes OAI-PMH (slug, nome, URL, set, mapeamento de tipo)
├── docs/
│   ├── DECISOES.md           # decisões e divergências (registro vivo)
│   ├── API.md                # visão humana da API (a fonte é o OpenAPI)
│   ├── SEGURANCA.md          # mapa OWASP 2017 → controles + resultados das ferramentas
│   ├── LGPD.md               # mapa dos direitos do titular → rotas
│   ├── ACESSIBILIDADE.md     # checklist WCAG 2.1 + resultados
│   ├── EXECUCAO.md           # como rodar, colher SciELO, testar
│   ├── os/                   # um relatório por OS
│   └── evidencias/           # capturas e medições para o TCC (capítulo 4)
├── migrations/               # Alembic
├── app/
│   ├── main.py
│   ├── core/                 # config.py, logging.py, security.py, errors.py
│   ├── db/                   # session.py, base.py
│   ├── models/               # user.py, favorite.py, search_history.py, security_event.py, oai_record.py
│   ├── schemas/              # record.py, search.py, user.py, favorite.py, common.py
│   ├── api/v1/               # router.py, auth.py, search.py, favorites.py, history.py, export.py, me.py, health.py
│   ├── services/             # search_service.py, dedup.py, normalize.py, export_service.py, auth_service.py, ...
│   ├── connectors/           # base.py, openalex.py, core_api.py, oai_local.py, http.py
│   ├── harvest/              # oai_client.py, oai_sources.py (lê o YAML), harvester.py, cli.py
│   └── scraping/             # polite_scraper.py, abstract_extractor.py
├── frontend/
│   ├── index.html            # busca e resultados
│   ├── favoritos.html
│   ├── conta.html
│   ├── privacidade.html
│   ├── css/                  # tokens.css, base.css, layout.css, components.css
│   └── js/                   # api.js, state.js, search.js, filters.js, auth.js, favorites.js, export.js, account.js, a11y.js, dom.js
├── scripts/
│   ├── measure_search.py     # OS-033
│   └── capture_screens.py    # OS-032
└── tests/
    ├── unit/  integration/  contract/  e2e/  a11y/
    └── fixtures/             # openalex/, core/, oai/ (uma pasta por fonte), html/
```

### 5.4 Variáveis de ambiente (`.env.example`)

| Variável | Padrão no exemplo | Uso |
|---|---|---|
| `APP_ENV` | `development` | `development` ou `production` |
| `SECRET_KEY` | *(vazio; obrigatório)* | Assinatura do JWT. Mínimo de 32 bytes aleatórios |
| `DATABASE_URL` | `postgresql+psycopg://user:pass@localhost:5432/academic_search` | Banco |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Validade do token |
| `ALLOWED_ORIGINS` | `http://localhost:8000` | CORS (lista separada por vírgulas) |
| `OPENALEX_API_KEY` | *(vazio)* | Chave gratuita (conta em openalex.org) |
| `CORE_API_KEY` | *(vazio)* | Chave gratuita (registro em core.ac.uk/services/api) |
| `OAI_SOURCES_FILE` | `config/oai_sources.yml` | Arquivo com as fontes OAI-PMH (ver 5.5) |
| `CONTACT_EMAIL` | *(vazio)* | Identificação em `User-Agent` de colheita e raspagem |
| `OAI_HARVEST_DELAY_SECONDS` | `1` | Pausa entre requisições de colheita ao mesmo servidor |
| `SCRAPING_ENABLED` | `false` | Liga a raspagem complementar |
| `SOURCE_TIMEOUT_SECONDS` | `10` | Tempo limite por fonte |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | `20` / `50` | Paginação |
| `RATE_LIMIT_SEARCH` | `60/minute` | Por IP |
| `RATE_LIMIT_AUTH` | `5/minute` | Por IP, em login e cadastro |
| `LOG_LEVEL` | `INFO` | Logs |
| `DOCS_ENABLED` | `true` | Liga `/api/docs` (OS-014 e OS-027) |
| `TEST_DATABASE_URL` | *(vazio)* | Banco só para testes de integração (OS-003) |
| `PRIVACY_POLICY_VERSION` | `1.0` | Versão registrada no consentimento |

### 5.5 Fontes OAI-PMH configuráveis (`config/oai_sources.yml`)

Cada fonte OAI-PMH é uma entrada do arquivo, validada por Pydantic ao iniciar. Campos de cada entrada:

| Campo | Tipo | Regra |
|---|---|---|
| `slug` | string | `a-z0-9_`, único. Valor gravado em `oai_records.source` e exposto em `Record.sources[].source` |
| `name` | string | Nome para exibir (ex.: "BDTD (IBICT)") |
| `base_url` | string | Endereço do OAI-PMH. Só `https` (aceitar `http` apenas se o servidor não oferecer `https`, registrando em `docs/DECISOES.md`) |
| `metadata_prefix` | string | `oai_dc` (padrão) |
| `set_spec` | string \| null | Restringe a colheita a um *set* (ex.: um periódico ou uma coleção) |
| `enabled` | bool | Fonte colhida e pesquisada só se `true` |
| `default_type` | enum | Tipo atribuído quando `dc:type` não ajuda (ver 6.3) |
| `type_map` | mapa texto→enum | Tradução de valores de `dc:type` (comparação sem acento e em minúsculas) |

Entradas iniciais (**todas as URLs são `[VERIFICAR]`**: rode `?verb=Identify` e registre o resultado em `docs/DECISOES.md`; **não** chute endereços):

| slug | name | Observação |
|---|---|---|
| `scielo` | SciELO | Endereço do Brasil não confirmado; ver 6.1 |
| `bdtd` | BDTD (IBICT) | Agrega teses e dissertações de instituições brasileiras. O padrão de metadados da BDTD é o MTD-BR3 e o protocolo é OAI-PMH (Almeida e Dias, 2023). Confirmar o endereço e se `oai_dc` está disponível |
| `ufpi` | Repositório da UFPI | Endereço **não confirmado**; localizar o repositório institucional da UFPI e testar `Identify` |
| `uespi` | Repositório da UESPI | A Resolução CEPEX 034/2024 instituiu o repositório, mas não informa o endereço; localizar e testar `Identify`. Pode ser que o repositório **não** exponha OAI-PMH: nesse caso a fonte fica `enabled: false` e o caso é registrado como limitação (não implementar raspagem para suprir isso sem autorização do desenvolvedor) |

---

## 6. CONTRATOS COMPARTILHADOS (USADOS POR VÁRIAS OS)

### 6.1 Fatos verificados sobre as fontes (consultados em 07/10/2026)

**OpenAlex** (`https://api.openalex.org`)
- Chave **gratuita** passada como parâmetro `api_key=`. A documentação atual descreve um orçamento diário: sem chave é muito pequeno (US$ 0,10/dia) e com chave gratuita é maior (US$ 1,00/dia); **busca textual custa 10 vezes mais que filtro** (US$ 1,00 por 1.000 chamadas contra US$ 0,10). Erros de limite: **HTTP 429** (e **409** foi citado em comunicado da lista de usuários para chamadas sem chave). `[VERIFICAR]` os valores vigentes em `https://developers.openalex.org/api-reference/authentication` antes de fixar números no código.
- Busca: `search=termo` (também `search.title`, `search.title_and_abstract`). Filtro: `filter=...` (exemplo da documentação: `publication_year:2024,is_oa:true`). `[VERIFICAR]` a sintaxe de intervalo de anos (ex.: `publication_year:2020-2024`) e do filtro `type:`.
- Paginação: padrão 25 por página, **máximo 100** por página. `[VERIFICAR]` o teto de paginação básica (`page`).
- Campos do objeto *work* confirmados: `id` (URI), `doi`, `title`/`display_name`, `publication_year`, `publication_date`, `type`, `language` (ISO 639-1), `authorships`, `abstract_inverted_index` (**índice invertido: cada palavra mapeada às suas posições; o resumo precisa ser reconstruído**), `primary_location`, `open_access.is_oa`, `open_access.oa_url`, `keywords`, `ids`. `[VERIFICAR]` em fixture real: `authorships[].author.display_name`, `authorships[].author.orcid`, `primary_location.landing_page_url`.

**CORE** (`https://api.core.ac.uk/v3`)
- **Chave gratuita obrigatória**, enviada em `Authorization: Bearer <chave>` (registro em `https://core.ac.uk/services/api`). Sem chave registrada o limite é de **1 requisição em lote ou 5 simples a cada 10 segundos**; com chave, limites maiores.
- Busca: `GET /v3/search/works/` com `q`, `limit`, `offset` e `sort` (ex.: `relevance`). Campos lidos por clientes existentes: `id`, `title`, `authors[].name`, `abstract`, `doi`, `downloadUrl`, `sourceFulltextUrls`, `documentType`, `publishedDate`, `depositedDate`, `journals[].title`.
- `[VERIFICAR]` em fixture real: nome do campo de ano (`yearPublished`?), sintaxe de filtro por ano e por tipo dentro de `q` (ex.: `yearPublished>=2020`), valores possíveis de `documentType`, campo de idioma, valor máximo de `limit`, e se existe `sort` por data.

**SciELO** (OAI-PMH)
- Verbs implementados pelo OAI-PMH do SciELO: `Identify`, `ListIdentifiers`, `ListSets` (um *set* por periódico, `setSpec` = ISSN), `ListRecords`, `GetRecord`. O formato obrigatório do protocolo é `oai_dc` (Lagoze et al., 2002).
- O endereço do Brasil **não foi confirmado**; sites do SciELO baseados no mesmo software expõem `/oai/` (ex.: `https://www.scielo.org.za/oai/`). `[VERIFICAR]` com `?verb=Identify` em `https://www.scielo.br/oai/` e registre a URL real em `docs/DECISOES.md`.
- `[VERIFICAR]` quantidade de registros por página, formato do `resumptionToken`, e como o `dc:identifier` expõe o endereço do artigo e o DOI.

**BDTD, UFPI e UESPI** (repositórios institucionais)
- Fato confirmado em fonte: a BDTD é criada e mantida pelo IBICT, foi lançada oficialmente em 2002, tem os dados colhidos por OAI-PMH e adota o padrão MTD-BR3 (28 metadados, 18 obrigatórios) (Almeida e Dias, 2023). Os repositórios de teses e dissertações costumam usar DSpace/TEDE2 (mesma fonte).
- Fato confirmado em fonte: a UESPI instituiu o repositório institucional de trabalhos acadêmicos pela Resolução CEPEX 034/2024, gerenciado pela Biblioteca Central; o aluno deposita o PDF pelo SIGAA.
- **Não confirmado:** endereço OAI-PMH de cada um, uso de `oai_dc`, quais `set`s existem, formato de `dc:identifier`, `dc:type`, `dc:language`, `dc:date` e se há DOI. `[VERIFICAR]` tudo isso com `Identify`, `ListSets` e `ListRecords` (uma página) e **grave a resposta como fixture** em `tests/fixtures/oai/<slug>/`.
- Muitos registros institucionais não trazem resumo, ano ou DOI: o normalizador deve aceitar `abstract`, `year` e `doi` nulos.

### 6.2 Esquema unificado `Record` (resposta pública da API)

Campos em inglês, `snake_case`, JSON. Todos os conectores devolvem **exatamente** este modelo (classe Pydantic `RecordOut`).

| Campo | Tipo | Regra |
|---|---|---|
| `id` | string | Identificador **interno estável**: `doi:<doi normalizado>` se houver DOI; senão `src:<fonte>:<id na fonte>` |
| `title` | string | Obrigatório. Sem tags HTML. Espaços normalizados |
| `authors` | lista de `{name: string, orcid: string \| null}` | Pode ser vazia. `name` na forma "Nome Sobrenome" quando possível; manter como veio se ambíguo |
| `abstract` | string \| null | Sem tags HTML. Texto reconstruído no caso do OpenAlex |
| `year` | int \| null | Ano de publicação (1000–2100) |
| `doi` | string \| null | Normalizado: minúsculas, sem prefixo `https://doi.org/` nem `doi:` |
| `url` | string \| null | Página do trabalho (landing page) ou, na falta, o link de acesso aberto. Só `http`/`https` |
| `pdf_url` | string \| null | Link direto para o texto completo, se informado pela fonte. Só `http`/`https` |
| `type` | enum | `article`, `thesis`, `preprint`, `book`, `other` (ver 6.3) |
| `language` | string \| null | Código ISO 639-1 em minúsculas quando disponível |
| `keywords` | lista de strings | Pode ser vazia |
| `sources` | lista de `{source: "openalex" \| "core" \| <slug de fonte OAI de config/oai_sources.yml>, source_id: string, url: string \| null}` (valores iniciais: `openalex`, `core`, `scielo`, `bdtd`, `ufpi`, `uespi`) | Todas as fontes em que o trabalho foi encontrado (após a deduplicação) |
| `is_favorite` | bool | Só preenchido quando há usuário autenticado; senão `false` |

### 6.3 Enumeração `type` e mapeamento por fonte

| Valor | Significado |
|---|---|
| `article` | Artigo de periódico |
| `thesis` | Tese ou dissertação |
| `preprint` | Preprint |
| `book` | Livro ou capítulo |
| `other` | Qualquer outro tipo, ou tipo desconhecido |

| Fonte | Regra inicial (`[VERIFICAR]` com fixture real) |
|---|---|
| OpenAlex | `article`→`article`; `dissertation`→`thesis`; `preprint`→`preprint`; `book`, `book-chapter`→`book`; demais→`other` |
| CORE | `documentType`: `thesis`→`thesis`; `research`/`journal`/`article`→`article`; `book`→`book`; demais→`other` |
| SciELO | `dc:type`: se indicar artigo/`journal article` → `article`; ausente → `article` (o SciELO reúne periódicos); demais→`other` |
| BDTD | `default_type: thesis` (a BDTD reúne teses e dissertações); `dc:type` indicando tese ou dissertação → `thesis` |
| UFPI, UESPI | `dc:type` com tese/dissertação → `thesis`; artigo → `article`; livro/capítulo → `book`; **monografia/TCC e demais → `other`**; ausente → `other`. Ajustar `type_map` aos valores reais vistos na fixture |

Toda regra de mapeamento fica numa **tabela de constantes** no código e é coberta por teste parametrizado.

### 6.4 Contrato de busca (`GET /api/v1/search`)

**Parâmetros de consulta**

| Nome | Tipo | Padrão | Regra |
|---|---|---|---|
| `q` | string | — | Obrigatório. 2 a 200 caracteres após remover espaços nas pontas |
| `sources` | lista (vírgulas) | todas | Subconjunto de `openalex,core,scielo,bdtd,ufpi,uespi` (na prática: os slugs habilitados) |
| `year_from`, `year_to` | int | — | 1900 a ano atual + 1. `year_from` ≤ `year_to` |
| `type` | lista (vírgulas) | todos | Subconjunto de `article,thesis,preprint,book,other` |
| `page` | int | `1` | ≥ 1 |
| `page_size` | int | `20` | 1 a `MAX_PAGE_SIZE` |
| `sort` | enum | `relevance` | `relevance` ou `year_desc` |

**Resposta (200)**

```json
{
  "query": "string",
  "page": 1,
  "page_size": 20,
  "total_estimated": 0,
  "total_is_estimate": true,
  "results": [ /* Record */ ],
  "sources_status": {
    "openalex": {"status": "ok|timeout|error|disabled|rate_limited", "count": 0, "total": 0, "message": null},
    "core":     {"status": "ok", "count": 0, "total": 0, "message": null},
    "scielo":   {"status": "ok", "count": 0, "total": 0, "message": null},
    "bdtd":     {"status": "ok", "count": 0, "total": 0, "message": null},
    "ufpi":     {"status": "ok", "count": 0, "total": 0, "message": null},
    "uespi":    {"status": "ok", "count": 0, "total": 0, "message": null}
  }
}
```

**Regras**
- Cada fonte ativa recebe a página `page` com tamanho `ceil(page_size / k)`, `k` = número de fontes ativas e habilitadas (com chave configurada). Fonte sem chave fica `disabled` e **não** conta em `k`. Fonte OAI com `enabled: false` ou **sem nenhum registro colhido** também fica `disabled` (mensagem: "Fonte ainda não colhida").
- Resultado intercalado fonte a fonte (primeiro de cada, depois segundo de cada…), seguido de deduplicação (OS-011). Pode haver menos de `page_size` itens por causa de duplicatas.
- `sort=year_desc`: repassa à fonte quando ela suporta; senão ordena os itens da página e registra `message` em `sources_status`.
- Erro de validação: **422** no formato padrão de erro (6.5). Todas as fontes falharam: **502** com `sources_status` detalhado.

### 6.5 Formato padrão de erro

```json
{"error": {"code": "string_em_snake_case", "message": "Mensagem em português para o usuário", "details": [ {"field": "q", "issue": "..."} ]}}
```

`details` é opcional. Nunca devolver *stack trace*, SQL, caminhos de arquivo ou chaves.

### 6.6 Modelo de dados (resumo; detalhado na OS-004)

- `users`: `id` (UUID), `email` (único, minúsculas), `full_name`, `password_hash`, `consent_at`, `consent_policy_version`, `created_at`, `updated_at`, `last_login_at`, `is_active`.
- `favorites`: `id` (UUID), `user_id` (FK, `ON DELETE CASCADE`), `record_id` (texto, o `Record.id`), `record_snapshot` (JSONB com o `Record` no momento de salvar), `note` (texto, até 1000 caracteres), `created_at`. Único em (`user_id`, `record_id`).
- `search_history`: `id`, `user_id` (FK, `ON DELETE CASCADE`), `query`, `filters` (JSONB), `result_count_estimated`, `created_at`.
- `security_events`: `id`, `user_id` (nulo permitido, **sem FK rígida** para sobreviver à exclusão), `event_type`, `ip_hash`, `created_at`, `details` (JSONB sem dados pessoais). Registra login falho, bloqueio por limite, exclusão de conta, alteração de senha.
- `oai_records`: índice local de **todas** as fontes OAI-PMH (SciELO, BDTD, UFPI, UESPI), com coluna `source` (OS-004 e OS-009).
- `harvest_runs`: um registro por colheita (fonte, início, fim, registros lidos/gravados, erros) (OS-004 e OS-009).

---

## 7. MAPA DE RASTREABILIDADE (TCC → OS)

| Trecho do TCC | OS |
|---|---|
| Introdução: busca unificada em CORE, SciELO, OpenAlex, BDTD, UFPI e UESPI | OS-007, 008, 009, 010, 012, 016 |
| Introdução: filtros por ano e tipo | OS-012, 016, 023 |
| Introdução: favoritos | OS-004, 017, 025 |
| Introdução: exportação em formatos de gerenciadores de referências | OS-019, 025 |
| Introdução: API pública | OS-014 a 020, 034 |
| 2.1 e 2.2 repositórios institucionais, BDTD/MTD-BR3, Resolução CEPEX 034/2024, OAI-PMH, mapeamento semântico, consolidação | OS-005, 009, 010, 011, 012 |
| 2.2 raspagem como complemento | OS-013 |
| 2.3 REST e JSON | OS-014, 016, 034 |
| 2.4 Python, FastAPI, PostgreSQL, HTML5/CSS3/JS | OS-001 a 004, 014, 021 |
| 2.5 responsividade, usabilidade, acessibilidade, tags/organização | OS-021 a 026, 031, 032 |
| 2.6 LGPD (arts. 6º, 18, 46) | OS-004, 015, 020, 024, 026, 027 |
| 2.6 OWASP (2017) e análise estática multiferramenta | OS-027, 028, 029 |
| 3 Delineamento: prototipação incremental com validação a cada etapa | todas (relatório por OS) |
| 4.1 a 4.6 Resultados e Discussões | OS-032, 033, 035 |
| 5 Conclusões: trabalhos futuros (inclui repositórios de outras universidades) | seção 3 deste arquivo |

### 7.1 Fatia 1 — caminho rápido para as capturas da seção 4.1

Serve a um objetivo só: **ter telas reais, com dados reais, antes de o sistema inteiro existir**. Não substitui nenhuma OS e não autoriza pular nada: é a execução das mesmas OS com um **subconjunto reduzido de critérios de aceite**, marcado no relatório para ser completado depois.

**Ordem da Fatia 1 (nesta sequência):** OS-001 → OS-002 → OS-005 → OS-006 → OS-007 → **OS-014r** → **OS-016r** → OS-021 → OS-022 → OS-023 → capturas.

**Não precisa de PostgreSQL nem de colheita.** A Fatia 1 não toca o banco, então as OS-003, 004, 009, 010, 015, 017, 018, 019 e 020 ficam para depois.

**OS-014r (reduzida):** faça a OS-014 inteira, com uma exceção: sem banco configurado, `GET /api/v1/health` responde `{"status":"ok","database":"nao_configurado"}` e **não** tenta conectar. Os cabeçalhos de segurança, a CORS restrita, o OpenAPI e o `StaticFiles` valem como escritos. Critério de aceite suspenso: o do banco em `health`.

**OS-016r (reduzida):** faça `GET /api/v1/search` e `GET /api/v1/sources` com os parâmetros de 6.4, **sem** `get_optional_user` e **sem** gravação de histórico (o ponto de chamada fica comentado com `# OS-018`). `is_favorite` sai sempre `false`. As fontes ativas são as que tiverem chave: OpenAlex e, se a chave já existir, CORE. As fontes OAI aparecem em `sources_status` como `disabled` com a mensagem "Fonte ainda não colhida" — **isso é verdade e deve aparecer na captura**. Critérios de aceite suspensos: os que dependem de usuário autenticado.

**OS-021, OS-022 e OS-023:** completas, como escritas. O botão de favorito da OS-022 fica **visível e desabilitado**, com o texto "Entre para salvar" e `aria-disabled="true"`; não crie tela de login falsa.

**Capturas que a Fatia 1 entrega** (todas com dados reais do OpenAlex, nomeadas conforme a OS-032):

| Captura | Como obter |
|---|---|
| `4.1-01-busca-vazia` | abrir a página inicial |
| `4.1-02-resultados` | buscar um termo do seu curso |
| `4.1-03-filtros-abertos` | abrir o painel de filtros |
| `4.1-04-filtros-ativos` | aplicar ano e tipo |
| `4.1-05-sem-resultados` | buscar um termo sem retorno |
| `4.1-06-fontes-parciais` | a própria lista de fontes, com as OAI em "ainda não colhida" |
| `4.1-07-api-docs` | abrir `/api/docs` |
| `4.4-01` a `4.4-03` | as mesmas telas em 320 px, 768 px e 1280 px |

**Capturas que a Fatia 1 NÃO entrega** (dependem das OS adiadas, não as simule): favoritos, anotação, seleção para exportar, arquivo exportado, cadastro com consentimento, login, minha conta, excluir conta, política de privacidade e histórico.

**Proibido na Fatia 1:** preencher a tela com resultados inventados; tirar captura de botão que não funciona como se funcionasse; escrever na seção 4 que o sistema tem favoritos ou login antes de a OS correspondente estar feita; declarar número de resultados por fonte como cobertura.

**Ao terminar a Fatia 1,** registre em `docs/os/FATIA-1-relatorio.md`: quais critérios de aceite ficaram suspensos, de qual OS, e o que falta para fechá-los. Nenhuma OS da Fatia 1 é considerada concluída até os critérios suspensos passarem.

---

# 8. ORDENS DE SERVIÇO

**Legenda das fases:** F0 Fundação · F1 Domínio e integração · F2 API · F3 Frontend · F4 Segurança · F5 Qualidade · F6 Entrega.
**Ordem de execução:** numérica. Não pule OS. Cada OS termina com relatório e commit (seção 0.1).
**Convenção de commit:** `feat(os-XXX): resumo` (ou `chore`, `test`, `docs`), em português, imperativo.

---

# FASE 0 — FUNDAÇÃO

## OS-001 — Repositório, ambiente e ferramentas de qualidade

**Depende de:** nenhuma.
**Rastreabilidade no TCC:** 2.4 (Python, FastAPI, PostgreSQL); 3 (prototipação incremental com validação a cada etapa).

**Objetivo:** criar o repositório com a estrutura de 5.3, o ambiente Python e as ferramentas de qualidade, de modo que toda OS seguinte tenha onde rodar lint, tipos e testes.

**Decisões já tomadas:** nome do projeto `academic-search-hub`; gerenciador de dependências livre (`pip` + `venv` ou `uv`), desde que gere o arquivo de versões travadas; Python 3.11+.

**Tarefas**
1. Criar a estrutura de pastas de 5.3 (pastas vazias com `.gitkeep` onde preciso).
2. Criar `pyproject.toml` com metadados, dependências de execução e de desenvolvimento (seção 4) e as configurações de `ruff`, `mypy` (modo estrito nos módulos de `app/`) e `pytest` (`asyncio_mode = "auto"`, marcadores `unit`, `integration`, `contract`, `e2e`, `a11y`).
3. Criar `.gitignore` (inclui `.env`, `.venv`, `__pycache__`, `.mypy_cache`, `.ruff_cache`, `htmlcov`, `*.egg-info`, `docs/evidencias/tmp/`).
4. Criar `.env.example` com **todas** as variáveis de 5.4 e comentário de uma linha em cada.
5. Criar `README.md` mínimo (o que é, pré-requisitos, comandos `make`/script para instalar, lintar, testar). A versão final vem na OS-034.
6. Criar um `Makefile` (ou `tasks.py`) com os alvos: `install`, `lint`, `format`, `typecheck`, `test`, `run`, `check` (lint + typecheck + test).
7. Criar `docs/DECISOES.md` com o modelo de entrada: data, OS, decisão, motivo, impacto.
8. Criar `docs/os/` e o modelo `docs/os/_modelo-relatorio.md` com os campos do passo 6 da seção 0.1.
9. Teste de fumaça: `tests/unit/test_smoke.py` com um teste trivial.
10. `git init`, primeiro commit.

**Arquivos:** `pyproject.toml`, `requirements.lock`, `.gitignore`, `.env.example`, `Makefile`, `README.md`, `docs/DECISOES.md`, `docs/os/_modelo-relatorio.md`, `tests/unit/test_smoke.py`, pastas de 5.3.

**Especificação detalhada**
- `ruff`: regras `E, F, I, B, UP, S, ASYNC, SIM, RUF`; `S` (bandit) fica ativo e as exceções em `tests/` são declaradas por `per-file-ignores`.
- `mypy`: `strict = true` para `app/`; `ignore_missing_imports` só para bibliotecas sem tipos, uma por uma, comentada.
- `pytest`: `--strict-markers`, cobertura com `pytest-cov` gerando `htmlcov/` e `coverage.xml`, **sem limiar mínimo ainda** (a OS-030 fixa).
- O `requirements.lock` deve ser gerado por comando (não escrito à mão).

**Critérios de aceite**
- [ ] `make install` cria o ambiente do zero sem erro.
- [ ] `make check` passa (ruff, ruff format, mypy, pytest).
- [ ] `.env` está no `.gitignore` e `.env.example` não contém segredo.
- [ ] A árvore de pastas confere com 5.3.
- [ ] `docs/DECISOES.md` e o modelo de relatório existem.

**Testes obrigatórios:** o teste de fumaça.
**Proibido nesta OS:** adicionar dependência fora da seção 4; criar código de aplicação além do necessário.
**Evidência para o TCC:** saída de `make check` e árvore de pastas (`tree -L 2`) em `docs/evidencias/os-001.txt`.
**Commit:** `chore(os-001): estrutura do projeto e ferramentas de qualidade`

---

## OS-002 — Configuração, logging e tratamento de erros

**Depende de:** OS-001.
**Rastreabilidade no TCC:** 2.4 (FastAPI, validação); 2.6 (LGPD art. 46; OWASP A3 e A10: não expor dados sensíveis e registrar eventos).

**Objetivo:** ter uma configuração central validada, logs estruturados sem dados pessoais e um formato único de erro.

**Decisões já tomadas:** `pydantic-settings` lê o `.env`; logs em JSON no stdout; erros no formato de 6.5.

**Tarefas**
1. `app/core/config.py`: classe `Settings` com todas as variáveis de 5.4, tipos e validações (ex.: `SECRET_KEY` com no mínimo 32 caracteres fora de `development`; `ALLOWED_ORIGINS` lista; `MAX_PAGE_SIZE` ≥ `DEFAULT_PAGE_SIZE`). Função `get_settings()` com cache.
2. `app/core/logging.py`: configurar `logging` com formatador JSON (`timestamp`, `level`, `logger`, `message`, `request_id` quando existir). Um filtro **remove/mascara** campos sensíveis (`password`, `token`, `authorization`, `api_key`, `secret`).
3. `app/core/errors.py`: hierarquia `AppError(code, message, status_code, details)` e subclasses `NotFoundError`, `ConflictError`, `AuthError`, `ForbiddenError`, `ValidationAppError`, `UpstreamError`, `RateLimitedError`. Função que converte qualquer `AppError` e `RequestValidationError` do FastAPI no formato 6.5.
4. Registrar um tratador genérico para exceções não previstas: resposta 500 com `code="internal_error"` e mensagem genérica; o detalhe vai só para o log.
5. Middleware de `request_id` (gera UUID, devolve em `X-Request-ID`, entra nos logs).

**Arquivos:** `app/core/config.py`, `app/core/logging.py`, `app/core/errors.py`, `app/core/middleware.py`, `tests/unit/test_config.py`, `tests/unit/test_errors.py`, `tests/unit/test_logging.py`.

**Especificação detalhada**
- A aplicação **não inicia** se faltar variável obrigatória; a mensagem de erro cita o **nome** da variável, nunca o valor.
- Em `APP_ENV=production`, `ALLOWED_ORIGINS` não pode conter `*`.
- O IP do cliente nunca é logado em claro: usar hash com sal derivado de `SECRET_KEY` (função `hash_ip` em `app/core/security.py`, criada aqui e reutilizada na OS-029).

**Critérios de aceite**
- [ ] Teste prova que um `password=abc` e um `Authorization: Bearer xyz` passados ao logger saem mascarados.
- [ ] Teste prova que uma exceção qualquer vira 500 genérico sem *stack trace* no corpo.
- [ ] Teste prova que a falta de `SECRET_KEY` em produção impede a inicialização.
- [ ] Toda resposta de erro tem o formato 6.5.

**Testes obrigatórios:** os quatro acima, mais validação de `ALLOWED_ORIGINS`.
**Proibido nesta OS:** logar corpo de requisição; usar `print`.
**Evidência para o TCC:** exemplo de linha de log e de resposta de erro em `docs/evidencias/os-002.md` (útil para 4.6).
**Commit:** `feat(os-002): configuração, logging estruturado e erros padronizados`

---

## OS-003 — PostgreSQL, sessão assíncrona e Alembic

**Depende de:** OS-002.
**Rastreabilidade no TCC:** 2.4 (PostgreSQL; Stonebraker e Kemnitz, 1991); 3.

**Objetivo:** conectar ao PostgreSQL de forma assíncrona e ter migrações versionadas.

**Decisões já tomadas:** SQLAlchemy 2.x assíncrono com `psycopg` 3; Alembic com *autogenerate* revisado à mão; extensões `unaccent` e `pg_trgm`.

**Tarefas**
1. `app/db/session.py`: `engine` assíncrono, `async_sessionmaker`, dependência `get_session()` do FastAPI (commit/rollback explícitos).
2. `app/db/base.py`: `DeclarativeBase` com convenção de nomes de índices e restrições (para migrações estáveis).
3. Configurar o Alembic (`alembic.ini`, `migrations/env.py`) para ler `DATABASE_URL` do `Settings` e rodar em modo assíncrono.
4. Migração `0001_extensoes`: `CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS pgcrypto;`.
5. Migração `0001` também cria a função **`immutable_unaccent(text)`** (wrapper `IMMUTABLE` de `unaccent`, necessário para usar em índice) e uma configuração de busca de texto `pt_unaccent` (`CREATE TEXT SEARCH CONFIGURATION ... COPY = portuguese` com mapeamento via `unaccent`). Documentar em `DECISOES.md` por que isso é necessário.
6. Documentar em `docs/EXECUCAO.md` como criar o banco local (comandos `createdb`, usuário sem privilégio de superusuário para a aplicação).
7. Rota/rotina de verificação de banco: função `check_database()` que executa `SELECT 1` (usada na OS-014).

**Arquivos:** `app/db/session.py`, `app/db/base.py`, `alembic.ini`, `migrations/env.py`, `migrations/versions/0001_extensoes.py`, `docs/EXECUCAO.md`, `tests/integration/test_db_connection.py`.

**Especificação detalhada**
- Os testes de integração com banco usam um PostgreSQL **de teste** definido por `TEST_DATABASE_URL`; se a variável não existir, esses testes são **pulados** com mensagem clara (regra 9: sem rede externa, mas banco local é permitido).
- A criação das extensões exige privilégio; descrever em `EXECUCAO.md` que é um passo único feito por superusuário.

**Critérios de aceite**
- [ ] `alembic upgrade head` e `alembic downgrade base` funcionam em banco vazio.
- [ ] `SELECT immutable_unaccent('Ação')` devolve `Acao`.
- [ ] `to_tsvector('pt_unaccent', 'Educação básica')` casa com `to_tsquery('pt_unaccent','educacao')`.
- [ ] Sem `TEST_DATABASE_URL`, os testes de banco são pulados, não falham.

**Testes obrigatórios:** conexão, `immutable_unaccent`, `pt_unaccent`, subida e descida da migração.
**Proibido nesta OS:** criar tabelas de domínio (vêm na OS-004); usar driver síncrono.
**Evidência para o TCC:** trecho de `EXECUCAO.md` com a criação do banco e saída de `alembic upgrade head`.
**Commit:** `feat(os-003): conexão assíncrona com PostgreSQL e migrações`

---

## OS-004 — Modelos de dados e migração inicial

**Depende de:** OS-003.
**Rastreabilidade no TCC:** 2.6 (LGPD: necessidade, art. 6º III; direitos do art. 18); Introdução (favoritos, histórico); 2.2 (índice local de metadados).

**Objetivo:** criar os modelos e a migração das tabelas de 6.6.

**Decisões já tomadas:** UUID como chave (`gen_random_uuid()`); minimização de dados (só e-mail, nome e hash de senha); `security_events` sem FK rígida; índice local único `oai_records` para todas as fontes OAI-PMH.

**Tarefas**
1. Modelos SQLAlchemy em `app/models/`: `User`, `Favorite`, `SearchHistory`, `SecurityEvent`, `OaiRecord`, `HarvestRun`.
2. Migração `0002_tabelas_dominio` revisada à mão.
3. Índices e restrições (abaixo).
4. Fábricas de teste (funções simples) em `tests/factories.py`.

**Arquivos:** `app/models/*.py`, `migrations/versions/0002_tabelas_dominio.py`, `tests/integration/test_models.py`, `tests/factories.py`.

**Especificação detalhada**
- `users`: conforme 6.6. `email` único em minúsculas (restrição `CHECK (email = lower(email))`). `consent_at` e `consent_policy_version` **não nulos**. Sem campos extras (nada de telefone, CPF, data de nascimento).
- `favorites`: único (`user_id`,`record_id`); `note` com `CHECK (char_length(note) <= 1000)`; índice em (`user_id`,`created_at` desc).
- `search_history`: índice em (`user_id`,`created_at` desc); `query` até 200 caracteres.
- `security_events`: `event_type` com `CHECK` em lista fechada (`login_failed`, `login_success`, `rate_limited`, `account_deleted`, `password_changed`, `data_exported`, `account_registered`); `ip_hash` texto; sem e-mail em `details`.
- `oai_records`: colunas `id` (UUID), `source` (texto, slug), `oai_identifier` (texto), `datestamp` (timestamptz), `deleted` (bool), `title`, `authors` (JSONB), `abstract`, `year` (int nulo), `doi` (nulo), `url` (nulo), `pdf_url` (nulo), `type` (enum de 6.3), `language` (nulo), `keywords` (JSONB), `raw_types` (JSONB, valores originais de `dc:type`), `search_vector` (`tsvector`, **coluna gerada** ou mantida por *trigger*, usando `to_tsvector('pt_unaccent', title || ' ' || coalesce(abstract,'') || ' ' || keywords_text)`, com **peso A para título, B para palavras-chave e C para resumo**), `harvested_at`. Único em (`source`,`oai_identifier`). Índice **GIN** em `search_vector`; índices em (`source`), (`year`), (`type`).
- `harvest_runs`: `id`, `source`, `started_at`, `finished_at`, `status` (`running|ok|error|partial`), `records_read`, `records_upserted`, `records_deleted`, `last_resumption_token` (nulo), `error_message` (nulo, sem dados sensíveis).
- Chaves estrangeiras de `favorites` e `search_history` com `ON DELETE CASCADE` (exclusão da conta apaga tudo, art. 18 da LGPD).

**Critérios de aceite**
- [ ] `alembic upgrade head` cria as seis tabelas e `downgrade` as remove.
- [ ] Inserir dois favoritos iguais para o mesmo usuário falha por restrição única.
- [ ] Excluir um usuário apaga seus favoritos e histórico (teste), mas **mantém** os `security_events`.
- [ ] E-mail com maiúscula é rejeitado pelo banco.
- [ ] Busca `to_tsquery('pt_unaccent','educacao')` encontra um `oai_records` com título "Educação" (teste com `EXPLAIN` mostrando uso do índice GIN **quando a tabela tiver volume suficiente**; em tabela pequena apenas conferir o resultado).

**Testes obrigatórios:** restrições, cascata, `security_events` sobrevivendo, `search_vector`.
**Proibido nesta OS:** colunas além das listadas; guardar IP em claro.
**Evidência para o TCC:** diagrama entidade-relacionamento (gerar em Mermaid `erDiagram` em `docs/evidencias/os-004-er.md`) para 4.3 e 4.6.
**Commit:** `feat(os-004): modelos, migração inicial e índice local OAI`

---

# FASE 1 — DOMÍNIO E INTEGRAÇÃO

## OS-005 — Esquema unificado e normalização

**Depende de:** OS-004.
**Rastreabilidade no TCC:** 2.2 (Chan e Zeng, 2006: mapeamento semântico entre campos; Zeng e Chan, 2006: conversão e consolidação); 4.2.

**Objetivo:** implementar o `Record` de 6.2 e as funções puras de normalização usadas por todos os conectores.

**Decisões já tomadas:** funções puras e testáveis; nenhum acesso a rede ou banco nesta OS.

**Tarefas**
1. `app/schemas/record.py`: `AuthorOut`, `SourceRef`, `RecordOut` (Pydantic v2), com validadores conforme 6.2 (`http`/`https` só; ano 1000–2100; etc.).
2. `app/services/normalize.py` com as funções:
   - `normalize_doi(value) -> str | None` (aceita `https://doi.org/10.x/y`, `http://dx.doi.org/...`, `doi:10.x/y`, espaços; devolve minúsculas; descarta se não começar por `10.`).
   - `clean_text(value) -> str` (remove tags HTML, decodifica entidades, colapsa espaços e quebras).
   - `normalize_title(value) -> str` (para comparação: minúsculas, sem acento, sem pontuação, sem espaços duplicados).
   - `parse_year(value) -> int | None` (aceita `2021`, `2021-05-03`, `2021-05`, texto com ano no meio; fora de 1000–2100 → `None`).
   - `normalize_author(name) -> AuthorOut` (aceita "Sobrenome, Nome" e "Nome Sobrenome"; mantém como veio se ambíguo; remove espaços extras).
   - `surname(author_name) -> str` (para a regra de deduplicação).
   - `normalize_language(value) -> str | None` (ISO 639-3 `por`→`pt`, `eng`→`en`, `spa`→`es`, `pt-BR`→`pt`; desconhecido → `None`).
   - `safe_url(value) -> str | None` (só `http`/`https`; descarta `javascript:` e similares).
   - `build_record_id(doi, source, source_id) -> str` (regra de 6.2).
3. `app/services/type_mapping.py`: tabelas de constantes de 6.3 (OpenAlex, CORE) e função genérica `map_oai_type(raw_types, type_map, default_type)` para as fontes OAI (compara sem acento e minúsculas).

**Arquivos:** `app/schemas/record.py`, `app/services/normalize.py`, `app/services/type_mapping.py`, `tests/unit/test_normalize.py`, `tests/unit/test_type_mapping.py`, `tests/unit/test_record_schema.py`.

**Especificação detalhada**
- Casos de borda obrigatórios nos testes (parametrizados): DOI com maiúsculas e espaço final; URL com `javascript:`; título com `<i>`; ano `"[2019]"`; nome `"SILVA, João P."`; resumo com `&amp;`; `dc:type` `"Dissertação"` e `"info:eu-repo/semantics/doctoralThesis"` (este último → `thesis`); lista vazia de `raw_types` → `default_type`.
- `map_oai_type` reconhece os prefixos `info:eu-repo/semantics/` mais comuns (`article`, `doctoralThesis`, `masterThesis`, `bachelorThesis`, `book`, `bookPart`, `preprint`, `report`, `conferenceObject`). Para `bachelorThesis` use `other` (monografia/TCC; ver 6.3). `[VERIFICAR]` com as fixtures reais.

**Critérios de aceite**
- [ ] `RecordOut` rejeita `url="javascript:alert(1)"`.
- [ ] Todos os casos de borda acima passam.
- [ ] `build_record_id` devolve `doi:10.1000/x` quando há DOI e `src:bdtd:abc` quando não há.
- [ ] Cobertura de `normalize.py` e `type_mapping.py` ≥ 95%.

**Testes obrigatórios:** os parametrizados acima.
**Proibido nesta OS:** chamar rede ou banco; criar classes de conector.
**Evidência para o TCC:** tabela "campo da fonte → campo unificado" (gerar em `docs/evidencias/os-005-mapeamento.md`; completar nas OS 007 a 010) para 4.2.
**Commit:** `feat(os-005): esquema unificado Record e funções de normalização`

---

## OS-006 — Contrato de conectores e cliente HTTP resiliente

**Depende de:** OS-005.
**Rastreabilidade no TCC:** 2.2 (interoperabilidade); 3 (interfaces testadas); 2.6 (OWASP A10: registro).

**Objetivo:** definir a interface comum de todas as fontes e um cliente HTTP com tempo limite, tentativas e identificação.

**Decisões já tomadas:** conectores assíncronos; falha de fonte é convertida em estado (`timeout`, `error`, `rate_limited`), nunca em exceção que derrube a busca.

**Tarefas**
1. `app/connectors/base.py`:
   - `SourceQuery` (dataclass/Pydantic): `q`, `page`, `page_size`, `year_from`, `year_to`, `types`, `sort`.
   - `SourcePage`: `records: list[RecordOut]`, `total: int | None`, `status`, `message`.
   - `class Connector(Protocol)` com `slug: str`, `name: str`, `is_enabled() -> bool`, `async search(query: SourceQuery) -> SourcePage`.
   - Enumeração `SourceStatus`: `ok`, `timeout`, `error`, `disabled`, `rate_limited`.
2. `app/connectors/http.py`: função/fábrica `make_client(settings)` com `httpx.AsyncClient`, `timeout=SOURCE_TIMEOUT_SECONDS`, `User-Agent: AcademicSearchHub/<versão> (+contato: CONTACT_EMAIL)`, limite de conexões, `follow_redirects=True` com no máximo 3 redirecionamentos.
3. Função `get_json(client, url, params, headers)` que: faz até **2 novas tentativas** (backoff exponencial curto) **só** para erros de rede, timeout e HTTP 502/503/504; **nunca** repete em 4xx; converte 429 em `RateLimitedError` (lendo `Retry-After` se vier); limita o tamanho da resposta (ex.: 5 MB) e levanta erro se passar.
4. Registrar em log (sem chaves) a URL base, o status e a duração de cada chamada externa.
5. `app/connectors/registry.py`: monta a lista de conectores a partir de `Settings` e do arquivo de fontes OAI (a OS-010 completa a parte OAI).

**Arquivos:** `app/connectors/base.py`, `app/connectors/http.py`, `app/connectors/registry.py`, `tests/unit/test_http_client.py`.

**Especificação detalhada**
- A chave de API **nunca** vai na URL registrada em log. Para o OpenAlex, que usa parâmetro `api_key`, o log deve mascarar o parâmetro.
- Testes com `respx`: sucesso; timeout; 503 seguido de 200 (uma tentativa extra); 404 sem nova tentativa; 429 com `Retry-After`; resposta maior que o limite.

**Critérios de aceite**
- [ ] Os seis cenários de `respx` passam.
- [ ] Nenhum teste faz chamada de rede real.
- [ ] O log de uma chamada com `api_key=SEGREDO` não contém `SEGREDO`.

**Testes obrigatórios:** os seis cenários e o mascaramento.
**Proibido nesta OS:** implementar conector de fonte real.
**Evidência para o TCC:** descrição do comportamento (tentativas, tempo limite) em `docs/evidencias/os-006.md`, para 4.2.
**Commit:** `feat(os-006): contrato de conectores e cliente HTTP resiliente`

---

## OS-007 — Conector OpenAlex

**Depende de:** OS-006.
**Rastreabilidade no TCC:** 2.2 (Priem, Piwowar e Orr, 2022); 4.2.

**Objetivo:** buscar no OpenAlex ao vivo e converter cada obra em `RecordOut`.

**Decisões já tomadas:** OpenAlex é consultado ao vivo (D1); a chave é gratuita e fica em `OPENALEX_API_KEY`; sem chave a fonte fica `disabled`.

**Tarefas**
1. **Passo manual 0 (desenvolvedor):** criar conta e chave gratuita; salvar uma resposta real de `GET https://api.openalex.org/works?search=educação&per-page=5&api_key=...` em `tests/fixtures/openalex/search_ok.json`. Se o desenvolvedor ainda não tiver a fixture, **construa uma fixture sintética fiel à documentação**, marque-a com `"_synthetic": true` no topo do arquivo de teste e registre pendência em `DECISOES.md`.
2. `app/connectors/openalex.py`: classe `OpenAlexConnector`.
3. Montagem da consulta: `search=<q>`, `per-page=<page_size do conector>`, `page=<page>`, `filter=` com `publication_year` e `type` conforme os filtros (usar a sintaxe confirmada; `[VERIFICAR]`), `sort=` quando `year_desc` (ex.: `publication_year:desc`, `[VERIFICAR]`).
4. Conversão `work → RecordOut`:
   - `title` ← `title` (ou `display_name`); `doi` ← `normalize_doi(doi)`; `year` ← `publication_year`.
   - `authors` ← `authorships[].author.display_name` (+ `orcid` quando existir, sem o prefixo de URL).
   - `abstract` ← `reconstruct_abstract(abstract_inverted_index)` (nulo se ausente).
   - `url` ← `primary_location.landing_page_url`, senão `doi` como URL (`https://doi.org/<doi>`), senão `open_access.oa_url`; `pdf_url` ← `primary_location.pdf_url` ou `best_oa_location.pdf_url`.
   - `type` ← tabela de 6.3; `language` ← `normalize_language(language)`; `keywords` ← `keywords[].display_name`.
   - `sources` ← `[{source:"openalex", source_id: <id curto, ex. W123>, url: <id URI>}]`.
5. `reconstruct_abstract`: ordenar as palavras pelas posições do índice invertido e juntar com espaço; tolerar posições faltantes; limite de segurança de 20.000 caracteres.
6. Total: `meta.count`.
7. Erros: 429 → `rate_limited`; 401/403 → `error` com mensagem "Chave do OpenAlex inválida ou sem permissão" (sem mostrar a chave); timeout → `timeout`.

**Arquivos:** `app/connectors/openalex.py`, `tests/unit/test_openalex_connector.py`, `tests/fixtures/openalex/*.json`.

**Especificação detalhada**
- Teste do índice invertido com um exemplo pequeno (`{"A":[0],"casa":[1,3],"bonita":[2]}` → "A casa bonita casa").
- Obra sem `doi`, sem resumo e sem autores deve resultar em `RecordOut` válido.
- `page_size` do conector pode ser até 100 (limite da fonte); acima disso, truncar e registrar `message`.

**Critérios de aceite**
- [ ] Com `respx` e a fixture, o conector devolve `RecordOut` válidos, com `total` igual a `meta.count`.
- [ ] Sem `OPENALEX_API_KEY`, `is_enabled()` é falso e `search` devolve `status=disabled`.
- [ ] 429 vira `rate_limited`; timeout vira `timeout`.
- [ ] Nenhum `RecordOut` tem `url` fora de `http/https`.
- [ ] A chave não aparece em log nem em mensagem.

**Testes obrigatórios:** os itens acima e o caso de obra mínima.
**Proibido nesta OS:** usar o resultado de busca para decidir cobertura ("OpenAlex cobre X%").
**Evidência para o TCC:** a linha do mapeamento (OS-005) preenchida para o OpenAlex; **passo manual do desenvolvedor**: uma busca real salva como captura em `docs/evidencias/os-007-busca-real.json` (sem a chave).
**Commit:** `feat(os-007): conector OpenAlex`

---

## OS-008 — Conector CORE

**Depende de:** OS-006.
**Rastreabilidade no TCC:** 2.2 (Knoth e Zdrahal, 2012); 4.2.

**Objetivo:** buscar no CORE ao vivo e converter cada resultado em `RecordOut`.

**Decisões já tomadas:** API v3, chave gratuita obrigatória em `Authorization: Bearer`; sem chave a fonte fica `disabled`.

**Tarefas**
1. **Passo manual 0:** criar chave em `https://core.ac.uk/services/api`; salvar resposta real de `GET /v3/search/works/?q=educação&limit=5` em `tests/fixtures/core/search_ok.json`. Sem fixture real, usar fixture sintética marcada e registrar pendência.
2. `app/connectors/core_api.py`: `CoreConnector`.
3. Consulta: `q=<q>` com filtros embutidos conforme a sintaxe confirmada (`[VERIFICAR]` ano e tipo), `limit`, `offset = (page-1) * limit`, `sort` se existir.
4. Conversão `result → RecordOut`:
   - `title`, `abstract` (limpar HTML), `doi` (normalizar), `authors[].name`, `year` ← campo de ano confirmado ou `parse_year(publishedDate)`.
   - `url` ← primeiro de: link de landing/`sourceFulltextUrls`/página CORE (`https://core.ac.uk/works/<id>`); `pdf_url` ← `downloadUrl`.
   - `type` ← tabela de 6.3 com `documentType`; `language` ← campo confirmado ou `null`.
   - `sources` ← `[{source:"core", source_id: str(id), url: página CORE}]`.
5. Total: `totalHits`.
6. Erros: 429 → `rate_limited` (respeitar `Retry-After` na mensagem); 401/403 → `error`; timeout → `timeout`.

**Arquivos:** `app/connectors/core_api.py`, `tests/unit/test_core_connector.py`, `tests/fixtures/core/*.json`.

**Especificação detalhada**
- O CORE pode devolver `authors` vazios ou com `name` nulo: descartar autores sem nome.
- Resultados sem `title` são **descartados** e contados em `message` ("N resultados sem título foram ignorados").
- Respeitar o limite de `limit` da fonte (`[VERIFICAR]`); truncar e registrar.

**Critérios de aceite**
- [ ] Com `respx` e a fixture, o conector devolve `RecordOut` válidos e o total correto.
- [ ] Sem chave, devolve `disabled`.
- [ ] 429 e timeout tratados.
- [ ] Resultado sem título é ignorado e contado.

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** raspar páginas do CORE.
**Evidência para o TCC:** linha do mapeamento (OS-005) para o CORE; busca real do desenvolvedor salva em `docs/evidencias/os-008-busca-real.json` (sem chave).
**Commit:** `feat(os-008): conector CORE`

---

## OS-009 — Colheita OAI-PMH multi-fonte (cliente, importador e CLI)

**Depende de:** OS-005, OS-006.
**Rastreabilidade no TCC:** 2.1 e 2.2 (Lagoze et al., 2002; Almeida e Dias, 2023: BDTD coletada por OAI-PMH, MTD-BR3); 3 (colheita e índice local); 4.2.

**Objetivo:** colher registros `oai_dc` de **qualquer fonte declarada em `config/oai_sources.yml`** (SciELO, BDTD, UFPI e UESPI) e gravá-los na tabela `oai_records`.

**Decisões já tomadas:** D2; um único cliente e um único importador para todas as fontes; a colheita é **CLI**, não rota; XML sempre com `defusedxml`; pausa entre requisições (`OAI_HARVEST_DELAY_SECONDS`) e `User-Agent` identificado.

**Tarefas**
1. `app/harvest/oai_sources.py`: carregar e validar `config/oai_sources.yml` (tabela de campos em 5.5). Criar o arquivo com as quatro entradas iniciais, **todas com `enabled: false` e URL como `TODO-VERIFICAR`**, até a validação manual (tarefa 8). Dependência `pyyaml` (registrar em `DECISOES.md`; é a única adição fora da seção 4 permitida aqui).
2. `app/harvest/oai_client.py`: cliente com `identify()`, `list_sets()`, `list_records(metadata_prefix, set_spec, from_date, until_date)` (gerador assíncrono que **segue o `resumptionToken`** até acabar) e `get_record(identifier)`.
3. Tratamento de erros do protocolo: `badResumptionToken`, `noRecordsMatch` (não é erro: devolve vazio), `cannotDisseminateFormat`, `badArgument`; resposta HTTP 503 com `Retry-After` (esperar e repetir, no máximo 3 vezes); XML malformado → erro claro.
4. `app/harvest/harvester.py`: função `harvest_source(slug, *, full: bool, limit: int | None)`:
   - cria um `harvest_runs` (`running`);
   - colheita **incremental** por padrão: usa a data do último `harvest_runs` com `ok` como `from`; `--full` ignora a data;
   - converte cada registro `oai_dc` em linha de `oai_records` (mapeamento abaixo);
   - **upsert** por (`source`,`oai_identifier`); cabeçalho `status="deleted"` marca `deleted=true`;
   - confirma em lotes (ex.: 500 linhas) para não perder tudo se falhar;
   - ao fim, atualiza o `harvest_runs` com contagens e `status` (`ok`, `partial` se houve registros ignorados, `error`).
5. Mapeamento `oai_dc → oai_records` (função pura `parse_oai_dc(record_xml, source_cfg) -> dict | None`):
   - `title` ← primeiro `dc:title` (`clean_text`); registro sem título → ignorado e contado.
   - `authors` ← cada `dc:creator` (`normalize_author`).
   - `abstract` ← `dc:description` mais longo (instituições costumam repetir em idiomas; guardar o mais longo; `clean_text`).
   - `year` ← `parse_year` do primeiro `dc:date` válido.
   - `doi` ← primeiro `dc:identifier`/`dc:relation` que contenha DOI (`normalize_doi`); `url` ← primeiro `dc:identifier` `http(s)` que **não** seja só o DOI e **não** termine em `.pdf`; se só houver DOI, `https://doi.org/<doi>`; `pdf_url` ← `dc:identifier`/`dc:relation` terminado em `.pdf` ou com `/bitstream/`.
   - `type` ← `map_oai_type(todos os dc:type, source_cfg.type_map, source_cfg.default_type)`; `raw_types` ← lista original.
   - `language` ← `normalize_language(dc:language)`; `keywords` ← `dc:subject` (sem duplicatas, sem vazios).
   - `[VERIFICAR]` com a fixture real de cada fonte e ajustar (as instituições variam muito); registrar os ajustes em `DECISOES.md`.
6. `app/harvest/cli.py` (executável por `python -m app.harvest.cli`):
   - `identify <slug>` imprime o resultado de `Identify` (para a validação);
   - `sets <slug>` lista os `set`s;
   - `run <slug> [--full] [--limit N] [--dry-run]`;
   - `run-all [--full]` roda todas as fontes `enabled`;
   - `status` mostra, por fonte, o último `harvest_runs` e a contagem de `oai_records`.
   - Código de saída diferente de zero em erro.
7. Cabeçalho `User-Agent` com `CONTACT_EMAIL`; **recusar** executar se `CONTACT_EMAIL` estiver vazio.
8. **Passo manual 0 (desenvolvedor), por fonte:** (a) descobrir o endereço OAI-PMH oficial; (b) `python -m app.harvest.cli identify <slug>`; (c) `sets <slug>`; (d) `run <slug> --limit 50 --dry-run` e salvar a resposta bruta de **uma página** em `tests/fixtures/oai/<slug>/list_records.xml` e de `Identify` em `identify.xml`; (e) preencher `base_url`, `set_spec`, `type_map` e `enabled: true` no YAML; (f) registrar em `DECISOES.md` (URL, versão do protocolo, formatos disponíveis, observações). **Se a fonte não expuser OAI-PMH, mantenha `enabled: false`, registre a limitação e avise o desenvolvedor.**

**Arquivos:** `config/oai_sources.yml`, `app/harvest/*.py`, `tests/unit/test_oai_client.py`, `tests/unit/test_parse_oai_dc.py`, `tests/integration/test_harvester.py`, `tests/fixtures/oai/<slug>/*.xml`.

**Especificação detalhada**
- `defusedxml` com `forbid_dtd=True`; nunca `xml.etree` direto.
- O gerador do `resumptionToken` deve ter **limite de páginas** de segurança (`--max-pages`, padrão alto) para evitar laço infinito.
- Fixtures sintéticas são permitidas **só como último recurso**, marcadas com comentário `<!-- SINTÉTICA -->` e registradas em `DECISOES.md`. Crie ao menos: `list_records_page1.xml` (com `resumptionToken`), `list_records_page2.xml` (sem token), `no_records_match.xml`, `bad_resumption_token.xml`, `deleted_record.xml`, `malicious_dtd.xml` (XML com entidade externa, para provar que é recusado).
- Registros em vários idiomas (`dc:title` repetido): usar o primeiro; `dc:description` o mais longo.

**Critérios de aceite**
- [ ] Teste de duas páginas com `resumptionToken` traz todos os registros.
- [ ] `noRecordsMatch` não é erro.
- [ ] O XML com DTD/entidade externa é **recusado** (teste).
- [ ] Rodar a colheita duas vezes **não duplica** linhas (upsert).
- [ ] Registro `deleted` marca `deleted=true` e some das buscas (OS-010).
- [ ] `run` sem `CONTACT_EMAIL` recusa executar.
- [ ] A CLI `status` mostra contagens por fonte.
- [ ] Nenhum teste usa rede real.

**Testes obrigatórios:** paginação por token, erros do protocolo, XXE, upsert, `deleted`, parsing de `oai_dc` com os casos: título repetido em dois idiomas, só DOI, só PDF, sem data, `dc:type` ausente.
**Proibido nesta OS:** criar rota de API para colher; raspar HTML de fonte que não exponha OAI-PMH.
**Evidência para o TCC:** saída de `identify` e `status` de cada fonte (editada para remover contato), tabela "fonte → URL OAI → total colhido" em `docs/evidencias/os-009-fontes.md` (para 4.2). **O total colhido é um fato medido: só escrever o que a CLI mostrar.**
**Commit:** `feat(os-009): colheita OAI-PMH multi-fonte para índice local`

---

## OS-010 — Conectores sobre o índice local (SciELO, BDTD, UFPI, UESPI)

**Depende de:** OS-004, OS-006, OS-009.
**Rastreabilidade no TCC:** 2.1 e 2.2; 3 (índice local no PostgreSQL); 4.2.

**Objetivo:** responder buscas das fontes OAI a partir de `oai_records`, com texto completo, filtros e ordenação.

**Decisões já tomadas:** uma classe `OaiLocalConnector(slug)` instanciada **uma vez por fonte habilitada** no arquivo YAML; busca com `websearch_to_tsquery('pt_unaccent', :q)`.

**Tarefas**
1. `app/connectors/oai_local.py`: `OaiLocalConnector(slug, name, session_factory)`.
2. Consulta SQL parametrizada (via SQLAlchemy Core/ORM, **sem** concatenar texto do usuário):
   - `WHERE source = :slug AND deleted = false AND search_vector @@ websearch_to_tsquery('pt_unaccent', :q)`;
   - filtro de ano: `year BETWEEN :from AND :to` (registros com `year` nulo **ficam de fora** quando há filtro de ano; documentar);
   - filtro de tipo: `type = ANY(:types)`;
   - ordenação `relevance`: `ts_rank_cd(search_vector, query)` desc, depois `year` desc nulos por último, depois `id`; `year_desc`: `year` desc nulos por último, depois relevância;
   - `LIMIT :limit OFFSET :offset`.
3. Total: `COUNT(*)` com os mesmos filtros (consulta separada). `[VERIFICAR]` desempenho com volume real; se a contagem for lenta, **registrar** a medição na OS-033 (não otimizar aqui).
4. Conversão `OaiRecord → RecordOut` (`sources=[{source: slug, source_id: oai_identifier, url}]`).
5. `is_enabled()`: fonte `enabled` no YAML **e** com ao menos um registro (`status=disabled` com mensagem "Fonte ainda não colhida" caso contrário).
6. Completar `app/connectors/registry.py` (OS-006): para cada fonte habilitada no YAML, registrar um `OaiLocalConnector`.
7. Termos vazios após `websearch_to_tsquery` (só *stop words*): devolver página vazia, `status=ok`, `message` explicativa.

**Arquivos:** `app/connectors/oai_local.py`, `app/connectors/registry.py`, `tests/integration/test_oai_local.py`.

**Especificação detalhada**
- Dados de teste: inserir via `tests/factories.py` registros de duas fontes diferentes (ex.: `bdtd` e `uespi`) e provar que a busca por `slug` **não mistura** fontes.
- Busca com acento e sem acento deve dar o mesmo resultado ("educação" e "educacao").
- Busca com aspas (`"ensino médio"`) e com `-termo` (exclusão) segue a semântica de `websearch_to_tsquery`.

**Critérios de aceite**
- [ ] A busca por "educacao" encontra "Educação".
- [ ] Filtros de ano e tipo funcionam; `deleted=true` nunca aparece.
- [ ] Duas fontes no mesmo banco não se misturam.
- [ ] Ordenação `year_desc` coloca nulos por último.
- [ ] Texto malicioso em `q` (`'; DROP TABLE users;--`) não causa erro de SQL (teste).
- [ ] Fonte sem registros devolve `disabled` com a mensagem.

**Testes obrigatórios:** os seis acima.
**Proibido nesta OS:** colher dados; usar `LIKE '%...%'` como busca principal.
**Evidência para o TCC:** exemplo de consulta SQL gerada e `EXPLAIN (ANALYZE)` de uma busca real após a colheita (medição do desenvolvedor), em `docs/evidencias/os-010-explain.txt`.
**Commit:** `feat(os-010): conectores de busca sobre o índice local OAI`

---

## OS-011 — Deduplicação

**Depende de:** OS-005.
**Rastreabilidade no TCC:** 2.2 (Zeng e Chan, 2006: consolidação de registros); 4.2.

**Objetivo:** reunir em um só `Record` os resultados repetidos vindos de fontes diferentes.

**Decisões já tomadas:** duas chaves, nesta ordem: (1) DOI normalizado; (2) título normalizado + ano + sobrenome do primeiro autor. Função pura.

**Tarefas**
1. `app/services/dedup.py`: `deduplicate(records: list[RecordOut]) -> list[RecordOut]`, **estável** (mantém a ordem da primeira ocorrência).
2. Regra de união ao detectar repetido: manter o primeiro como base; `sources` = união (sem repetir par fonte/id); `abstract` = o mais longo não nulo; `doi`, `year`, `language` = o primeiro não nulo; `url`/`pdf_url` = o primeiro não nulo; `authors` = a lista mais completa (mais itens; em empate, a que tem ORCID); `keywords` = união sem repetir; `type` = o do primeiro, **exceto** se o do primeiro for `other` e o outro for específico.
3. Chave 2 só vale se título normalizado tiver ≥ 15 caracteres **e** houver ano **e** primeiro autor; caso contrário, o registro nunca é fundido por chave 2 (evita fundir "Introdução" com "Introdução").
4. Tolerância: títulos que diferem só por pontuação, acento, caixa ou espaços são iguais. **Não** usar similaridade difusa nesta versão.
5. `id` do `Record` resultante: recalculado (`build_record_id`) depois da união (se ganhou DOI, passa a `doi:...`).

**Arquivos:** `app/services/dedup.py`, `tests/unit/test_dedup.py`.

**Especificação detalhada**
- Casos de teste: mesmo DOI em OpenAlex e CORE (caixa diferente); mesmo título sem DOI em CORE e UESPI; títulos curtos iguais sem DOI (não fundir); mesmo título e anos diferentes (não fundir); três fontes para o mesmo trabalho; registro sem DOI cujo duplicado tem DOI (fundir por chave 2 e herdar o DOI).
- Complexidade linear com dicionários (sem comparação par a par).

**Critérios de aceite**
- [ ] Todos os casos acima passam.
- [ ] Teste com 5.000 registros sintéticos roda sem crescimento quadrático (apenas verifique que termina em tempo razoável; **não** escreva número de tempo na documentação).
- [ ] `deduplicate` é idempotente (aplicar duas vezes dá o mesmo resultado).

**Testes obrigatórios:** os acima, mais propriedade de idempotência.
**Proibido nesta OS:** similaridade difusa; fusão por título curto.
**Evidência para o TCC:** exemplo antes/depois de uma fusão real (busca do desenvolvedor) em `docs/evidencias/os-011-exemplo.md`, para 4.2.
**Commit:** `feat(os-011): deduplicação de registros por DOI e por título normalizado`

---

## OS-012 — Orquestrador de busca

**Depende de:** OS-007, 008, 010, 011.
**Rastreabilidade no TCC:** Introdução (busca unificada, filtros); 2.2; 4.2.

**Objetivo:** consultar todas as fontes ativas em paralelo, combinar, deduplicar, paginar e reportar o estado de cada uma.

**Decisões já tomadas:** D3 (paginação combinada, total estimado) e D4 (falha parcial).

**Tarefas**
1. `app/services/search_service.py`: `async search(query: SearchParams, user_id | None) -> SearchResponse`.
2. Selecionar os conectores: os pedidos em `sources` (ou todos) **e** habilitados. Os demais entram em `sources_status` com `disabled`.
3. `k` = número de conectores ativos; `per_source = ceil(page_size / k)`; chamar todos com `asyncio.gather(..., return_exceptions=True)` e um **tempo limite global** (`SOURCE_TIMEOUT_SECONDS + 2`) por fonte (`asyncio.wait_for`).
4. Converter exceções e timeouts em `SourceStatus` (nunca propagar).
5. **Intercalar** (round-robin) os resultados na ordem das fontes (ordem fixa: `openalex, core, scielo, bdtd, ufpi, uespi`), `deduplicate`, e **cortar em `page_size`**.
6. `total_estimated` = soma dos `total` das fontes com `status=ok`; `total_is_estimate=true`.
7. Se **todas** as fontes pedidas falharem ou estiverem desabilitadas: `UpstreamError` (HTTP 502) com `sources_status`.
8. `sort=year_desc` com fontes que não suportam: ordenar a página combinada por `year` desc (nulos por último) e preencher `message` na fonte.
9. Marcar `is_favorite` para o usuário (consulta única a `favorites` com os `record_id` da página; a OS-017 fornece a função; aqui, defina o ponto de extensão `favorite_ids_for(user_id, record_ids)` que devolve `set[str]`, com implementação real já pronta se a OS-017 ainda não existir, **sem** depender dela).
10. Medir duração por fonte e total; devolver em `sources_status[...].duration_ms` **apenas se** `APP_ENV=development` (para a OS-033 medir; não vira promessa de desempenho).

**Arquivos:** `app/services/search_service.py`, `app/schemas/search.py`, `tests/unit/test_search_service.py`.

**Especificação detalhada**
- Testes com **conectores falsos** (classes que implementam o `Protocol`): todos ok; um com timeout; um levantando exceção; todos desabilitados; todos falhando; duplicata entre duas fontes; `year_desc`.
- Validação de parâmetros em `SearchParams` conforme 6.4 (limites, `year_from ≤ year_to`, tipos válidos, `sources` válidos entre os slugs registrados).

**Critérios de aceite**
- [ ] Um conector lento (acima do limite) não atrasa a resposta além do limite global.
- [ ] Uma fonte com erro não impede as demais.
- [ ] Todas falhando → 502 com `sources_status`.
- [ ] Duplicata entre fontes vira um registro com duas entradas em `sources`.
- [ ] `total_is_estimate` é sempre `true`.

**Testes obrigatórios:** os sete cenários.
**Proibido nesta OS:** cache de resultados (D6); escrever no banco além do que o serviço de histórico pedir (OS-018).
**Evidência para o TCC:** diagrama de sequência (Mermaid `sequenceDiagram`) da busca em `docs/evidencias/os-012-sequencia.md`, para 4.2 e 4.3.
**Commit:** `feat(os-012): orquestrador de busca com paginação combinada e falha parcial`

---

## OS-013 — Raspagem complementar de resumo

**Depende de:** OS-006, OS-012.
**Rastreabilidade no TCC:** Introdução e 2.2 (Vargiu e Urru, 2012: web scraping); 3; 4.2 (decisão: raspagem só como complemento).

**Objetivo:** quando habilitada, completar o **resumo** de registros que vieram sem ele, a partir da página pública do trabalho, com respeito a `robots.txt`, identificação e limite de frequência.

**Decisões já tomadas:** D8 — desligada por padrão (`SCRAPING_ENABLED=false`); só roda para `abstract is None` e só em `url` `http/https`; nunca raspa páginas que exijam login; nunca roda em lote durante a busca (apenas nos itens da página, no máximo 5 por busca).

**Tarefas**
1. `app/scraping/polite_scraper.py`: busca de página com: leitura e cache em memória do `robots.txt` por domínio (biblioteca padrão `urllib.robotparser`); recusa se o caminho for proibido para o nosso `User-Agent`; **pausa mínima de 2 s por domínio**; `User-Agent` identificado; tempo limite; tamanho máximo de página (1 MB); só `text/html`.
2. `app/scraping/abstract_extractor.py`: extrai o resumo de HTML em **ordem de preferência**: `<meta name="citation_abstract">`, `<meta name="DC.description">` / `dc.description`, `<meta property="og:description">` (somente se tiver ≥ 200 caracteres), JSON-LD (`"description"` ou `"abstract"` de um `ScholarlyArticle`). **Sem** heurística de "pegar o maior parágrafo".
3. Biblioteca de HTML: **`selectolax`** ou **`beautifulsoup4`** (escolha uma e registre em `DECISOES.md`; é a segunda adição permitida fora da seção 4).
4. Integração no orquestrador (OS-012): depois da deduplicação, se `SCRAPING_ENABLED`, completar até 5 registros da página com `abstract is None` e `url`; falhas são silenciosas (log de nível `INFO`) e **não** alteram `sources_status`.
5. Marcar no `Record` que o resumo veio de raspagem? **Não**: o esquema 6.2 não muda. Registrar em log.

**Arquivos:** `app/scraping/*.py`, `tests/unit/test_abstract_extractor.py`, `tests/unit/test_polite_scraper.py`, `tests/fixtures/html/*.html`.

**Especificação detalhada**
- Fixtures HTML: página com `citation_abstract`; página só com `og:description` curta (ignorar); página com JSON-LD; página sem nada.
- `robots.txt`: teste com regra `Disallow: /` (recusa), arquivo ausente (404 → permitido), erro 5xx (tratar como **proibido** por prudência).
- Pausa por domínio testada com relógio simulado (injetar função de tempo).

**Critérios de aceite**
- [ ] Com `SCRAPING_ENABLED=false`, **nenhuma** chamada de raspagem acontece (teste).
- [ ] Páginas bloqueadas por `robots.txt` não são requisitadas.
- [ ] A pausa por domínio é respeitada.
- [ ] Extração segue a ordem de preferência.
- [ ] Nenhuma raspagem em registro que já tem resumo.

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** raspar sites que exijam login ou que bloqueiem; contornar CAPTCHA; trocar o `User-Agent` por um de navegador; raspar para campos além do resumo.
**Evidência para o TCC:** texto curto em `docs/evidencias/os-013-raspagem.md` dizendo **quando** a raspagem entra, **como** respeita `robots.txt` e que fica desligada por padrão (para 4.2). **Medir** (script do projeto) em quantos de N registros de uma busca real o resumo foi completado; só relatar o número medido.
**Commit:** `feat(os-013): raspagem complementar de resumo, desligada por padrão`

---

# FASE 2 — API

## OS-014 — FastAPI base, OpenAPI, saúde, CORS e cabeçalhos

**Depende de:** OS-002, OS-003.
**Rastreabilidade no TCC:** 2.3 (Fielding, 2000; Bray, 2017); 2.4 (Ramírez, 2018: OpenAPI, JSON); 2.6 (OWASP A6: configuração).

**Objetivo:** subir a aplicação com roteador versionado `/api/v1`, documentação OpenAPI, rota de saúde, CORS restrito e cabeçalhos de segurança.

**Decisões já tomadas:** prefixo `/api/v1`; JSON em todas as respostas; documentação em `/api/docs` (Swagger UI) e `/api/openapi.json`; frontend estático servido em `/` (D7).

**Tarefas**
1. `app/main.py`: `create_app()` com título, descrição em português, versão; registrar tratadores de erro (OS-002), middleware de `request_id`, CORS (apenas `ALLOWED_ORIGINS`, métodos `GET, POST, PUT, PATCH, DELETE`, cabeçalhos `Authorization, Content-Type`), `slowapi` (limitador por IP, armazenamento em memória).
2. Middleware de **cabeçalhos de segurança** em todas as respostas: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy` restritiva, `Content-Security-Policy` (`default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`; **sem** `unsafe-inline`), e `Strict-Transport-Security` quando `APP_ENV=production`.
3. `app/api/v1/health.py`: `GET /api/v1/health` → `{"status":"ok","database":"ok|error","version":"..."}` (sem detalhes do erro).
4. `app/api/v1/router.py`: agrega os roteadores (vazios por ora, com `tags` em português).
5. Montar `StaticFiles` para `frontend/` em `/` (com `html=True`), **depois** das rotas de API.
5a. **Limitação do limitador de taxa, a registrar:** o `slowapi` guarda os contadores **em memória do processo**. Com mais de um processo (`uvicorn --workers N` ou vários contêineres) cada processo conta separado e o limite por IP deixa de valer. Portanto: execute a aplicação com **um único processo** e escreva isso em `docs/DECISOES.md` e em `docs/SEGURANCA.md` como limitação conhecida. **Não** adicione Redis (fora do escopo).
6. Documentar no OpenAPI: `servers`, esquemas de erro (6.5) como resposta padrão 4xx/5xx, esquema de segurança `bearerAuth`.
7. Exemplos (`examples`) nos modelos principais (`RecordOut`).

**Arquivos:** `app/main.py`, `app/api/v1/router.py`, `app/api/v1/health.py`, `app/core/security_headers.py`, `tests/integration/test_app_base.py`.

**Critérios de aceite**
- [ ] `GET /api/v1/health` responde 200 com banco ok; 200 com `database:"error"` se o banco cair (sem *stack trace*).
- [ ] `GET /api/openapi.json` é um OpenAPI 3.x válido (validar com `openapi-spec-validator` em dev **ou** carregando o JSON e checando chaves obrigatórias).
- [ ] CORS: origem fora da lista **não** recebe `Access-Control-Allow-Origin`.
- [ ] Todos os cabeçalhos do item 2 presentes (teste).
- [ ] `uvicorn app.main:app` sobe e `/api/docs` abre.

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** rotas de negócio; `allow_origins=["*"]`.
**Evidência para o TCC:** captura de `/api/docs` (feita na OS-032) e lista de cabeçalhos de segurança em `docs/evidencias/os-014-cabecalhos.txt` (4.3 e 4.6).
**Commit:** `feat(os-014): aplicação FastAPI com OpenAPI, CORS e cabeçalhos de segurança`

---

## OS-015 — Cadastro e login (JWT, Argon2id)

**Depende de:** OS-004, OS-014.
**Rastreabilidade no TCC:** Introdução (favoritos exigem conta); 2.3 (stateless); 2.6 (LGPD: consentimento, necessidade, segurança; OWASP A2 autenticação e A3).

**Objetivo:** permitir cadastro com consentimento explícito e login com token JWT.

**Decisões já tomadas:** D5; Argon2id; token de acesso único (sem refresh token nesta versão); dados mínimos: nome, e-mail, senha.

**Tarefas**
1. `app/core/security.py`: `hash_password`, `verify_password` (com `needs_rehash`), `create_access_token(user_id)` (claims: `sub`, `iat`, `exp`, `iss`, `jti`), `decode_access_token` (valida assinatura, `exp`, `iss`; algoritmo **fixo** `HS256`, nunca aceitar o do cabeçalho).
2. `app/schemas/user.py`: `UserCreate` (`full_name` 2–120; `email` válido, normalizado em minúsculas; `password` 10–128 caracteres, ao menos 1 letra e 1 número, não pode conter o e-mail; `accept_privacy_policy` deve ser `true`), `UserOut` (sem `password_hash`), `TokenOut` (`access_token`, `token_type="bearer"`, `expires_in`).
3. `app/services/auth_service.py`: `register`, `authenticate`.
4. `app/api/v1/auth.py`:
   - `POST /api/v1/auth/register` → 201 com `UserOut` (grava `consent_at` e `consent_policy_version`); e-mail repetido → 409 com mensagem **genérica** ("Não foi possível concluir o cadastro") — **não** revelar se o e-mail existe;
   - `POST /api/v1/auth/login` (JSON `{email, password}`) → 200 `TokenOut`; credencial inválida → 401 com mensagem única e **tempo de resposta semelhante** (executar `verify_password` contra um hash falso quando o usuário não existe);
   - `GET /api/v1/auth/me` → `UserOut` (exige token).
5. Dependência `get_current_user` (lê `Authorization: Bearer`, valida, carrega usuário ativo; 401 caso contrário) e `get_optional_user`.
6. Limite de taxa `RATE_LIMIT_AUTH` em `register` e `login`.
7. Registrar `security_events` (`account_registered`, `login_success`, `login_failed`, `rate_limited`), com `ip_hash` e **sem** e-mail.

**Arquivos:** `app/core/security.py`, `app/schemas/user.py`, `app/services/auth_service.py`, `app/api/v1/auth.py`, `app/api/deps.py`, `tests/unit/test_security.py`, `tests/integration/test_auth.py`.

**Especificação detalhada**
- Token adulterado, expirado, com `alg=none` e com `iss` errado → 401 (testes).
- Senha nunca aparece em log, em resposta ou em `security_events`.
- Os parâmetros do Argon2id ficam em constantes documentadas em `DECISOES.md` (usar os padrões da biblioteca; **não** inventar valores).

**Critérios de aceite**
- [ ] Cadastro sem aceitar a política → 422.
- [ ] E-mail repetido → 409 genérico; login com e-mail inexistente e com senha errada → mesma mensagem e mesmo status.
- [ ] Token `alg=none` e token expirado → 401.
- [ ] Sexto login errado no minuto → 429 e evento `rate_limited`.
- [ ] `password_hash` nunca é devolvido.

**Testes obrigatórios:** os acima e hash/verify/rehash.
**Proibido nesta OS:** OAuth/login social; 2FA; refresh token; recuperação de senha por e-mail (fora do escopo).
**Evidência para o TCC:** tabela "controle → risco OWASP" parcial em `docs/SEGURANCA.md` (A2, A3, A7), para 4.6.
**Commit:** `feat(os-015): cadastro e login com JWT e Argon2id`

---

## OS-016 — Rota de busca

**Depende de:** OS-012, OS-015.
**Rastreabilidade no TCC:** Introdução (busca unificada, filtros); 2.3 (REST); 4.1 e 4.2.

**Objetivo:** expor `GET /api/v1/search` conforme 6.4, aberto a visitantes e enriquecido para usuários logados.

> **Na Fatia 1 (7.1)** esta OS é executada na forma reduzida **OS-016r**, sem usuário autenticado e sem histórico.

**Tarefas**
1. `app/api/v1/search.py`: `GET /api/v1/search` com os parâmetros de 6.4 (`Query` com validação e descrição em português), dependência `get_optional_user`, limite `RATE_LIMIT_SEARCH`.
2. Chamar `search_service.search`; devolver `SearchResponse` (6.4).
3. Para usuário autenticado: gravar histórico (função da OS-018; se a OS-018 ainda não existir, deixar o ponto de chamada pronto e testado com *stub*); `is_favorite` preenchido.
4. `GET /api/v1/sources` → lista de fontes com `slug`, `name`, `kind` (`api` ou `oai`), `enabled` e `status` (`disabled` quando faltar chave ou colheita) — usada pela interface para montar o filtro de fontes. **Não** expor URLs internas, chaves nem contagens de registros.
5. Códigos: 422 validação; 429 limite; 502 todas as fontes falharam.

**Arquivos:** `app/api/v1/search.py`, `tests/integration/test_search_api.py`.

**Especificação detalhada**
- `q` com espaços nas pontas é aparada; `q` de 1 caractere → 422 com mensagem em português.
- `sources=foo` → 422 listando os valores válidos.
- Testes com **conectores falsos** injetados via dependência (sem rede).

**Critérios de aceite**
- [ ] Busca de visitante devolve resultados com `is_favorite=false`.
- [ ] Parâmetros inválidos → 422 no formato 6.5.
- [ ] Todas as fontes falhando → 502 com `sources_status`.
- [ ] `/api/v1/sources` não vaza chaves nem URLs internas (teste).
- [ ] O OpenAPI descreve todos os parâmetros e a resposta.

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** cache; novos parâmetros fora de 6.4.
**Evidência para o TCC:** exemplo de requisição e resposta (JSON, editada) em `docs/evidencias/os-016-exemplo.json`, para 4.1 e 4.3.
**Commit:** `feat(os-016): rota de busca unificada e listagem de fontes`

---

## OS-017 — Favoritos

**Depende de:** OS-015, OS-016.
**Rastreabilidade no TCC:** Introdução (favoritos); 2.5 (Santarém Segundo e Vidotti, 2011: organização por tags).

> **Divergência a declarar no TCC:** a seção 2.5 cita organização por **tags** (folksonomia assistida), e esta versão do sistema entrega **anotação em texto livre**, não tags. Na seção 4.5 escreva o que o sistema faz (anotação) e diga que a organização por tags, discutida por Santarém Segundo e Vidotti (2011), não foi implementada. Registre também em `docs/CONFORMIDADE_TCC.md` (OS-035).

**Objetivo:** permitir salvar, anotar, listar e remover favoritos.

**Decisões já tomadas:** o favorito guarda um **retrato** (`record_snapshot`) do `Record` para continuar válido mesmo se a fonte mudar; a **anotação** (`note`) é texto livre até 1000 caracteres. **Tags** como entidade própria **não** entram nesta versão (a anotação cumpre o papel de organização).

**Tarefas**
1. `app/schemas/favorite.py`: `FavoriteCreate` (`record` completo conforme `RecordOut`, `note` opcional), `FavoriteUpdate` (`note`), `FavoriteOut` (`id`, `record`, `note`, `created_at`).
2. `app/services/favorite_service.py`: `add`, `list` (paginado, mais recentes primeiro, busca opcional por texto no título/anotação do retrato), `update_note`, `remove`, `favorite_ids_for`.
3. `app/api/v1/favorites.py`:
   - `POST /api/v1/favorites` → 201 (idempotente: já existente → 200 com o existente);
   - `GET /api/v1/favorites?page&page_size&q` → lista paginada;
   - `PATCH /api/v1/favorites/{id}` → atualiza `note`;
   - `DELETE /api/v1/favorites/{id}` → 204.
4. **Autorização por objeto:** um usuário nunca lê, altera ou apaga favorito de outro (404, não 403, para não revelar existência).
5. Validação do `record` recebido: reaplicar `RecordOut` e limite de tamanho (ex.: 20 KB serializado) para evitar abuso de armazenamento. Limitar a **2.000 favoritos por usuário** (registrar o motivo em `DECISOES.md`).

**Arquivos:** `app/schemas/favorite.py`, `app/services/favorite_service.py`, `app/api/v1/favorites.py`, `tests/integration/test_favorites.py`.

**Critérios de aceite**
- [ ] Criar o mesmo favorito duas vezes não duplica.
- [ ] Usuário B recebe 404 ao tentar ler/alterar/apagar favorito do usuário A.
- [ ] Sem token → 401.
- [ ] `note` acima de 1000 caracteres → 422.
- [ ] `record` com `url` inválida → 422.
- [ ] A busca (OS-016) marca `is_favorite=true` para itens salvos.

**Testes obrigatórios:** os acima, e o limite de 2.000.
**Proibido nesta OS:** tags como tabela; coleções públicas ou compartilhamento.
**Evidência para o TCC:** descrição do controle de acesso por objeto em `docs/SEGURANCA.md` (OWASP A5), para 4.5 e 4.6.
**Commit:** `feat(os-017): favoritos com anotação e controle de acesso por objeto`

---

## OS-018 — Histórico de buscas

**Depende de:** OS-015, OS-016.
**Rastreabilidade no TCC:** Introdução; 2.5; 2.6 (LGPD: necessidade e eliminação).

**Objetivo:** registrar as buscas do usuário logado e permitir consulta e limpeza.

**Tarefas**
1. `app/services/history_service.py`: `record_search(user_id, params, total_estimated)`, `list`, `delete_one`, `clear_all`.
2. Regras de gravação: **não gravar** buscas de visitantes; **não repetir** a mesma consulta com os mesmos filtros em sequência imediata; manter no máximo as **200** mais recentes por usuário (apagar as mais antigas).
3. `app/api/v1/history.py`:
   - `GET /api/v1/history?page&page_size` → lista paginada (mais recentes primeiro);
   - `DELETE /api/v1/history/{id}` → 204;
   - `DELETE /api/v1/history` → 204 (limpa tudo).
4. Ligar à OS-016 (a rota de busca chama `record_search` **sem** atrasar a resposta: executar após a resposta com `BackgroundTasks` do FastAPI; falha ao gravar histórico **nunca** quebra a busca).

**Arquivos:** `app/services/history_service.py`, `app/api/v1/history.py`, `tests/integration/test_history.py`.

**Critérios de aceite**
- [ ] Busca de visitante não grava nada.
- [ ] Busca repetida em sequência grava uma vez.
- [ ] A 201ª busca apaga a mais antiga.
- [ ] Usuário só vê o próprio histórico.
- [ ] Erro ao gravar histórico não altera o status da busca (teste simulando falha).

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** análise ou "tendências" do histórico; recomendação.
**Evidência para o TCC:** texto sobre retenção limitada (200) e eliminação em `docs/LGPD.md`.
**Commit:** `feat(os-018): histórico de buscas com retenção limitada`

---

## OS-019 — Exportação (BibTeX, RIS, JSON, CSV)

**Depende de:** OS-017.
**Rastreabilidade no TCC:** Introdução (exportação em formatos de gerenciadores de referências); 4.5. **Atenção:** o TCC não tem fonte que sustente a exportação; ela é decisão do autor.

**Objetivo:** exportar favoritos (todos ou selecionados) e resultados de busca em quatro formatos.

**Decisões já tomadas:** formatos **BibTeX, RIS, JSON e CSV** (sem MARCXML); codificação UTF-8; exportação **gerada no servidor**, sem biblioteca externa de bibliografia (funções próprias e testadas).

**Tarefas**
1. `app/services/export_service.py` com `to_bibtex`, `to_ris`, `to_json`, `to_csv` (cada uma recebe `list[RecordOut]` e devolve `str`).
2. **BibTeX:** tipo de entrada por `type` (`article`→`@article`; `thesis`→`@phdthesis` **ou** `@mastersthesis` não distinguíveis → usar `@thesis`; `book`→`@book`; `preprint`→`@misc`; `other`→`@misc`); chave de citação `<sobrenome><ano><primeira palavra do título>` em minúsculas sem acento e **única** no arquivo (sufixo `a`, `b`...); campos `title`, `author` (`Sobrenome, Nome and ...`), `year`, `doi`, `url`, `abstract`, `keywords`, `language`; **escapar** `{ } \ & % $ # _ ^ ~` e preservar maiúsculas do título com `{}` duplas.
3. **RIS:** `TY` (`JOUR`, `THES`, `BOOK`, `GEN`), `TI`, `AU` (um por autor), `PY`, `DO`, `UR`, `AB`, `KW` (um por palavra-chave), `LA`, `ER  - ` ao fim de cada registro; linhas no padrão `TAG  - valor`.
4. **JSON:** lista de `RecordOut` com `indent=2`, `ensure_ascii=False`.
5. **CSV:** cabeçalho `id,title,authors,year,doi,url,pdf_url,type,language,keywords,sources`; `authors`, `keywords` e `sources` unidos por `; `; separador vírgula; aspas conforme RFC 4180; **neutralizar injeção de fórmula** (prefixar com `'` células que comecem com `=`, `+`, `-`, `@`, tab ou retorno).
6. `app/api/v1/export.py`:
   - `GET /api/v1/favorites/export?format=bibtex|ris|json|csv` (exporta todos os favoritos do usuário) — **rota declarada antes** de `/favorites/{id}` para não conflitar;
   - `POST /api/v1/export` com `{format, records: [Record...]}` (até 100 registros) para exportar **resultados da busca** sem exigir login.
   - Cabeçalhos: `Content-Type` correto (`application/x-bibtex`, `application/x-research-info-systems`, `application/json`, `text/csv; charset=utf-8`) e `Content-Disposition: attachment; filename="exportacao-<AAAAMMDD>.<ext>"`.
7. Registrar `security_events` `data_exported` para a exportação de favoritos (sem conteúdo).

**Arquivos:** `app/services/export_service.py`, `app/api/v1/export.py`, `tests/unit/test_export_service.py`, `tests/integration/test_export_api.py`.

**Especificação detalhada**
- Testes de **ida e volta** onde possível: ler o RIS gerado com um *parser* simples escrito no teste e conferir os campos.
- Casos de borda: título com `&`, `%`, `{`; autor com acento; registro sem ano/DOI/autores; duas entradas com a mesma chave de citação; célula CSV `=HYPERLINK(...)`.
- `[VERIFICAR]` (manual, desenvolvedor): importar o `.bib` e o `.ris` gerados em um gerenciador (Zotero ou Mendeley) e registrar o resultado.

**Critérios de aceite**
- [ ] Os quatro formatos geram saída válida para os casos de borda.
- [ ] Chaves BibTeX únicas.
- [ ] CSV neutraliza fórmulas.
- [ ] Mais de 100 registros em `POST /export` → 422.
- [ ] `Content-Disposition` correto nos quatro formatos.

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** MARCXML; integração direta com Zotero/Mendeley; biblioteca de bibliografia externa.
**Evidência para o TCC:** um arquivo `.bib` e um `.ris` de exemplo em `docs/evidencias/os-019/` e o resultado do teste manual de importação (4.5).
**Commit:** `feat(os-019): exportação em BibTeX, RIS, JSON e CSV`

---

## OS-020 — Conta e direitos do titular (LGPD)

**Depende de:** OS-015, OS-017, OS-018, OS-019.
**Rastreabilidade no TCC:** 2.6 (Brasil, 2018, arts. 6º III, VII e VIII, 18 e 46); 4.6.

**Objetivo:** dar ao titular acesso, correção, eliminação e portabilidade dos próprios dados.

**Decisões já tomadas:** o art. 18 assegura, entre outros, acesso aos dados, correção de dados incompletos, inexatos ou desatualizados e eliminação de dados tratados com consentimento. Cada direito vira uma rota.

**Tarefas**
1. `app/api/v1/me.py`:
   - `GET /api/v1/me` → dados da conta (`full_name`, `email`, `created_at`, `consent_at`, `consent_policy_version`);
   - `PATCH /api/v1/me` → corrige `full_name` e `email` (e-mail novo exige a senha atual; e-mail já usado → 409 genérico);
   - `POST /api/v1/me/password` → troca de senha (exige a senha atual; registra `password_changed`);
   - `GET /api/v1/me/data-export` → **portabilidade/acesso**: um JSON com conta, favoritos e histórico (registra `data_exported`);
   - `DELETE /api/v1/me` → **eliminação**: exige `{password}` no corpo; apaga usuário, favoritos e histórico (cascata) e registra `account_deleted` **sem** dados pessoais; 204.
2. `GET /api/v1/privacy` → texto da política (versão em `PRIVACY_POLICY_VERSION`, conteúdo em `app/content/privacy_pt.md`), público.
3. Escrever `app/content/privacy_pt.md` em português claro: quais dados são tratados (nome, e-mail, hash de senha, favoritos, histórico, eventos de segurança com IP em hash), finalidade, base (consentimento), retenção, direitos e como exercê-los, medidas de segurança, contato do responsável (**placeholder** `{CONTATO_DO_RESPONSAVEL}` que o desenvolvedor preenche), data. **Não** afirmar certificações nem números.
4. Novo consentimento: se a versão da política mudar, o login devolve `consent_required=true` e a rota `POST /api/v1/me/consent` registra o novo aceite.
5. `docs/LGPD.md`: tabela "direito do art. 18 → rota → teste".

**Arquivos:** `app/api/v1/me.py`, `app/content/privacy_pt.md`, `docs/LGPD.md`, `tests/integration/test_me.py`.

**Critérios de aceite**
- [ ] Excluir a conta apaga usuário, favoritos e histórico (teste conta linhas antes/depois).
- [ ] Exclusão exige senha correta.
- [ ] O JSON de `data-export` contém todos os dados do usuário e **nenhum** dado de outro.
- [ ] Após a exclusão, o token antigo falha (401).
- [ ] `security_events` mantém o evento `account_deleted` sem e-mail.
- [ ] `PATCH /me` com e-mail repetido → 409 genérico.

**Testes obrigatórios:** os acima, e mudança de versão da política.
**Proibido nesta OS:** coletar dados adicionais; analytics; cookies de rastreamento.
**Evidência para o TCC:** `docs/LGPD.md` pronto; texto da política (4.6).
**Commit:** `feat(os-020): conta do usuário e direitos do titular (LGPD)`

---

# FASE 3 — FRONTEND

> **Regras de toda a Fase 3:** HTML5 semântico, CSS3 e JavaScript ES2020+ com **módulos nativos** (`<script type="module">`). **Sem** frameworks, bundlers, jQuery, CDN externo (fontes e bibliotecas ficam locais ou são do sistema), nem `innerHTML` com dados externos (usar `textContent` e criação de elementos). Todo texto em português. O token JWT fica **só em memória** e em `sessionStorage` **quando o usuário marcar "manter conectado nesta aba"**; **nunca** em `localStorage` (reduz o risco de roubo por XSS; registrar a decisão em `DECISOES.md`). Sem inline `style` nem `script` inline (por causa da CSP da OS-014).

## OS-021 — Base do frontend: layout, tokens, responsividade e acessibilidade

**Depende de:** OS-014.
**Rastreabilidade no TCC:** 2.5 (Bader e Hammouri, 2016; Pathak et al.; Cybis et al., 2010; Prates e Barbosa, 2003; W3C, 2014 e 2018); 4.4.

**Objetivo:** criar o esqueleto visual, o sistema de estilos e os módulos JS compartilhados.

**Tarefas**
1. `frontend/css/tokens.css`: variáveis (cores, espaçamento, tipografia, raios, sombras); paleta com **contraste ≥ 4,5:1** (texto comum) e ≥ 3:1 (componentes e texto grande), verificado e anotado no próprio arquivo; **sem** tema escuro próprio (fora do escopo).
2. `frontend/css/base.css` (reset leve, tipografia, foco visível `:focus-visible` com contorno de ≥ 3 px e contraste), `layout.css` (grade e *breakpoints*: móvel primeiro; ajustes em ~600 px e ~960 px), `components.css` (botões, campos, cartões, avisos, *skeleton* de carregamento).
3. `frontend/js/dom.js` (helpers `el()`, `clear()`, `announce()` para região `aria-live`), `api.js` (cliente `fetch` com base `/api/v1`, cabeçalho `Authorization`, tratamento do formato de erro 6.5, tempo limite com `AbortController`), `state.js` (estado simples: usuário/token), `a11y.js` (gestão de foco ao trocar de "tela", região `aria-live`, link "Pular para o conteúdo").
4. Estrutura comum de página (cabeçalho com marca e navegação, `<main id="conteudo">`, rodapé com link "Política de privacidade" e "API"): replicada em todas as páginas (sem gerador; copiar com cuidado ou usar um pequeno módulo JS que injeta o cabeçalho/rodapé **por criação de elementos**).
5. Menu de navegação **utilizável por teclado** e em celular (botão "Menu" com `aria-expanded` e `aria-controls`).
6. `prefers-reduced-motion` respeitado; nenhum conteúdo depende só de cor.
7. Página `index.html` provisória só com o esqueleto (a OS-022 preenche).

**Arquivos:** `frontend/**` conforme 5.3.

**Especificação detalhada**
- `<html lang="pt-BR">`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, um `<h1>` por página, hierarquia de títulos sem saltos, pontos de referência (`header`, `nav`, `main`, `footer`).
- Alvos de toque ≥ 44×44 px (WCAG 2.5.5 é AAA, mas adotado como boa prática; registrar).
- Tamanho de fonte em `rem`; layout sem rolagem horizontal a 320 px de largura e com zoom de 200%.

**Critérios de aceite**
- [ ] Página provisória abre sem erro de console.
- [ ] Sem rolagem horizontal em 320 px.
- [ ] Navegação por Tab percorre o cabeçalho na ordem lógica e o foco é visível.
- [ ] Tabela de contraste das cores principais anotada em `docs/ACESSIBILIDADE.md`, com a razão calculada (use um script do projeto para calcular; **não** estime).
- [ ] CSP da OS-014 não bloqueia nada (sem erro de CSP no console).

**Testes obrigatórios:** teste de fumaça Playwright que abre `/` e verifica ausência de erros de console e o `lang`.
**Proibido nesta OS:** framework, CDN, `innerHTML` com dados externos, `localStorage` para token.
**Evidência para o TCC:** capturas em 3 larguras (celular, tablet, computador) do esqueleto (4.4) e a tabela de contraste.
**Commit:** `feat(os-021): base do frontend responsivo e acessível`

---

## OS-022 — Tela de busca e resultados

**Depende de:** OS-016, OS-021.
**Rastreabilidade no TCC:** Introdução (busca unificada); 4.1; 4.4.

**Objetivo:** campo de busca, lista de resultados unificados, estados de carregamento/erro/vazio, paginação e indicação de fontes.

**Tarefas**
1. `index.html` com formulário de busca (`<form role="search">`, `<label>` visível, botão "Buscar"); a busca atualiza a URL (`?q=&page=...`) com `history.pushState` para permitir voltar/compartilhar o link; ao carregar com `?q=`, executa a busca.
2. `frontend/js/search.js`: chama `GET /api/v1/search`; renderiza cada `Record` como cartão: título (link para `url` em nova aba com `rel="noopener noreferrer"`), autores (até 5 e "+N"), ano, tipo (texto), idioma, **selos das fontes** (nome legível, não só cor), resumo truncado com "Ler mais" (botão que expande, `aria-expanded`), link "Texto completo (PDF)" quando `pdf_url`, botão de favorito (OS-025), botão "Copiar citação" (opcional **não**; fora do escopo).
3. Estados: carregando (*skeleton* + anúncio `aria-live` "Buscando…"), vazio ("Nenhum resultado. Tente outros termos ou remova filtros."), erro total (mensagem do 502 + estado por fonte), erro parcial (aviso "Algumas fontes não responderam: …" listando `sources_status` não `ok`, com o motivo em português).
4. Resumo da busca: "Cerca de N resultados (estimativa)" usando `total_estimated` e **sempre** a palavra "estimativa"; indicar quantas fontes responderam.
5. Paginação: botões "Anterior/Próxima" e indicação "Página X"; ao trocar de página, rolar ao topo da lista e mover o foco para o título de resultados.
6. Fonte desabilitada (`sources_status = disabled`) aparece como nota discreta em "Fontes" (ex.: "BDTD: ainda não colhida"), sem alarme.
7. Texto de ajuda sob o campo: dicas de busca (aspas para expressão exata; `-termo` exclui) — válidas para as fontes locais; avisar que nas fontes externas o comportamento pode variar.

**Arquivos:** `frontend/index.html`, `frontend/js/search.js`, `frontend/css/components.css` (acréscimos), `tests/e2e/test_search_page.py`.

**Critérios de aceite**
- [ ] Busca com resposta simulada (rota interceptada no Playwright) renderiza os cartões.
- [ ] Erro parcial mostra o aviso com as fontes que falharam.
- [ ] Todos os resultados vêm de `textContent`; teste injeta `<img src=x onerror=...>` num título e prova que **não** executa.
- [ ] Voltar do navegador restaura a busca anterior.
- [ ] Foco e leitura por teclado funcionam em toda a tela.

**Testes obrigatórios:** os acima (Playwright, rede interceptada).
**Proibido nesta OS:** `innerHTML` com dados externos; scroll infinito.
**Evidência para o TCC:** capturas "busca vazia", "resultados", "erro parcial", "sem resultados" (4.1).
**Commit:** `feat(os-022): tela de busca e resultados unificados`

---

## OS-023 — Filtros (ano, tipo, fontes e ordenação)

**Depende de:** OS-022.
**Rastreabilidade no TCC:** Introdução (filtros por ano e tipo); 4.1.

**Objetivo:** permitir refinar a busca por ano, tipo e fonte, e ordenar.

**Tarefas**
1. Painel de filtros (em celular, dentro de um botão "Filtros" que abre um painel com `<dialog>` ou seção recolhível acessível): ano inicial e final (`<input type="number">` com `min`, `max` e validação `year_from ≤ year_to`), tipos (caixas de seleção: Artigo, Tese/Dissertação, Preprint, Livro, Outro), fontes (caixas dinâmicas a partir de `/api/v1/sources`; fontes `disabled` aparecem desabilitadas com a razão), ordenação (Relevância / Mais recentes).
2. `frontend/js/filters.js`: lê e escreve os filtros na URL; botão "Aplicar" e "Limpar"; mostra os filtros ativos como etiquetas removíveis.
3. Aplicar filtro volta para a página 1.
4. Aviso: "Registros sem ano são ocultados quando há filtro de ano" (as fontes locais ocultam registros sem ano, OS-010).
5. Mensagens de validação ligadas ao campo (`aria-describedby`, `aria-invalid`).

**Arquivos:** `frontend/js/filters.js`, `frontend/index.html` (ajustes), `frontend/css/components.css`, `tests/e2e/test_filters.py`.

**Critérios de aceite**
- [ ] Filtros refletem na URL e na requisição (teste confere a *query string*).
- [ ] `year_from > year_to` bloqueia o envio com mensagem acessível.
- [ ] "Limpar" remove tudo e refaz a busca.
- [ ] Utilizável só com teclado, em celular e em computador.

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** filtros além de ano, tipo, fonte e ordenação (idioma só se o desenvolvedor pedir; **não** está no TCC).
**Evidência para o TCC:** capturas do painel aberto e dos filtros ativos (4.1).
**Commit:** `feat(os-023): filtros por ano, tipo, fonte e ordenação`

---

## OS-024 — Cadastro e login na interface

**Depende de:** OS-015, OS-021.
**Rastreabilidade no TCC:** 2.6 (consentimento, LGPD); 4.6.

**Tarefas**
1. `conta.html` com abas **Entrar** e **Criar conta** (padrão de abas acessível: `role="tablist"`, setas do teclado) ou duas seções simples; escolher a mais simples e acessível.
2. Formulário de cadastro: nome, e-mail, senha (com botão "mostrar senha", `aria-pressed`), **caixa de consentimento** ("Li e aceito a Política de Privacidade", com link para `privacidade.html`), regras de senha visíveis antes de digitar, erros por campo.
3. Formulário de login; mensagem única de erro de credencial; tratamento do 429 ("Muitas tentativas. Aguarde um minuto.").
4. `frontend/js/auth.js`: guarda o token (regras da Fase 3), atualiza o cabeçalho ("Entrar" → nome do usuário e "Sair"), `logout` limpa o estado, e trata 401 em qualquer chamada levando a "Sessão expirada. Entre novamente." sem perder a busca atual.
5. Autocomplete correto: `autocomplete="name|email|current-password|new-password"`.
6. `privacidade.html` exibe `GET /api/v1/privacy` (Markdown simples convertido por **função própria** que escapa HTML e suporta títulos, parágrafos e listas; **sem biblioteca**).

**Arquivos:** `frontend/conta.html`, `frontend/privacidade.html`, `frontend/js/auth.js`, `tests/e2e/test_auth_ui.py`.

**Critérios de aceite**
- [ ] Cadastro sem marcar o consentimento não envia (mensagem acessível).
- [ ] Login bem-sucedido atualiza o cabeçalho; sair limpa o estado.
- [ ] Token não vai para `localStorage` (teste verifica).
- [ ] Erros são lidos por leitor de tela (`role="alert"` ou `aria-live`).
- [ ] O texto da política é renderizado sem executar HTML embutido (teste).

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** login social; "esqueci minha senha" por e-mail.
**Evidência para o TCC:** capturas de cadastro (com consentimento) e login (4.6).
**Commit:** `feat(os-024): cadastro, login e política de privacidade na interface`

---

## OS-025 — Favoritos, histórico e exportação na interface

**Depende de:** OS-017, OS-018, OS-019, OS-022, OS-024.
**Rastreabilidade no TCC:** Introdução; 4.5.

**Tarefas**
1. Botão de favorito em cada cartão (alternância `aria-pressed`, rótulo "Salvar nos favoritos" / "Remover dos favoritos"); visitante é levado a entrar (mantendo o contexto).
2. `favoritos.html`: lista paginada, busca textual, edição da **anotação** (campo de texto com contador de 1000), remoção com confirmação acessível (`<dialog>`), vazio amigável.
3. **Exportar:** em resultados, seleção por caixa e botão "Exportar selecionados"; em favoritos, "Exportar todos"; escolha do formato (BibTeX, RIS, JSON, CSV) e download (`Blob`/`<a download>` sem `innerHTML`).
4. Histórico: seção na própria `favoritos.html` ou página `historico.html` (escolher uma), lista com "Repetir busca", "Remover" e "Limpar tudo".
5. Todos os estados (carregando, vazio, erro) com anúncio `aria-live`.

**Arquivos:** `frontend/favoritos.html`, `frontend/js/favorites.js`, `frontend/js/export.js`, `tests/e2e/test_favorites_ui.py`.

**Critérios de aceite**
- [ ] Salvar, anotar, remover e exportar funcionam de ponta a ponta (API simulada ou servidor de teste).
- [ ] Exportação baixa arquivo com o nome e a extensão corretos.
- [ ] Remover favorito pede confirmação.
- [ ] Repetir busca do histórico refaz a consulta com os mesmos filtros.

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** tags como entidade; compartilhamento.
**Evidência para o TCC:** capturas de favoritos, anotação, seleção para exportar e arquivo exportado (4.5).
**Commit:** `feat(os-025): favoritos, histórico e exportação na interface`

---

## OS-026 — Conta e privacidade na interface

**Depende de:** OS-020, OS-024.
**Rastreabilidade no TCC:** 2.6 (art. 18); 4.6.

**Tarefas**
1. Seção "Minha conta" em `conta.html` (visível logado): ver dados, **corrigir** nome/e-mail, **trocar senha**, **baixar meus dados** (`data-export`, arquivo JSON), **excluir minha conta** (diálogo com aviso do que será apagado e confirmação por senha).
2. Tratar `consent_required` (novo aceite da política) ao entrar.
3. Rodapé: links "Política de privacidade" e "API" (`/api/docs`).
4. Após excluir: limpar estado e levar à página inicial com aviso.

**Arquivos:** `frontend/conta.html` (ajustes), `frontend/js/account.js`, `tests/e2e/test_account_ui.py`.

**Critérios de aceite**
- [ ] Cada direito do art. 18 implementado tem um botão funcional correspondente.
- [ ] Excluir exige senha e limpa a sessão.
- [ ] Baixar dados gera arquivo JSON com a conta, favoritos e histórico do usuário.
- [ ] Mudança de versão da política pede novo aceite.

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** exibir o hash de senha ou qualquer dado de outro usuário.
**Evidência para o TCC:** capturas de "Minha conta", "baixar dados" e "excluir conta" (4.6).
**Commit:** `feat(os-026): conta do usuário e privacidade na interface`

---

# FASE 4 — SEGURANÇA

## OS-027 — Tratamento dos riscos do OWASP Top 10 (2017)

**Depende de:** OS-015 a OS-026.
**Rastreabilidade no TCC:** 2.6 (OWASP, 2017); 4.6. **Atenção:** o TCC cita a lista de **2017** (A1 a A10). Se o autor trocar para 2021, atualizar esta OS junto (registrar em `DECISOES.md`).

**Objetivo:** revisar o sistema contra cada um dos dez riscos, corrigir lacunas e documentar o controle de cada um.

**Tarefas.** Criar `docs/SEGURANCA.md` com uma tabela "Risco → onde pode ocorrer neste sistema → controle implementado (arquivo) → teste". Para cada item, **verificar no código**, corrigir se faltar e escrever o teste:

| Risco (2017) | Verificações obrigatórias |
|---|---|
| A1 Injeção | Todas as consultas SQL parametrizadas (busca de código por `text(` e `execute(` com f-strings; zero ocorrências com entrada do usuário). `q` malicioso em todas as rotas e conectores. CSV com neutralização de fórmula (OS-019) |
| A2 Autenticação quebrada | Argon2id; mensagem única de erro; limite de tentativas; token com `exp`, `iss`, algoritmo fixo; nenhuma senha em log |
| A3 Exposição de dados sensíveis | Sem `password_hash` em respostas; IP só em hash; HSTS em produção; erros sem *stack trace*; `.env` fora do Git; chaves mascaradas em log |
| A4 Entidades externas XML (XXE) | Todo XML com `defusedxml` (teste com `malicious_dtd.xml` da OS-009); busca de `xml.etree` fora de `defusedxml` no código (zero) |
| A5 Controle de acesso quebrado | Favoritos e histórico por objeto (404 para outro usuário); rotas de `/me` exigem token; teste "usuário B não acessa dados de A" em **todas** as rotas protegidas (teste parametrizado que percorre as rotas do OpenAPI com `security`) |
| A6 Configuração incorreta de segurança | Cabeçalhos (OS-014); CORS restrito; `/api/docs` mantido, mas `APP_ENV=production` **desliga** `/api/docs` se `DOCS_ENABLED=false` (nova variável opcional, padrão `true`; documentar); mensagens de erro genéricas; sem `debug` em produção |
| A7 Cross-site scripting (XSS) | Frontend sem `innerHTML` com dados externos (busca automatizada nos `.js` por `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`: zero ocorrências com dados externos; permitir só com literais constantes e comentário); CSP sem `unsafe-inline`; teste de XSS armazenado (título/anotação com `<script>`) |
| A8 Desserialização insegura | Sem `pickle`, `yaml.load` inseguro (usar `yaml.safe_load`), `eval`, `exec`; JSON só por `json`/Pydantic |
| A9 Uso de componentes com vulnerabilidades conhecidas | `pip-audit` sem vulnerabilidade conhecida **ou** com exceção justificada por escrito; dependências travadas (OS-001) |
| A10 Registro e monitoramento insuficientes | `security_events` (OS-029); logs estruturados; eventos de login falho, limite e exclusão registrados |

**Arquivos:** `docs/SEGURANCA.md`, `tests/integration/test_security_owasp.py`, `tests/unit/test_code_hygiene.py` (varreduras de código descritas acima).

**Critérios de aceite**
- [ ] Cada linha da tabela de `SEGURANCA.md` tem controle, arquivo e teste referenciados.
- [ ] O teste parametrizado de A5 percorre todas as rotas protegidas.
- [ ] As varreduras de higiene (SQL concatenado, `innerHTML`, `xml.etree`, `pickle`, `eval`) passam.
- [ ] Qualquer correção feita está listada no relatório da OS.

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** declarar "sistema 100% seguro"; afirmar proteção que não foi testada.
**Evidência para o TCC:** `docs/SEGURANCA.md` pronto (base do 4.6).
**Commit:** `feat(os-027): controles e testes para os dez riscos do OWASP Top 10 (2017)`

---

## OS-028 — Análise estática com mais de uma ferramenta

**Depende de:** OS-027.
**Rastreabilidade no TCC:** 2.6 (Nunes et al., 2018: combinar ferramentas amplia a detecção, mas nenhuma cobre tudo); 4.6.

**Objetivo:** rodar `bandit`, `pip-audit` e `semgrep` (se instalável), triar os achados e documentar.

**Tarefas**
1. Alvos `make sast` (ou equivalente) que rodam: `bandit -r app -f json`, `pip-audit -r requirements.lock -f json`, `semgrep --config p/python --config p/owasp-top-ten app frontend` (**se o semgrep não puder rodar** — por exemplo sem rede para regras — registrar o motivo e usar `ruff` com regra `S` como segunda ferramenta; **não** fingir que rodou).
2. Salvar as saídas brutas em `docs/evidencias/sast/` (`bandit.json`, `pip-audit.json`, `semgrep.json`, com data e versões das ferramentas).
3. Criar `docs/SEGURANCA.md#analise-estatica` com **tabela de triagem**: ferramenta, achado, arquivo/linha, severidade informada, decisão (`corrigido`, `falso positivo` com justificativa, `aceito` com justificativa) e commit da correção.
4. Corrigir todos os achados de severidade alta e média que não sejam falso positivo comprovado. Achados baixos: corrigir ou justificar.
5. Quadro comparativo "qual ferramenta achou o quê" (quantos achados cada uma teve e quantos se sobrepõem) — **calcular por script**, sem estimar.

**Arquivos:** `Makefile` (alvo `sast`), `docs/SEGURANCA.md`, `docs/evidencias/sast/*`, `scripts/sast_summary.py`.

**Critérios de aceite**
- [ ] As saídas brutas existem e têm data e versão da ferramenta.
- [ ] Nenhum achado alto/médio sem decisão.
- [ ] O quadro comparativo é gerado por `scripts/sast_summary.py`.
- [ ] `pip-audit` sem vulnerabilidade conhecida **ou** exceção justificada.

**Testes obrigatórios:** `scripts/sast_summary.py` com teste unitário em entradas pequenas.
**Proibido nesta OS:** silenciar achado com `# nosec` sem justificativa escrita ao lado.
**Evidência para o TCC:** o quadro comparativo e a tabela de triagem (4.6). Se só duas ferramentas rodaram, o TCC deve dizer exatamente isso.
**Commit:** `chore(os-028): análise estática com múltiplas ferramentas e triagem`

---

## OS-029 — Registro de eventos de segurança

**Depende de:** OS-015, OS-020.
**Rastreabilidade no TCC:** 2.6 (OWASP A10; LGPD art. 46); 4.6.

**Objetivo:** consolidar o registro e a consulta administrativa dos eventos de segurança.

**Decisões já tomadas:** **não** haverá painel nem rota de administração na API (fora do escopo); a consulta é por **CLI**.

**Tarefas**
1. `app/services/security_events.py`: função única `record_event(session, event_type, user_id=None, request=None, details=None)` que calcula `ip_hash` e **recusa** (levanta erro) `details` com chaves proibidas (`email`, `password`, `token`, `name`).
2. Revisar as OS 015, 020 e 009 e fazê-las usar essa função.
3. CLI `python -m app.cli_security events [--type X] [--since AAAA-MM-DD] [--limit N]` que lista eventos (data, tipo, hash do IP truncado, detalhes).
4. Política de **retenção**: comando `purge --older-than-days N` (padrão sugerido: **180**; registrar a escolha em `DECISOES.md` como decisão do projeto, não como exigência legal).
5. Documentar em `docs/LGPD.md` o que é registrado e por quanto tempo.

**Arquivos:** `app/services/security_events.py`, `app/cli_security.py`, `tests/unit/test_security_events.py`.

**Critérios de aceite**
- [ ] Tentar registrar `details={"email": "..."}` falha (teste).
- [ ] Os eventos da lista de 6.6 são gerados nas rotas correspondentes.
- [ ] `purge` apaga só eventos antigos.
- [ ] O IP nunca aparece em claro (teste varre o banco).

**Testes obrigatórios:** os acima.
**Proibido nesta OS:** armazenar IP, e-mail ou User-Agent em claro.
**Evidência para o TCC:** exemplo de saída do `events` (sem dados pessoais) em `docs/evidencias/os-029.txt` (4.6).
**Commit:** `feat(os-029): registro e retenção de eventos de segurança`

---

# FASE 5 — QUALIDADE

## OS-030 — Consolidação da suíte de testes

**Depende de:** OS-001 a OS-029.
**Rastreabilidade no TCC:** 3 (validação a cada etapa); 4.

**Objetivo:** garantir uma suíte coesa, rápida e sem rede, com cobertura medida.

**Tarefas**
1. Rodar toda a suíte; corrigir testes frágeis (ordem, relógio, dados compartilhados).
2. Separar marcadores: `unit` (sem banco), `integration` (banco de teste), `contract`, `e2e`, `a11y`; alvos `make test-unit`, `make test-integration`, `make test`.
3. **Testes de contrato** em `tests/contract/`: para cada conector, validar que as **fixtures** (reais, quando existirem) produzem `RecordOut` válidos; falhar se uma fixture sintética ainda estiver sem substituição **e** `STRICT_FIXTURES=1` (para o desenvolvedor saber o que falta trocar por real).
4. Teste que garante que **nenhum teste usa rede**: fixture `autouse` que bloqueia `socket.connect` para endereços que não sejam o banco local (exceto o servidor de teste local do Playwright).
5. Cobertura: medir com `pytest-cov`; definir limiar mínimo de **80% de linhas em `app/`** **somente depois de medir** e registrar o valor real; se estiver abaixo, escrever os testes que faltam (priorizar `services/` e `api/`). **Não** inflar com testes vazios.
6. `docs/TESTES.md`: como rodar, o que cada marcador cobre, o que é manual.

**Arquivos:** `tests/**`, `Makefile`, `docs/TESTES.md`, `tests/conftest.py`.

**Critérios de aceite**
- [ ] `make test` verde duas vezes seguidas (sem teste instável).
- [ ] O bloqueio de rede funciona (teste prova que `httpx` real a um host externo é impedido).
- [ ] Cobertura medida e registrada; limiar aplicado só se atingido.
- [ ] `STRICT_FIXTURES=1` lista as fixtures sintéticas pendentes.

**Testes obrigatórios:** os próprios.
**Proibido nesta OS:** reduzir o limiar para "passar"; apagar testes que falham sem corrigir a causa.
**Evidência para o TCC:** relatório de cobertura (`htmlcov` resumido em `docs/evidencias/os-030-cobertura.txt`) e contagem de testes por marcador (tabela gerada por comando).
**Commit:** `test(os-030): consolidação da suíte, bloqueio de rede e cobertura medida`

---

## OS-031 — Verificação de acessibilidade (WCAG 2.1)

**Depende de:** OS-021 a OS-026.
**Rastreabilidade no TCC:** 2.5 (W3C, 2018; Nagaraju, Chawla e Rana, 2019: desafios práticos de avaliar acessibilidade); 4.4.

**Objetivo:** verificar a acessibilidade de todas as telas com ferramenta automática **e** com checklist manual, relatando o que cada método pode e não pode detectar.

**Tarefas**
1. Teste `tests/a11y/` com `axe-playwright-python` percorrendo todas as páginas e estados principais (busca com resultados, filtros abertos, erro parcial, favoritos, conta, privacidade, diálogos abertos) em **duas larguras** (celular e computador). Falhar em violações `serious` e `critical`.
2. **Checklist manual** em `docs/ACESSIBILIDADE.md` (uma linha por critério WCAG 2.1 aplicável, com `Atende / Não atende / Não se aplica` e observação). Cobrir no mínimo: 1.1.1, 1.3.1, 1.4.1, 1.4.3, 1.4.4, 1.4.10, 2.1.1, 2.1.2, 2.4.1, 2.4.3, 2.4.7, 3.1.1, 3.3.1, 3.3.2, 4.1.2, 4.1.3.
3. Testes manuais descritos para o desenvolvedor executar (a IA **não** pode simulá-los): navegação só por teclado em todas as telas; leitura com leitor de tela (NVDA no Windows ou VoiceOver no macOS) das telas de busca, resultados e favoritos; zoom 200% e 400%; modo de alto contraste do sistema. O desenvolvedor anota o resultado no mesmo documento.
4. Corrigir o que for encontrado e anotar o que foi corrigido.
5. Seção "limites da avaliação": ferramentas automáticas detectam apenas parte dos problemas; **dizer isso** no documento, coerente com Nagaraju et al. (2019).

**Arquivos:** `tests/a11y/*.py`, `docs/ACESSIBILIDADE.md`.

**Critérios de aceite**
- [ ] Zero violações `serious/critical` do axe nas telas e estados listados.
- [ ] Checklist manual preenchido com observações reais (**não** marcar "Atende" sem verificar).
- [ ] Itens que dependem do teste humano ficam marcados `PENDENTE (desenvolvedor)` até serem feitos.

**Testes obrigatórios:** os de axe.
**Proibido nesta OS:** afirmar "conformidade WCAG 2.1 AA" no documento; usar a expressão **"atende aos critérios verificados"**, listando-os.
**Evidência para o TCC:** o `ACESSIBILIDADE.md` e a saída do axe (4.4).
**Commit:** `test(os-031): verificação de acessibilidade automática e checklist manual`

---

## OS-032 — Testes de ponta a ponta e capturas para o TCC

**Depende de:** OS-022 a OS-026, OS-030.
**Rastreabilidade no TCC:** 4.1 (telas com a legenda "Fonte: Elaborado pelo Autor (2026)"); 4.4 a 4.6.

**Objetivo:** provar os fluxos principais ponta a ponta e gerar, por script, as capturas de tela de todo o capítulo 4.

**Tarefas**
1. `tests/e2e/test_flows.py` (Playwright, servidor local, **conectores falsos** com dados fixos e **banco de teste**): (a) visitante busca e exporta resultados; (b) cadastro → login → busca → favorita → anota → exporta favoritos; (c) filtros; (d) histórico → repetir busca; (e) baixar dados → excluir conta → login falha.
2. `scripts/capture_screens.py`: sobe a aplicação com dados de demonstração (**fictícios**, claramente marcados, ex.: títulos genéricos) e gera PNGs em `docs/evidencias/telas/` com nomes numerados (`4.1-01-busca-vazia.png`, `4.1-02-resultados.png`...), em larguras de computador e celular. Lista de telas: busca vazia; resultados; erro parcial; sem resultados; filtros abertos; filtros ativos; favoritos; anotação; exportar; histórico; cadastro (com consentimento); login; minha conta; excluir conta; política de privacidade; `/api/docs`.
3. Um arquivo `docs/evidencias/telas/INDICE.md` com a lista das capturas, o que cada uma mostra e **a seção do TCC** onde cabe.
4. Capturas com **dados reais** das fontes (para ilustrar a integração) são passo manual do desenvolvedor: roteiro em `docs/evidencias/telas/ROTEIRO_REAIS.md` (quais buscas fazer, em qual ordem; remover chave e e-mail das capturas).

**Arquivos:** `tests/e2e/test_flows.py`, `scripts/capture_screens.py`, `docs/evidencias/telas/*`.

**Critérios de aceite**
- [ ] Os cinco fluxos passam.
- [ ] O script gera todas as capturas listadas, sem intervenção.
- [ ] `INDICE.md` mapeia cada captura a uma seção do TCC.
- [ ] Nenhuma captura mostra dado pessoal real, chave ou e-mail verdadeiro.

**Testes obrigatórios:** os cinco fluxos.
**Proibido nesta OS:** apresentar dados de demonstração como se fossem resultados reais das fontes.
**Evidência para o TCC:** as capturas e o índice.
**Commit:** `test(os-032): fluxos de ponta a ponta e capturas de tela para o TCC`

---

## OS-033 — Medição: busca manual versus aplicação

**Depende de:** OS-012, OS-022, e **todas as fontes configuradas e colhidas** (OS-007 a OS-010 com validação manual).
**Rastreabilidade no TCC:** 4 (o roteiro do TCC exige medição para qualquer afirmação como "reduz o tempo de busca"); Introdução (justificativa).

**Objetivo:** produzir **dados medidos** que sustentem (ou não) a afirmação de que a aplicação reduz o esforço de busca. Esta OS **não** conclui nada sozinha: cria o instrumento e relata o que foi medido.

**Tarefas**
1. `scripts/measure_search.py`: para uma lista de consultas (arquivo `docs/evidencias/medicao/consultas.txt`, 5 consultas definidas pelo desenvolvedor, de temas dos cursos da UESPI), executa a busca na aplicação (com chaves reais e índice colhido) **N vezes** e registra: tempo total por consulta, `sources_status.duration_ms`, número de resultados por fonte, **número de duplicatas fundidas**, fontes que falharam. Saída em `docs/evidencias/medicao/resultado-AAAAMMDD.csv` e resumo em Markdown.
2. **Roteiro da medição manual** (`docs/evidencias/medicao/ROTEIRO_MANUAL.md`) para o desenvolvedor ou voluntários: para cada consulta, buscar **manualmente** nas seis fontes (abrir cada site, digitar, anotar o tempo com cronômetro até ter a lista de resultados relevantes copiada e deduplicada à mão) e depois fazer o mesmo na aplicação. Planilha-modelo com colunas: consulta, método (manual/aplicação), pessoa, tempo, nº de resultados úteis, observações.
3. Script `scripts/summarize_manual.py` que lê a planilha preenchida e calcula média, mínimo e máximo por método e consulta.
4. Relatório `docs/evidencias/medicao/RELATORIO.md` com: método, limitações (poucos participantes e consultas; rede e carga variáveis; o índice local depende da colheita feita), e os números **exatamente como medidos**. Sem generalizar.

**Arquivos:** `scripts/measure_search.py`, `scripts/summarize_manual.py`, `docs/evidencias/medicao/*`, `tests/unit/test_measure_scripts.py` (com dados falsos).

**Critérios de aceite**
- [ ] Os scripts rodam e geram CSV/Markdown.
- [ ] O roteiro manual e a planilha-modelo existem.
- [ ] `RELATORIO.md` só contém números que vieram dos arquivos medidos.
- [ ] As limitações estão escritas.

**Testes obrigatórios:** testes unitários dos scripts com dados falsos.
**Proibido nesta OS:** preencher o relatório com números inventados, estimados ou copiados de outros trabalhos; escrever "reduz em X%" sem os dados.
**Evidência para o TCC:** o `RELATORIO.md` (4.1, 4.2 e a justificativa). Se o desenvolvedor não fizer a medição manual, o TCC deve **remover** a afirmação de redução de tempo.
**Commit:** `feat(os-033): instrumentos de medição de busca manual versus aplicação`

---

# FASE 6 — ENTREGA

## OS-034 — Documentação do projeto

**Depende de:** OS-001 a OS-033.
**Rastreabilidade no TCC:** 2.3 (OpenAPI, REST); 4.3; Introdução (API pública).

**Objetivo:** deixar o sistema compreensível e executável por outra pessoa.

**Tarefas**
1. `README.md` completo: o que é; funcionalidades; requisitos (Python, PostgreSQL); instalação passo a passo; variáveis de ambiente (tabela); **como obter as chaves gratuitas** (OpenAlex e CORE); **como configurar e colher as fontes OAI-PMH** (`config/oai_sources.yml`, `identify`, `run`, `status`, periodicidade sugerida com `cron` do sistema); como rodar, testar e verificar qualidade; estrutura de pastas; licença (**perguntar** ao desenvolvedor qual licença; não escolher sozinho).
2. `docs/EXECUCAO.md` revisado (banco, migrações, colheita, execução em produção simples com `uvicorn` atrás de um proxy reverso; **sem** exigir Docker).
3. `docs/API.md`: visão humana da API (rotas, parâmetros, exemplos com `curl` e JavaScript `fetch`, formato de erro, autenticação, limites), alinhada ao OpenAPI; conferir por script que **toda rota do OpenAPI** aparece em `API.md`.
3a. **Autoavaliação da API** em `docs/API.md#conformidade-rest`, para sustentar a seção 4.3: percorrer as rotas e registrar, uma por uma, (a) se o verbo HTTP corresponde à operação, (b) se o caminho nomeia um **substantivo no plural** e não um verbo, (c) se o código de status é o adequado, (d) se a resposta é sem estado. Rodríguez et al. (2016) mostram que APIs declaradas REST frequentemente não seguem os princípios, e Palma et al. (2017) tratam de antipadrões na **nomeação** de recursos: esta tabela é a evidência de que o trabalho verificou isso no próprio sistema, em vez de apenas citar. Corrigir o que estiver fora e anotar a correção.
4. `docs/DECISOES.md` revisado e organizado, **incluindo**: URLs OAI-PMH reais de cada fonte, divergências entre este arquivo e a realidade, limitações encontradas (ex.: fonte sem OAI-PMH, registros sem ano ou resumo) e pendências.
5. `docs/ARQUITETURA.md` com os diagramas (Mermaid): componentes, sequência da busca, modelo de dados, fluxo de colheita.
6. Seção "Limitações conhecidas": total estimado; fontes locais dependem da colheita; OpenAlex e CORE dependem de chaves e limites; registros institucionais sem resumo/ano; raspagem desligada por padrão.
7. Seção "Trabalhos futuros" **idêntica** à do TCC (aplicativo móvel nativo, recomendação, repositórios de outras universidades, alertas, integração direta com gerenciadores, outros idiomas e 2FA).

**Arquivos:** `README.md`, `docs/*.md`, `scripts/check_api_docs.py`.

**Critérios de aceite**
- [ ] Alguém sem contexto consegue instalar e rodar seguindo só o README (o desenvolvedor testa em uma pasta limpa e anota no relatório).
- [ ] `scripts/check_api_docs.py` confirma que todas as rotas estão em `API.md`.
- [ ] Todos os `[VERIFICAR]` deste arquivo estão resolvidos em `DECISOES.md` ou listados como pendentes.
- [ ] Nenhuma afirmação numérica sem fonte de medição.

**Testes obrigatórios:** `check_api_docs.py` como teste.
**Proibido nesta OS:** escolher licença sem perguntar; copiar texto da documentação das fontes sem citar.
**Evidência para o TCC:** diagramas e `API.md` (4.3).
**Commit:** `docs(os-034): documentação do projeto, da API e da arquitetura`

---

## OS-035 — Revisão final e pacote de evidências

**Depende de:** todas as anteriores.
**Rastreabilidade no TCC:** 4 e 5 (Resultados, Discussões e Conclusões).

**Objetivo:** verificar o conjunto contra o TCC e entregar o pacote de evidências para o desenvolvedor redigir o capítulo 4.

**Tarefas**
1. Rodar tudo: `make check`, `make sast`, testes e2e e de acessibilidade. Registrar os resultados.
2. **Matriz de conformidade com o TCC** em `docs/CONFORMIDADE_TCC.md`: cada item de 2 (E1 a E15) → OS → teste → status (`Atende`, `Atende parcialmente`, `Não atende`) e **observação honesta** (ex.: "fonte UESPI sem OAI-PMH: `enabled: false`").
3. Verificar que **nada fora do escopo** (seção 3) foi implementado: varrer rotas, tabelas, dependências e código por Redis, Celery, MARCXML, filas, 2FA, i18n, recomendação, alertas e integração direta com gerenciadores.
4. Conferir **dependências** contra a seção 4 (mais as duas adições permitidas: `pyyaml` e a biblioteca de HTML).
5. **Pacote de evidências** em `docs/evidencias/PACOTE.md`: índice com, para cada seção 4.1 a 4.6, os arquivos que a sustentam (capturas, tabelas, diagramas, medições, relatórios de ferramentas) e **o que ainda falta ser feito pelo desenvolvedor** (medição manual, teste de leitor de tela, importação em gerenciador, validação com chaves reais, fixtures reais).
6. **Lista de pendências do desenvolvedor** consolidada (todos os `[VERIFICAR]` não resolvidos e passos manuais).
7. **Lista de divergências TCC ↔ sistema**: onde o sistema fez algo diferente do que o TCC afirma, para o autor ajustar o texto (ex.: fonte que não expõe OAI-PMH; tipo `other` para monografias; total estimado).
8. Etiqueta `v1.0.0` no Git **somente se o desenvolvedor pedir**.

**Arquivos:** `docs/CONFORMIDADE_TCC.md`, `docs/evidencias/PACOTE.md`, `docs/os/OS-035-relatorio.md`.

**Critérios de aceite**
- [ ] A matriz cobre E1 a E15 com status honesto.
- [ ] A varredura do escopo não encontra itens da seção 3.
- [ ] O pacote de evidências aponta arquivos existentes.
- [ ] As pendências do desenvolvedor estão listadas.

**Testes obrigatórios:** todos os da suíte, mais a varredura de escopo como teste (`tests/unit/test_scope_guard.py`).
**Proibido nesta OS:** marcar "Atende" sem prova; esconder limitação.
**Evidência para o TCC:** o pacote e a matriz.
**Commit:** `docs(os-035): revisão final, matriz de conformidade e pacote de evidências`

---

## OS-036 — Avaliação de usabilidade

**Depende de:** OS-022 a OS-026 (ou, no mínimo, OS-021 a OS-023 da Fatia 1).
**Rastreabilidade no TCC:** 2.5 (Cybis, Betiol e Faust, 2010: métodos de ergonomia e usabilidade; Prates e Barbosa, 2003: conceitos e métodos de avaliação de interfaces); 4.4.

**Motivo desta OS:** o referencial cita duas obras sobre **avaliação** de interfaces, mas nenhuma OS avaliava usabilidade — só acessibilidade (OS-031) e tempo (OS-033). Sem esta OS, a seção 4.4 cita Cybis e Prates e Barbosa sem nada ter avaliado.

**Objetivo:** avaliar a interface por um método reconhecido e registrar os problemas encontrados e as correções feitas.

**Decisões já tomadas:** **avaliação heurística** como método principal, por ser aplicável sem participantes; **teste com usuários** como complemento opcional, se o desenvolvedor conseguir de 3 a 5 colegas. Sem questionário padronizado proprietário.

**Tarefas**
1. `docs/USABILIDADE.md` com uma tabela de avaliação heurística: uma linha por heurística, por tela (busca, resultados, filtros, favoritos, conta), com `Atende / Problema / Não se aplica`, descrição do problema, severidade (1 a 3, definida por você) e decisão (`corrigido`, `aceito` com justificativa).
2. **Usar o método descrito na fonte que você tem em mãos.** Se adotar as heurísticas de Nielsen, **cite Nielsen**, não Cybis nem Prates e Barbosa; se usar o roteiro de uma dessas duas obras, cite a obra e diga qual roteiro. Registre a escolha em `docs/DECISOES.md`.
3. Corrigir os problemas de severidade 3 e 2; os de severidade 1 ficam corrigidos ou justificados.
4. **Complemento opcional (passo manual):** roteiro de 4 tarefas em `docs/USABILIDADE.md#teste-com-usuarios` (buscar um tema; filtrar por ano; salvar um favorito; exportar em BibTeX), com registro, por participante, de conclusão da tarefa, dúvidas e comentários. **Sem** medir tempo aqui (isso é a OS-033) e **sem** calcular porcentagem com 3 a 5 pessoas.
5. Anotar as limitações: avaliação feita pelo próprio autor, amostra pequena, sem especialista em usabilidade.

**Arquivos:** `docs/USABILIDADE.md`, mais as correções de interface que surgirem.

**Critérios de aceite**
- [ ] A tabela cobre todas as telas existentes.
- [ ] Cada problema tem severidade e decisão.
- [ ] O método está citado com a fonte que você realmente usou.
- [ ] As limitações estão escritas.
- [ ] Nenhum número percentual calculado sobre menos de 20 participantes.

**Testes obrigatórios:** nenhum automatizado; as correções de interface entram nos testes das OS-022 a 026.
**Proibido nesta OS:** inventar participantes; apresentar opinião própria como resultado de teste; citar Cybis ou Prates e Barbosa para um método que você não aplicou.
**Evidência para o TCC:** `docs/USABILIDADE.md` (base da seção 4.4).
**Commit:** `docs(os-036): avaliação de usabilidade e correções de interface`

---

## OS-037 — Implantação, colheita agendada e backup

**Depende de:** OS-034.
**Rastreabilidade no TCC:** 3 (a aplicação precisa estar acessível para ser demonstrada); 4.1 e 4.2 (as fontes OAI só têm resultado se a colheita rodar periodicamente); 4.6 (disponibilidade e proteção dos dados, Brasil, 2018, art. 46).

**Motivo desta OS:** a colheita OAI-PMH era só um comando manual, e não havia nada sobre colocar o sistema no ar nem sobre backup. Sem isso, o índice local envelhece e os dados do usuário não têm cópia.

**Objetivo:** deixar o sistema em execução contínua, com a colheita periódica e o banco com cópia de segurança.

**Decisões já tomadas:** sem Docker como requisito e sem serviço de fila; o agendamento usa o **cron do sistema operacional** e o serviço usa o **systemd** (ou o equivalente do ambiente onde você for publicar); um único processo do Uvicorn (ver OS-014, item 5a).

**Tarefas**
1. `docs/IMPLANTACAO.md`: requisitos do servidor; criação do usuário do sistema sem privilégios; instalação; variáveis de ambiente em produção (`APP_ENV=production`, `DOCS_ENABLED`, `ALLOWED_ORIGINS` sem `*`, `SECRET_KEY` gerada no servidor); Uvicorn atrás de um proxy reverso (Nginx ou Caddy) com HTTPS e certificado gratuito; `Strict-Transport-Security` ativo.
2. Arquivo de serviço de exemplo (`deploy/academic-search.service`) com reinício automático e `EnvironmentFile`.
3. Exemplo de configuração do proxy reverso (`deploy/nginx.conf.example`) que encaminha para o Uvicorn, serve o frontend e **não** sobrescreve os cabeçalhos de segurança da OS-014.
4. **Colheita agendada:** `deploy/crontab.example` com `run-all` em horário de baixo movimento (uma vez por dia é suficiente; a colheita é incremental) e com a saída indo para um arquivo de log. Documentar como ver o resultado com a CLI `status` (OS-009).
5. **Backup:** script `scripts/backup_db.sh` com `pg_dump` compactado, nome com data, retenção local de 7 cópias, e **teste de restauração** documentado passo a passo (um backup não testado não é backup). Escrever onde as cópias ficam e quem tem acesso.
6. `docs/IMPLANTACAO.md#verificacao`: lista do que conferir depois de publicar — `health` responde, `/api/docs` conforme `DOCS_ENABLED`, HTTPS válido, cabeçalhos presentes, uma busca real funciona, a colheita rodou, um backup foi gerado e restaurado.
7. Se você for apenas rodar na própria máquina para a defesa, **diga isso** no TCC em vez de descrever um ambiente que não existe.

**Arquivos:** `docs/IMPLANTACAO.md`, `deploy/*`, `scripts/backup_db.sh`.

**Critérios de aceite**
- [ ] O serviço sobe sozinho depois de reiniciar a máquina.
- [ ] A colheita agendada rodou ao menos uma vez e a CLI `status` mostra o resultado.
- [ ] Um backup foi gerado **e restaurado** em um banco de teste, com o procedimento registrado.
- [ ] A lista de verificação está preenchida com o resultado real.
- [ ] Nenhum segredo aparece nos arquivos de `deploy/`.

**Testes obrigatórios:** `scripts/backup_db.sh` com teste que verifica a geração do arquivo; o restante é verificação manual registrada.
**Proibido nesta OS:** exigir Docker; publicar com `DEBUG` ligado, `ALLOWED_ORIGINS=*` ou chave de exemplo; descrever uma implantação que você não fez.
**Evidência para o TCC:** a lista de verificação preenchida e o registro do teste de restauração (4.1 e 4.6).
**Commit:** `chore(os-037): implantação, colheita agendada e backup`

---

# 9. APÊNDICES

## 9.1 Ordem e dependências (resumo)

| Fase | OS | Resultado |
|---|---|---|
| F0 Fundação | 001–004 | Projeto, configuração, banco e modelos |
| F1 Domínio | 005–013 | Normalização, conectores (OpenAlex, CORE, OAI local), colheita, deduplicação, orquestrador, raspagem |
| F2 API | 014–020 | FastAPI, autenticação, busca, favoritos, histórico, exportação, LGPD |
| F3 Frontend | 021–026 | Interface web completa |
| F4 Segurança | 027–029 | OWASP 2017, análise estática, eventos |
| F5 Qualidade | 030–033 | Testes, acessibilidade, e2e e capturas, medição |
| F6 Entrega | 034–037 | Documentação, usabilidade, implantação e pacote de evidências |

**Ordem real no fim:** OS-034 → OS-036 → OS-037 → **OS-035 por último** (a revisão final precisa que a usabilidade e a implantação já existam para entrar na matriz de conformidade).

**Para ter capturas antes de tudo isso,** use a Fatia 1 (seção 7.1).

## 9.2 Passos manuais do desenvolvedor (a IA não consegue fazer)

1. Criar as chaves gratuitas do **OpenAlex** e do **CORE** e colocá-las no `.env`.
2. Descobrir e **confirmar os endereços OAI-PMH** do SciELO, BDTD (IBICT), UFPI e UESPI (`identify`), e preencher `config/oai_sources.yml`. Se algum não expuser OAI-PMH, avisar para decidir o que fazer.
3. Rodar a **colheita** de cada fonte e conferir `status`.
4. Salvar **fixtures reais** (uma página por fonte) para substituir as sintéticas.
5. Testes de **acessibilidade humana** (teclado, leitor de tela, zoom).
6. **Importar** os arquivos `.bib` e `.ris` num gerenciador de referências.
7. Fazer a **medição manual** (OS-033).
8. Preencher o **contato do responsável** na política de privacidade.
9. Escolher a **licença** do repositório.
10. Atualizar o TCC com as divergências listadas na OS-035.
11. Conseguir de 3 a 5 colegas para o teste de usabilidade da OS-036, se quiser o complemento opcional.
12. Definir onde o sistema vai rodar (servidor, máquina da universidade ou a sua própria) e, se for a sua própria, dizer isso no TCC (OS-037).
13. Testar a restauração de um backup (OS-037).

## 9.3 Glossário

- **OAI-PMH:** protocolo de colheita de metadados entre repositórios (Lagoze et al., 2002).
- **`oai_dc`:** formato mínimo de metadados Dublin Core exigido pelo OAI-PMH.
- **MTD-BR3:** padrão de metadados da BDTD, com 28 elementos (18 obrigatórios) (Almeida e Dias, 2023).
- **BDTD:** Biblioteca Digital Brasileira de Teses e Dissertações, mantida pelo IBICT.
- **Índice local:** tabela `oai_records` com os metadados colhidos, usada para a busca de texto completo.
- **Fixture:** resposta gravada de uma fonte, usada nos testes sem rede.
- **Colheita (harvest):** cópia periódica dos metadados de uma fonte OAI-PMH para o banco local.

## 9.4 Referências usadas neste arquivo (para o desenvolvedor conferir)

- ALMEIDA, L. S.; DIAS, T. M. R. Análise dos mecanismos de busca de repositórios institucionais de acesso aberto. *RDBCI: Revista Digital de Biblioteconomia e Ciência da Informação*, 2023. (conferir volume e DOI)
- UNIVERSIDADE ESTADUAL DO PIAUÍ. Conselho de Ensino, Pesquisa e Extensão. Resolução CEPEX nº 034, de 21 de agosto de 2024.
- Demais fontes: as do TCC (Lagoze et al., 2002; Knoth e Zdrahal, 2012; Priem, Piwowar e Orr, 2022; Fielding, 2000; Bray, 2017; Brasil, 2018; OWASP, 2017; W3C, 2014 e 2018; Nunes et al., 2018).

— **Fim do arquivo de Ordens de Serviço** —
