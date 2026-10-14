# Academic Search Hub

Aplicação web e API pública para **buscar trabalhos acadêmicos em uma única consulta** em
repositórios de acesso aberto: CORE, SciELO, OpenAlex, BDTD (IBICT) e os repositórios da UFPI e da
UESPI. Os resultados vêm unificados, sem duplicatas, e podem ser filtrados, salvos como favoritos,
anotados e exportados para BibTeX, RIS, CSV e JSON.

Projeto do TCC de João Victor de Freitas Martins (UESPI, Tecnólogo em Sistemas para a Internet).
Licença: [MIT](LICENSE).

## Funcionalidades

- **Busca unificada** em todas as fontes ativas, com filtros por ano e tipo, ordenação por relevância
  ou por ano e paginação. Se uma fonte falha, as outras continuam respondendo e o aviso mostra qual
  falhou.
- **Duplicatas fundidas** por DOI e, na falta dele, por título, ano e sobrenome do primeiro autor.
- **Fontes ao vivo** (OpenAlex, CORE) e **fontes colhidas por OAI-PMH** (SciELO, BDTD, UFPI, UESPI),
  pesquisadas num índice local com busca em português sem acentos.
- **Conta opcional:** favoritos com anotações, histórico de buscas e exportação dos favoritos.
  Visitantes buscam e exportam os resultados sem login.
- **Privacidade (LGPD):** consentimento no cadastro e os direitos de acesso, correção, portabilidade
  e eliminação em "Minha conta".
- **API REST documentada** (OpenAPI/Swagger em `/api/docs`) e **frontend sem build**, acessível por
  teclado e verificado com o axe.

## Requisitos

- Python 3.11 ou superior
- [uv](https://docs.astral.sh/uv/) (gerenciador de dependências)
- PostgreSQL 14 ou superior, com as extensões `unaccent`, `pg_trgm` e `pgcrypto`
- Para os testes de interface: Chromium do Playwright (`uv run playwright install chromium`)

Não é preciso Docker nem Redis.

## Instalação

Passo a passo (os comandos valem no Windows, Linux e macOS; no Windows não há `make`, por isso os
alvos ficam em `tasks.py`):

1. **Dependências**
   ```
   python tasks.py install
   ```
2. **Banco de dados:** crie o usuário, os bancos e as extensões (ver `docs/EXECUCAO.md`, seção 1).
3. **Configuração:** copie `.env.example` para `.env` e preencha ao menos `SECRET_KEY` (mínimo de 32
   caracteres aleatórios) e `DATABASE_URL`. Nunca faça commit do `.env`.
   Para gerar uma chave: `uv run python -c "import secrets; print(secrets.token_urlsafe(48))"`.
4. **Migrações**
   ```
   uv run alembic upgrade head
   ```
5. **Subir o servidor**
   ```
   python tasks.py run
   ```
   Abra <http://127.0.0.1:8000> (a documentação da API fica em <http://127.0.0.1:8000/api/docs>).

Sem as chaves do OpenAlex e do CORE e sem a colheita OAI, a aplicação sobe, mas essas fontes
aparecem como indisponíveis.

## Variáveis de ambiente

Todas ficam no `.env` (modelo em `.env.example`). Valores inválidos impedem a inicialização, e a
mensagem cita só o nome da variável, nunca o valor.

| Variável | Padrão | Para que serve |
|---|---|---|
| `APP_ENV` | `development` | `development` ou `production`. Em produção, `SECRET_KEY` é obrigatória, `ALLOWED_ORIGINS` não aceita `*` e a resposta passa a enviar HSTS |
| `SECRET_KEY` | vazio | Assinatura do token JWT; 32 caracteres ou mais fora do desenvolvimento |
| `DATABASE_URL` | `postgresql+psycopg://user:pass@localhost:5432/academic_search` | Conexão com o PostgreSQL |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Validade do token de acesso |
| `ALLOWED_ORIGINS` | `http://localhost:8000` | Origens permitidas no CORS, separadas por vírgula |
| `OPENALEX_API_KEY` | vazio | Chave do OpenAlex (sem ela a fonte fica indisponível) |
| `CORE_API_KEY` | vazio | Chave do CORE (sem ela a fonte fica indisponível) |
| `OAI_SOURCES_FILE` | `config/oai_sources.yml` | Arquivo com as fontes OAI-PMH |
| `CONTACT_EMAIL` | vazio | E-mail de contato enviado no `User-Agent` da colheita e da raspagem |
| `OAI_HARVEST_DELAY_SECONDS` | `1` | Pausa entre requisições de colheita ao mesmo servidor |
| `SCRAPING_ENABLED` | `false` | Liga a raspagem complementar de resumos |
| `SOURCE_TIMEOUT_SECONDS` | `10` | Tempo limite por fonte de busca |
| `DEFAULT_PAGE_SIZE` | `20` | Tamanho de página padrão |
| `MAX_PAGE_SIZE` | `50` | Tamanho de página máximo |
| `RATE_LIMIT_SEARCH` | `60/minute` | Limite de buscas por IP |
| `RATE_LIMIT_AUTH` | `5/minute` | Limite de login e cadastro por IP |
| `LOG_LEVEL` | `INFO` | Nível de log |
| `DOCS_ENABLED` | `true` | Liga a documentação em `/api/docs` |
| `TEST_DATABASE_URL` | vazio | Banco usado só nos testes de integração e de ponta a ponta |
| `PRIVACY_POLICY_VERSION` | `1.0` | Versão da política registrada no consentimento |

## Chaves gratuitas (OpenAlex e CORE)

As duas fontes ao vivo pedem uma chave gratuita:

- **OpenAlex:** crie uma conta em <https://openalex.org> e copie a chave para `OPENALEX_API_KEY`.
- **CORE:** registre-se em <https://core.ac.uk/services/api> e copie a chave para `CORE_API_KEY`.

Os passos exatos de cada site podem mudar; consulte a documentação deles. Esses cadastros não foram
refeitos ao escrever este README (pendência do desenvolvedor, em `docs/PENDENCIAS_DESENVOLVEDOR.md`).
Não publique as chaves: elas ficam só no `.env`.

## Fontes OAI-PMH: configurar e colher

SciELO, BDTD, UFPI e UESPI são colhidas por OAI-PMH para uma tabela local e pesquisadas ali.

1. Em `config/oai_sources.yml`, cada fonte tem `base_url`, `metadata_prefix` (`oai_dc`), `set_spec`
   opcional, `enabled`, `default_type` e `type_map`. Os endereços vêm como `TODO-VERIFICAR`: confirme
   cada um com o `Identify` do servidor, não use endereços chutados.
2. Confira o servidor e os conjuntos:
   ```
   uv run python -m app.harvest.cli identify <fonte>
   uv run python -m app.harvest.cli sets <fonte>
   ```
3. Teste sem gravar: `uv run python -m app.harvest.cli run <fonte> --limit 50 --dry-run`
4. Troque `enabled` para `true` e colha:
   ```
   uv run python -m app.harvest.cli run <fonte>        # uma fonte (incremental)
   uv run python -m app.harvest.cli run <fonte> --full # ignora a última colheita
   uv run python -m app.harvest.cli run-all            # todas as habilitadas
   uv run python -m app.harvest.cli status             # última colheita e total por fonte
   ```
5. **Periodicidade (sugestão):** uma colheita por dia, de madrugada, com o agendador do sistema; como
   ela é incremental, uma vez por dia basta. Exemplo de `cron` (Linux, todo dia às 3h):
   ```
   0 3 * * *  cd /caminho/do/projeto && uv run python -m app.harvest.cli run-all
   ```
   No Windows, use o Agendador de Tarefas com o mesmo comando. A implantação completa (serviço,
   proxy, colheita agendada e backup) está em `docs/IMPLANTACAO.md`.

Fontes ainda não colhidas aparecem como indisponíveis na busca, sem derrubá-la.

## Testes e qualidade

| Comando | O que faz |
|---|---|
| `python tasks.py check` | `ruff`, `ruff format --check`, `mypy` (estrito) e toda a suíte com cobertura mínima de 80% |
| `python tasks.py test` | Toda a suíte, com cobertura |
| `python tasks.py test-unit` / `test-integration` / `test-contract` | Só um tipo de teste |
| `python tasks.py test-e2e` / `test-a11y` | Navegador (Chromium): telas, fluxos e axe |
| `python tasks.py test-stats` | Conta testes por tipo e resume a cobertura medida |
| `python tasks.py sast` | Análise estática (bandit, semgrep, pip-audit) com resumo |
| `python tasks.py lint` / `format` / `typecheck` | Partes do `check` |
| `uv run python scripts/check_api_docs.py` | Confere que toda rota do OpenAPI está em `docs/API.md` |

Os testes de integração precisam de `TEST_DATABASE_URL`; sem ela, são **pulados**. Nenhum teste usa
a internet. Detalhes em `docs/TESTES.md`.

## Estrutura de pastas

```
app/            código da aplicação (api, services, connectors, harvest, scraping, models, core...)
frontend/       páginas e módulos JavaScript (sem build)
migrations/     migrações do Alembic
config/         fontes OAI-PMH (oai_sources.yml)
deploy/         exemplos de implantação: serviço systemd, proxy reverso, cron (docs/IMPLANTACAO.md)
scripts/        capturas de tela, medição, SAST, backup do banco, verificação da documentação
tests/          unit, integration, contract, e2e e a11y
docs/           documentação (veja abaixo) e evidências para o TCC
```

## Documentação

| Arquivo | Assunto |
|---|---|
| `docs/EXECUCAO.md` | Banco, migrações, colheita, execução simples em produção |
| `docs/API.md` | Rotas, exemplos, erros, limites e autoavaliação REST |
| `docs/ARQUITETURA.md` | Componentes, sequência da busca, modelo de dados, fluxo de colheita |
| `docs/CONTINUAR_EM_CASA.md` | Onde o projeto está, como preparar outro computador e o que falta, em ordem |
| `docs/IMPLANTACAO.md` | Serviço, proxy com HTTPS, colheita agendada, backup e restauração, lista de verificação |
| `docs/USABILIDADE.md` | Avaliação heurística (Nielsen), problemas, correções e roteiro de teste com usuários |
| `docs/FONTES_CANDIDATAS.md` | Fontes gratuitas que dá para adicionar (OAI-PMH e REST), verificadas |
| `docs/SEGURANCA.md` | OWASP Top 10 (2017) verificado por teste e análise estática |
| `docs/LGPD.md` | Dados tratados, base legal e direitos do titular |
| `docs/ACESSIBILIDADE.md` | Verificação com axe, checklist WCAG 2.1 e testes manuais |
| `docs/TESTES.md` | Como rodar e o que cada tipo de teste cobre |
| `docs/DECISOES.md` | Decisões e divergências, com data e motivo |
| `docs/PENDENCIAS_DESENVOLVEDOR.md` | O que só o desenvolvedor pode fazer |

## Limitações conhecidas

- **O total de resultados é uma estimativa:** soma os totais informados por cada fonte e pode incluir
  duplicatas.
- **As fontes locais dependem da colheita:** BDTD, UFPI, UESPI e SciELO só respondem com o que foi
  colhido antes; uma colheita antiga ou parcial muda os resultados.
- **OpenAlex e CORE dependem de chaves e de limites das próprias fontes:** sem chave a fonte fica
  indisponível; com chave, vale o limite de requisições que cada uma impõe.
- **Registros institucionais podem vir sem resumo ou sem ano:** o que a fonte não informa não é
  inventado.
- **A raspagem de resumos vem desligada por padrão** (`SCRAPING_ENABLED=false`) e deve ser usada só
  onde os termos da fonte permitirem.
- **O limite de requisições é em memória:** vale para um único processo do servidor.
- **Não há recuperação de senha:** o sistema não envia e-mail; o cadastro avisa. Quem esquece a
  senha não tem como recuperar a conta.
- **Fontes OAI reais ainda não validadas:** os endereços de BDTD, UFPI, UESPI e SciELO estão por
  confirmar e as fontes seguem desligadas até isso (ver `docs/PENDENCIAS_DESENVOLVEDOR.md`).

## Trabalhos futuros

Aplicativo móvel nativo; recomendação de trabalhos; repositórios de outras universidades; alertas;
integração direta com gerenciadores de referências; outros idiomas; autenticação em dois fatores
(2FA).

## Licença

[MIT](LICENSE) © 2026 João Victor de Freitas Martins.
