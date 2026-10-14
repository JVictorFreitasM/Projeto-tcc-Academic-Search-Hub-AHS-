# Fontes candidatas: o que dá para adicionar (gratuitas)

Verificação feita em **14/10/2026**. Este documento diz o que respondeu **naquele dia**; um
repositório que funciona hoje pode mudar amanhã, e o que falhou pode ser temporário.

## Como foi verificado

- Uma requisição leve por endereço (`Identify` do OAI-PMH, ou uma busca mínima de 1 resultado nas
  APIs REST), com `User-Agent` identificado, em sequência e com pausa entre elas.
- **Sem chave, sem cadastro e sem contornar nada** (anti-robô, `robots.txt`, limites). O que exigiu
  isso está marcado como "não funciona agora".
- Para os OAI que responderam, uma página de `ListRecords` em `oai_dc` (100 registros) para medir a
  qualidade dos metadados. **É uma amostra da primeira página, não o repositório inteiro.**
- "Gratuito" aqui quer dizer: respondeu sem pagamento nem chave. **Termos de uso e limites de cada
  fonte não foram lidos nem verificados**: leia antes de colher em escala.

## Resumo em uma frase

Funciona hoje, só com configuração (sem código novo): **UFPE, UFMG e UFRGS (Lume)** por OAI-PMH.
**UFPI e UESPI estão no ar, mas não devolvem registros** (problema do lado deles). Fontes REST
gratuitas e sem chave que responderam: **DOAJ, Europe PMC, OpenAIRE, Crossref, Zenodo, HAL e arXiv**,
mas cada uma exige um **conector novo** (código).

## 1. OAI-PMH

Adicionar uma fonte OAI é só editar `config/oai_sources.yml` e colher (`docs/EXECUCAO.md`, seção 4).

### 1.1 Responderam e devolveram registros

| Repositório | Endereço que respondeu | Nome no `Identify` | Registros (`completeListSize`) | Amostra de 100 registros |
|---|---|---|---|---|
| **UFPE** | `https://repositorio.ufpe.br/oai/request` | RI UFPE | 12.367 | Todos com título, autor, resumo, ano e idioma (96 `por`). Tipos: `masterThesis` 74, `doctoralThesis` 17, `bachelorThesis` 4 |
| **UFMG** | `https://repositorio.ufmg.br/server/oai/request` | Repositório Institucional da UFMG | 80.144 | 85 de 100 com resumo; todos com ano. Tipos: "Dissertação de mestrado" 39, "Tese de doutorado" 20, "Artigo de periódico" 19, "Monografia de especialização" 16 |
| **UFRGS (Lume)** | `https://lume.ufrgs.br/oai/request` | Lume 5.8 | 304.949 | Todos com título e ano, mas **só 1 de 100 com resumo** nesta página. Tipos: "Resumo publicado em evento" 70, "Trabalho completo publicado em evento" 29; o campo `dc:type` também traz "Nacional" (não é um tipo) |

Todos usam DSpace, têm `deletedRecord` e formatos `oai_dc` e outros. Os endereços de `baseURL` que
o `Identify` de alguns informa (por exemplo `http://...:8080`) diferem dos que respondem; use os da
tabela.

**Para configurar**, o `type_map` do `oai_sources.yml` precisa dos valores de `dc:type` que o
sistema ainda não reconhece sozinho. O sistema já entende `masterThesis`, `doctoralThesis`, `Tese`,
`Dissertação`, `Artigo de periódico`, `Capítulo de livro` e `bachelorThesis` (como `other`).
Sugestão (a conferir com uma amostra maior):

```yaml
  - slug: ufmg
    name: Repositório Institucional da UFMG
    base_url: https://repositorio.ufmg.br/server/oai/request
    metadata_prefix: oai_dc
    set_spec: null
    enabled: false          # troque para true só depois de testar com --dry-run
    default_type: other
    type_map:
      "Dissertação de mestrado": thesis
      "Tese de doutorado": thesis
      "Artigo de evento": other
      "Monografia de especialização": other
```

### 1.2 Estão no ar, mas **não devolvem registros** (precisa do administrador)

| Repositório | O que se viu |
|---|---|
| **UFPI** (`https://repositorio.ufpi.br/oai/request`) | `Identify`, `ListSets` (59 conjuntos) e `ListMetadataFormats` respondem. `ListRecords` e `ListIdentifiers` devolvem `noRecordsMatch` em `oai_dc`, `xoai` e em quatro conjuntos testados |
| **UESPI** (`https://repositorio.uespi.br/oai/request`, "Repositorio de Artigos Cientificos da UESPI") | Mesmo comportamento: `Identify` e 22 conjuntos respondem, mas todo `ListRecords` dá `noRecordsMatch` |

Isso é do lado do servidor deles: o índice OAI está vazio ou desatualizado (em DSpace costuma ser
preciso reindexar). **Não é algo que o sistema consiga contornar.** Como a UESPI é a sua
instituição, vale pedir ao administrador do repositório para reindexar o OAI e conferir de novo com
`uv run python -m app.harvest.cli run uespi --limit 50 --dry-run`.

As duas respondem agora, ao contrário do que o `config/oai_sources.yml` e a OS-009 encontraram em
08/10/2026 (UFPI com 502, UESPI sem endereço). Os endereços acima podem substituir os
`TODO-VERIFICAR` quando os registros aparecerem.

### 1.3 Não funcionam agora (ou não deu para validar)

| Repositório | Resultado em 14/10/2026 |
|---|---|
| BDTD (IBICT) e Oasisbr | Respondem com a página HTML "Verificando conexão" (desafio anti-robô), sem XML. Não foi contornado |
| SciELO | Nenhum endereço OAI testado respondeu (`oai.scielo.br` sem conexão; `articlemeta.scielo.org/oai` e `www.scielo.br/oai/scielo-oai.php` com 404). Há API REST (seção 2) |
| UFSC (`/oai/request` e `/server/oai/request`) | Responderam HTML, não OAI |
| UNICAMP, UFC | 404 nos dois caminhos testados (o endereço correto é outro) |
| UnB | 503 (servidor indisponível, duas tentativas) |
| UFSCar, UNESP | `Identify` válido em `/server/oai/request` (RI UFSCar; Repositório Institucional Unesp), mas **sem amostra de registros**: falta testar |
| LA Referencia | 404 no endereço testado |
| RCAAP (Portugal) | `Identify` válido, mas `ListRecords` sem conjunto deu erro 500 |

### 1.4 Repositórios internacionais com OAI-PMH que responderam ao `Identify`

arXiv (`https://export.arxiv.org/oai2`), Zenodo (`https://zenodo.org/oai2d`), DOAJ
(`https://www.doaj.org/oai`), PubMed Central (`https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi`) e HAL
(`https://api.archives-ouvertes.fr/oai/hal`). Não foram amostrados. São enormes e de conteúdo
majoritariamente não lusófono (exceto parte de Zenodo, DOAJ e HAL): colher tudo isso pesa no banco e
foge do foco do TCC.

## 2. APIs REST gratuitas

Todas responderam **sem chave** a uma busca de 1 resultado por "letramento". **Nenhuma tem conector no
sistema**: cada uma exigiria uma OS nova (conector, mapeamento, fixtures, testes). Quem usa o que cada
API cobre é conhecimento geral, não medido aqui.

| API | Endereço testado | Resultado | Observação |
|---|---|---|---|
| **DOAJ** | `https://doaj.org/api/search/articles/<consulta>` | 200, JSON | Artigos de revistas em acesso aberto; boa para o foco do TCC |
| **Europe PMC** | `https://www.ebi.ac.uk/europepmc/webservices/rest/search` | 200, JSON | Literatura de ciências da vida e preprints |
| **OpenAIRE** | `https://api.openaire.eu/search/publications` | 200, JSON | Agregador europeu de publicações |
| **Crossref** | `https://api.crossref.org/works` | 200, JSON | Metadados de DOIs; costuma não trazer resumo. Recomenda identificar-se com e-mail ("polite pool") |
| **Zenodo** | `https://zenodo.org/api/records` | 200, JSON | Produção de pesquisa de várias áreas, inclusive dados e software |
| **HAL** | `https://api.archives-ouvertes.fr/search/` | 200, JSON | Arquivo aberto francês |
| **arXiv** | `https://export.arxiv.org/api/query` | 200, Atom (XML) | Preprints de exatas e computação; a documentação pede pausa entre requisições |
| **SciELO ArticleMeta** | `https://articlemeta.scielo.org/api/v1/...` | 200, JSON | Metadados por identificador, **sem busca por texto**: serve para colher, não para pesquisar ao vivo |
| Semantic Scholar | `https://api.semanticscholar.org/graph/v1/paper/search` | **429** | Limitou a requisição sem chave; sem chave não é confiável |

OpenAlex e CORE, que o sistema já usa, ficam fora desta lista (já são fontes, dependem de chave).

## 3. Web scraping

Só como último recurso e só onde o `robots.txt` permitir. O raspador do projeto (OS-013) **recusa**
caminhos proibidos pelo `robots.txt` e só completa resumos de registros que já existem.

- **UFPI e UESPI:** o `robots.txt` de ambos tem `User-agent: *` com `Disallow: /discover` e
  `Disallow: /search-filter`. A busca do site **não pode ser raspada**. A API REST do DSpace também
  não existe nesses servidores (`/rest/...` e `/server/api` deram 404; na UESPI, `/rest` não
  conectou). Portanto raspar não é um caminho para essas duas: o caminho é o administrador
  consertar o OAI.
- Nenhuma outra fonte aqui precisa de raspagem: todas têm OAI-PMH ou REST.

## 4. O que eu faria (por esforço e retorno)

1. **UESPI e UFPI:** pedir aos administradores para reindexar o OAI. É o que realiza o objetivo do
   TCC (as duas instituições estão no escopo). Esforço: um e-mail.
2. **Só configuração, sem código:** UFPE e UFMG (colhem, trazem resumo e ano, em português). A UFRGS
   também, mas a amostra quase não tem resumo (1 em 100): confirme com uma amostra maior antes.
3. **Com código novo (uma OS por API):** DOAJ é a mais alinhada ao tema (revistas em acesso aberto).
4. Deixar para depois: Crossref, Europe PMC, OpenAIRE, Zenodo, HAL e arXiv, por foco e volume.

## 5. Atenção ao escopo do TCC

O TCC fala em **seis fontes** (CORE, SciELO, OpenAlex, BDTD, UFPI e UESPI). Adicionar UFPE, UFMG,
DOAJ etc. amplia o escopo descrito no texto e entra na lista de divergências da OS-035. A decisão é
sua: ampliar o sistema ou manter as seis e apenas relatar, no TCC, o estado real de cada uma (por
exemplo, "BDTD com desafio anti-robô; UFPI e UESPI com OAI sem registros em 14/10/2026").
