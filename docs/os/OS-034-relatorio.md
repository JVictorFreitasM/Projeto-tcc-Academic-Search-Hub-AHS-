# OS-034 — Documentação do projeto, da API e da arquitetura

## O que foi feito

- `README.md` completo: o que é, funcionalidades, requisitos, instalação passo a passo, tabela das
  variáveis de ambiente, como obter as chaves gratuitas (OpenAlex e CORE), como configurar e colher as
  fontes OAI-PMH (`identify`, `sets`, `run`, `run-all`, `status`, periodicidade com `cron`), como
  rodar, testar e verificar a qualidade, estrutura de pastas, limitações conhecidas, trabalhos
  futuros e licença.
- `LICENSE` (MIT, escolhida pelo desenvolvedor em 14/10/2026) e `license = "MIT"` no `pyproject.toml`.
- `docs/EXECUCAO.md` revisado: banco, `.env`, migrações, colheita (incremental, `--full`, status,
  falhas), servidor em desenvolvimento e em produção simples (Uvicorn atrás de proxy reverso, um
  processo, sem Docker). Aponta para `docs/IMPLANTACAO.md` (OS-037) para serviço, proxy, colheita
  agendada e backup.
- `docs/API.md`: visão humana das 22 operações (autenticação, formato de erro, limites, parâmetros,
  exemplos com `curl` e `fetch`) e a autoavaliação REST (`#conformidade-rest`).
- `scripts/check_api_docs.py` e `tests/unit/test_api_docs.py`: toda operação do OpenAPI precisa
  aparecer em `docs/API.md`, na seção "Rotas" **e** na tabela de conformidade REST (8 testes).
- `docs/ARQUITETURA.md` com quatro diagramas Mermaid: componentes, sequência da busca, modelo de
  dados e fluxo de colheita. Conferidos contra o código (pesos do índice, estados da colheita,
  regra incremental, limite de 50 MB por resposta OAI, chaves de deduplicação).
- `docs/PENDENCIAS_DESENVOLVEDOR.md`: lista de tudo o que só o desenvolvedor pode fazer, com os
  `[VERIFICAR]` ainda abertos.

## Achados ao documentar (registrados em `docs/DECISOES.md`)

1. **Autoavaliação REST:** das 22 rotas, 4 têm verbo no caminho (`/auth/register`, `/auth/login`,
   `/favorites/export`, `/export`); 12 nomeiam substantivo no singular ou singleton (ressalva);
   5 seguem o padrão por completo; `/health` não se aplica. No verbo HTTP: 19 atendem e 3 atendem
   com ressalva. Nenhuma rota foi renomeada: os nomes vêm das OS e o frontend, os testes e o TCC
   dependem deles. A decisão (manter ou renomear) ficou para o autor.
2. **`/health` responde 200 com o banco fora do ar** (`database: error`), decisão da OS-014; o usual
   seria 503. Anotado na tabela.
3. **`duration_ms` por fonte só é enviado com `APP_ENV=development`.** Afeta a medição da OS-033;
   a documentação da medição foi atualizada com o aviso.
4. O total de resultados é a soma dos totais das fontes (inclui duplicatas); está dito no `API.md` e
   nas limitações.

## O que NÃO foi feito

- **Critério "alguém sem contexto instala seguindo só o README":** não verificado. É teste do
  desenvolvedor em pasta limpa, que deve anotar o resultado aqui (pendência listada).
- Os passos de cadastro nos sites do OpenAlex e do CORE não foram refeitos; o README diz isso.
- Os exemplos de `curl` e `fetch` não foram executados contra um servidor com chaves reais; os
  formatos de pedido e resposta vêm do OpenAPI e dos esquemas da aplicação.
- Nenhum texto foi copiado da documentação das fontes.

## `[VERIFICAR]` ainda abertos

Listados em `docs/PENDENCIAS_DESENVOLVEDOR.md`, seção 7 (filtros do OpenAlex e do CORE, importação
no Zotero/Mendeley, endereços OAI).
