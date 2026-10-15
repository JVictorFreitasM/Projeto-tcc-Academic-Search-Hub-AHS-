# Validação real do OpenAlex (OS-007)

Feita em **15/10/2026**, com a chave gratuita do desenvolvedor (guardada só no `.env`, que o Git
ignora; **nunca** aparece em fixture, teste, documento ou saída). Resolve o passo manual 0 da OS-007 e os
itens `[VERIFICAR]` do OpenAlex.

## O que foi feito

1. **Resposta real gravada** (passo manual 0): `GET https://api.openalex.org/works?search=educação&per-page=5`
   com a chave, salva em `tests/fixtures/openalex/search_ok.json` (HTTP 200, 5 trabalhos, sem a chave
   no corpo). Substitui a fixture sintética.
2. **A sintética virou `tests/fixtures/openalex/edge_cases.json`**, marcada `_synthetic` e
   `_permanent`: guarda os casos de borda (autor sem nome, registro mínimo, tese) que uma resposta real
   não garante cobrir e que os testes detalhados de mapeamento usam. Não é pendência.
3. **Todo trabalho da resposta real vira um registro válido** (5 de 5), com título, ano, tipo, idioma,
   DOI, autoria com ORCID, `url`, `pdf_url`, resumo reconstruído e palavras-chave
   (`tests/unit/test_openalex_connector.py`, `test_real_openalex_response_maps_to_valid_records`).
4. **Chamadas ao vivo pelo conector** (`OpenAlexConnector`), uma busca por "letramento digital" com cada
   variação. Os totais são o que a API devolveu **naquele momento** e mudam com o tempo.

| Caso | Total (API) | Resultado conferido |
|---|---|---|
| sem filtros | 46.894 | 5 artigos, anos 2020 a 2026 |
| `year_from=2018`, `year_to=2022` | 14.981 | todos os anos entre 2018 e 2022 |
| só `year_from=2020` (limite aberto) | 37.852 | todos de 2020 em diante |
| só `year_to=2005` (limite aberto) | 145 | todos de 2005 para trás (2004 e 2005) |
| tipo `article` | 26.114 | só artigos |
| tipo `thesis` | 7.187 | só teses (2016 a 2023) |
| tipo `preprint` | 153 | só preprints |
| tipo `book` | 10.696 | só livros |
| ordenação `year_desc` | 46.894 | os 5 primeiros são de 2026 |
| página 2 | 46.894 | 5 resultados, com títulos diferentes dos primeiros da página 1 |
| ano 2015 a 2024 + tipos artigo e tese + `year_desc` ("educação inclusiva") | 68.102 | 5 artigos de 2024 |

Em todos, `status = ok` e nenhum erro.

## Pela aplicação inteira (servidor, API e fonte real)

`docs/evidencias/os-007-validacao-real.txt`: `GET /api/v1/sources` mostra o OpenAlex habilitado e as outras
cinco fontes indisponíveis com o motivo (CORE sem chave; fontes OAI ainda não colhidas); `GET
/api/v1/search` devolve resultados reais do OpenAlex com `sources_status` por fonte, total marcado como
estimativa e, em modo desenvolvimento, `duration_ms` (cerca de 1 a 2,5 s por busca nesta máquina e rede,
**uma medição, não desempenho**).

## O que isso resolve e o que não resolve

- **Resolve** os `[VERIFICAR]` do OpenAlex: sintaxe do filtro de ano (faixa e limites abertos), do filtro
  de tipo, da ordenação por ano e da paginação, e os campos de autoria, ORCID e `landing_page_url`.
- **Não resolve:** o CORE (sem chave; fixture ainda sintética), as fontes OAI (nenhuma colhida), a
  medição de tempo (nenhuma feita) e o filtro de tipo `other`, que é feito localmente e não foi
  exercitado ao vivo.
- Os totais acima são **estimativas da API num dia**: não os cite como resultado do sistema sem a data.
