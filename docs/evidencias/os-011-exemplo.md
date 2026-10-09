# Exemplo antes/depois de uma fusão (OS-011)

> **Exemplo ilustrativo, com dados fictícios** (os mesmos usados nos testes). Para o TCC, substituir
> por uma fusão real de uma busca feita pelo desenvolvedor com as chaves e o índice colhido
> (passo manual).

**Antes** (três registros da mesma obra, vindos de fontes diferentes):

| Fonte | `id` | DOI | Ano | Resumo | PDF |
|---|---|---|---|---|---|
| OpenAlex | `doi:10.5/x` | `10.5/x` | 2021 | — | — |
| CORE | `doi:10.5/x` | `10.5/X` | — | "Resumo longo do trabalho." | `https://core.ac.uk/…pdf` |
| UESPI (índice local) | `src:uespi:oai:u:3` | — | 2021 | "Resumo curto." | — |

**Depois** (um único registro): `id = doi:10.5/x`, `year = 2021`, resumo mais longo (o do CORE),
PDF herdado do CORE e `sources` com as três entradas (`openalex`, `core`, `uespi`).

Regras aplicadas (`app/services/dedup.py`): chave 1 (DOI normalizado) junta OpenAlex e CORE; o
registro da UESPI, sem DOI, entra pela chave 2 (título normalizado ≥ 15 caracteres + ano +
sobrenome do primeiro autor) e a obra ganha o DOI. Títulos curtos, anos diferentes ou DOIs
diferentes **não** fundem.
