# Pendências do desenvolvedor

Lista do que só você pode fazer (a IA não tem as chaves, as fontes reais nem pessoas para testar).
Marque `[x]` quando terminar e escreva a data e uma observação. A OS-035 consolidou esta lista com
os `[VERIFICAR]` que restaram e com o pacote de evidências do TCC (`docs/evidencias/PACOTE.md`);
a matriz E1 a E15 e as divergências TCC ↔ sistema estão em `docs/CONFORMIDADE_TCC.md`.

Última atualização: 14/10/2026 (revisão final, OS-035).

> Para retomar o trabalho em outro computador, com a ordem sugerida e o passo a passo, veja
> `docs/CONTINUAR_EM_CASA.md`.

## O que mais pesa para o TCC (resumo)

1. **Chaves e fontes reais** (seção 2): sem elas, nenhuma das seis fontes foi validada com dados reais.
2. **Medição manual de tempo** (seção 4): sem ela, o TCC não pode afirmar redução de tempo de busca.
3. **Contato do responsável na política de privacidade** (seção 1): hoje aparece um marcador na página.
4. **Testes de acessibilidade com pessoas** (seção 3).
5. **Decisões suas** (seções 1 e 8): nomes das 4 rotas, caixa "manter conectado", fontes extras.
6. **Onde o sistema vai rodar** (seção 9): se for só na sua máquina, o TCC deve dizer isso.

## 1. Decisões que dependem de você

- [x] **Licença do projeto: MIT** (escolhida por você em 14/10/2026). O arquivo `LICENSE` foi criado
  com o titular "João Victor de Freitas Martins" e o ano de 2026.
- [ ] **Conferir o `LICENSE`:** o nome do titular está correto? (veio do README do projeto) E confirme
  com o orientador se a UESPI tem regra sobre a licença ou a propriedade intelectual de trabalhos
  de conclusão.
- [ ] **Decidir sobre os nomes de 4 rotas da API** (autoavaliação em `docs/API.md#conformidade-rest`).
  `/auth/register`, `/auth/login`, `/favorites/export` e `/export` têm um verbo no caminho, o que
  foge da convenção REST de substantivos no plural. Foram mantidos porque as OS e o TCC os definem.
  Opção A: manter e escrever no TCC que a API segue REST nos verbos e no formato, mas não na
  nomeação dessas rotas. Opção B: renomear (por exemplo `/users`, `/sessions`, `/exports`), o que
  muda frontend, testes e documentos. A IA faz a B se você pedir.
- [ ] **Contato do responsável** na política de privacidade (`app/content/privacy_pt.md`): nome e
  e-mail de quem responde pelos dados (LGPD, art. 18).
- [ ] **Definir as 5 consultas** da medição, sobre temas dos cursos da UESPI, em
  `docs/evidencias/medicao/consultas.txt`. Use as mesmas na medição manual e na da aplicação.
- [ ] **Definir o critério de "resultado útil"** (uma ou duas frases) em
  `docs/evidencias/medicao/ROTEIRO_MANUAL.md`, antes de medir.

## 2. Chaves e fontes reais (OS-007 a OS-010)

- [ ] **Chave do OpenAlex** (`OPENALEX_API_KEY` no `.env`) e gravar uma resposta real em
  `tests/fixtures/openalex/` no lugar da fixture sintética.
- [ ] **Chave do CORE** (`CORE_API_KEY` no `.env`) e gravar uma resposta real em
  `tests/fixtures/core/` no lugar da fixture sintética.
- [ ] **Trocar as fixtures sintéticas** por respostas reais: `STRICT_FIXTURES=1 uv run pytest
  tests/contract` lista as que faltam.
- [ ] **Endereços OAI-PMH reais** de cada fonte, em `config/oai_sources.yml`, e depois habilitar
  (`enabled: true`) e rodar a colheita. Situação encontrada em **14/10/2026** (detalhes em
  `docs/FONTES_CANDIDATAS.md`):
  - **UFPI** e **UESPI:** o OAI responde (`https://repositorio.ufpi.br/oai/request` e
    `https://repositorio.uespi.br/oai/request`), mas **não devolve registros** (`noRecordsMatch`).
    Pedir ao administrador para reindexar o OAI e testar de novo com `--dry-run`;
  - **BDTD:** desafio anti-robô (sem XML);
  - **SciELO:** nenhum endereço OAI respondeu; há API REST (ArticleMeta), sem busca por texto.
  Enquanto não validadas, ficam `enabled: false`.
- [ ] **Decidir se amplia as fontes** além das seis do TCC (UFPE, UFMG, DOAJ...). Ver
  `docs/FONTES_CANDIDATAS.md`, seção 5.
- [ ] **Rodar a colheita** das fontes OAI e conferir o estado (`status`) antes de medir.

## 3. Testes com pessoas (a IA não pode simular)

Registrar o resultado na tabela de `docs/ACESSIBILIDADE.md`.

- [ ] **M1 Só teclado**, em todas as telas: foco sempre visível, ordem lógica, nenhuma armadilha.
- [ ] **M2 Leitor de tela** (NVDA no Windows ou VoiceOver no macOS): busca, resultados, aviso de erro
  parcial, favoritar, diálogos e erros de formulário.
- [ ] **M3 Zoom de 200%** em cada tela.
- [ ] **M4 Zoom de 400%** em cada tela.
- [ ] **M5 Modo de alto contraste** do sistema.
- [ ] **Teste de usabilidade** com pessoas, quando a OS-036 entregar o roteiro.

## 4. Medições para o capítulo 4

- [ ] **Medição manual de tempo** (roteiro em `docs/evidencias/medicao/ROTEIRO_MANUAL.md`):
  copiar `planilha_modelo.csv` para `planilha_preenchida.csv`, preencher e rodar
  `scripts/summarize_manual.py`.
- [ ] **Medição da aplicação** com chaves reais e índice colhido:
  `uv run python scripts/measure_search.py --base-url http://127.0.0.1:8000 --runs 5`.
- [ ] **Preencher** `docs/evidencias/medicao/RELATORIO.md` com os números exatamente como saíram.
- [ ] **Se não fizer a medição manual:** remover do TCC qualquer afirmação de que a aplicação
  reduz o tempo ou o esforço de busca.

## 5. Capturas e importações

- [ ] **Capturas com dados reais** das fontes (roteiro em `docs/evidencias/telas/ROTEIRO_REAIS.md`),
  sem chave, sem e-mail nem nome verdadeiros.
- [ ] **Ajustar a coluna "Seção do TCC"** em `docs/evidencias/telas/INDICE.md` ao texto final.
- [ ] **Importar os arquivos `.bib` e `.ris` exportados** no Zotero ou no Mendeley e conferir se os
  campos chegam certos.

## 6. Antes de entregar

- [ ] **Testar o README em uma pasta limpa:** clonar o repositório numa pasta nova, seguir só o
  README e anotar o que faltou em `docs/os/OS-034-relatorio.md` (a OS-034 não pôde fazer isso).
- [ ] **Restaurar um backup e conferir a implantação** no ambiente onde for rodar (seção 9).
- [ ] **Decidir se quer a etiqueta `v1.0.0`** no Git (só é criada se você pedir).
- [ ] **Enviar os commits ao GitHub** (`git push origin master:main`): o remoto parou na OS-031;
  tudo depois (OS-032 em diante) só existe localmente até você pedir o envio.
- [ ] **Ler a lista de divergências** (`docs/CONFORMIDADE_TCC.md`, seção 4) e ajustar o texto do TCC.

## 7. Itens `[VERIFICAR]` ainda abertos

Dependem de chamada real às fontes ou de importação manual; nada disso foi confirmado.

- [ ] **OpenAlex:** sintaxe dos filtros de ano (`publication_year:A-B`), de tipo (`type:a|b`) e da
  ordenação (`sort=publication_year:desc`); campos `authorships[].author.display_name`, `.orcid` e
  `primary_location.landing_page_url`. (`docs/DECISOES.md`, OS-007; `docs/evidencias/os-005-mapeamento.md`)
- [ ] **CORE:** filtros embutidos em `q` (`yearPublished>=A AND yearPublished<=B`,
  `documentType:"thesis"`), campo de ano, idioma, `limit` máximo de 100 (`MAX_LIMIT` em
  `app/connectors/core_api.py`) e o mapa de tipos de documento. (`docs/DECISOES.md`, OS-008)
- [ ] **Importação no Zotero ou Mendeley:** teses saem como `@thesis`/`THES` e preprint e outros como
  `@misc`/`GEN`; conferir na importação (`docs/evidencias/os-019/LEIA-ME.md`).
- [ ] **Endereços OAI** das quatro fontes (já listado na seção 2).

Ao receber as chaves e rodar a primeira chamada real, se algo divergir, ajuste `build_filter`
(OpenAlex) e `build_query_string` (CORE) e registre em `docs/DECISOES.md`.

## Observação sobre o banco local

A instância do PostgreSQL do projeto roda na porta 5434 (dados em `C:\Users\Copperline\pgdata-tcc`).
Se a máquina reiniciar, ela precisa ser iniciada de novo antes dos testes de banco e dos fluxos de
ponta a ponta. No PowerShell:

```
$b = "C:\Program Files\PostgreSQL\18\bin"; $d = "C:\Users\Copperline\pgdata-tcc"
Remove-Item "$d\postmaster.pid" -ErrorAction SilentlyContinue
Start-Process "$b\pg_ctl.exe" -ArgumentList "-D","`"$d`"","-o","`"-p 5434`"","-l","`"$d\server.log`"","start" -WindowStyle Hidden
& "$b\pg_isready.exe" -h 127.0.0.1 -p 5434   # repita até aparecer "aceitando conexões"
```

Depois de uma queda, a recuperação do banco pode levar alguns minutos.

## 8. Decisões da avaliação de usabilidade (OS-036)

- [ ] **Confirmar a mudança do login:** a caixa "Manter conectado nesta aba" agora vem marcada por
  padrão (divergência da OS-021; motivo e como reverter em `docs/USABILIDADE.md`, seção 4, e em
  `docs/DECISOES.md`). Se discordar, peça para voltar ao padrão antigo.
- [ ] **Preencher o contato do responsável** na política (`{CONTATO_DO_RESPONSAVEL}` aparece como
  texto na página; severidade 3 na avaliação, problema P2). É o mesmo item da seção 1.
- [ ] **Decidir sobre a recuperação de senha:** hoje não existe (exigiria envio de e-mail). O
  cadastro avisa. Decida se o TCC cita isso como limitação.
- [ ] **Conferir as referências** de Nielsen e Molich (1990) e Nielsen (1994) na fonte original antes
  de citá-las, e o texto das dez heurísticas.
- [ ] **(Opcional) Teste com 3 a 5 colegas**, com o roteiro de 4 tarefas de `docs/USABILIDADE.md`,
  seção 6, sem medir tempo e sem calcular porcentagem.

## 9. Implantação, colheita agendada e backup (OS-037)

Os exemplos de `deploy/` **não foram executados** (não há servidor nem domínio). Detalhes e a lista de
verificação em `docs/IMPLANTACAO.md`, seção 10.

- [ ] **Decidir onde o sistema vai rodar.** Se for só na sua máquina, para a defesa, o TCC deve dizer
  isso e não descrever um ambiente de produção.
- [ ] **Se for publicar:** instalar no servidor, preencher `/etc/academic-search-hub/env` (com uma
  `SECRET_KEY` gerada lá), ativar o serviço, configurar o Nginx ou o Caddy com HTTPS e conferir os
  itens "PENDENTE" da lista de verificação.
- [ ] **Confirmar que o serviço sobe sozinho** depois de reiniciar a máquina.
- [ ] **Confirmar que a colheita agendada rodou** e que `status` mostra o resultado (depende das
  fontes OAI da seção 2).
- [ ] **Repetir o teste de restauração no servidor real**, com o banco real, e anotar a data e o
  resultado em `docs/IMPLANTACAO.md`, seção 9.
- [ ] **Copiar os backups para fora da máquina** (não está automatizado): uma cópia só no servidor não
  protege contra perda dele.
- [ ] **Conferir o texto da política de privacidade** (`app/content/privacy_pt.md`): ele deve avisar
  que contas excluídas ficam nas cópias de segurança por até 7 dias.
