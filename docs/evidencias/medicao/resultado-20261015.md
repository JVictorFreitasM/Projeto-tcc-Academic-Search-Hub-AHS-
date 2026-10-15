# Resultado da medição da aplicação (15/10/2026)

Gerado por `scripts/measure_search.py`. Tempo total = cronômetro do cliente, do pedido à resposta completa; duração por fonte = `sources_status.duration_ms` da resposta.

## Tempo total por consulta

| Consulta | Execuções | Tempo total | Resultados exibidos (média) | Duplicatas fundidas |
|---|---|---|---|---|
| letramento digital | 3 | média 1404 ms · mín 1156 · máx 1831 | 17.0 | 9 (em 3 de 3 execuções) |
| acessibilidade web | 3 | média 1508 ms · mín 1144 · máx 2177 | 17.0 | 9 (em 3 de 3 execuções) |
| segurança em aplicações web | 3 | média 2379 ms · mín 1996 · máx 3099 | 17.7 | 2 (em 3 de 3 execuções) |
| repositórios institucionais | 3 | média 899 ms · mín 821 · máx 1022 | 12.0 | 3 (em 3 de 3 execuções) |
| educação a distância | 3 | média 1739 ms · mín 1246 · máx 1990 | 15.0 | 0 (em 3 de 3 execuções) |

## Por fonte

| Fonte | Respostas | Falhas | Duração |
|---|---|---|---|
| bdtd | 15 | 0 | média 333 ms · mín 280 · máx 467 |
| core | 15 | 7 | média 1141 ms · mín 380 · máx 2666 |
| openalex | 15 | 0 | média 928 ms · mín 751 · máx 1252 |
| scielo | 15 | 15 | sem dados |
| uespi | 15 | 15 | sem dados |
| ufmg | 15 | 15 | sem dados |
| ufpe | 15 | 0 | média 22 ms · mín 18 · máx 32 |
| ufpi | 15 | 15 | sem dados |
| ufrgs | 15 | 15 | sem dados |
| ufscar | 15 | 15 | sem dados |
| unesp | 15 | 15 | sem dados |

## Fontes que não responderam como `ok`

- core: rate_limited
- scielo: disabled
- uespi: disabled
- ufmg: disabled
- ufpi: disabled
- ufrgs: disabled
- ufscar: disabled
- unesp: disabled

Duplicatas fundidas = registros devolvidos pelas fontes menos resultados exibidos; só é calculada quando a página não cortou resultados (senão fica "não determinável").
