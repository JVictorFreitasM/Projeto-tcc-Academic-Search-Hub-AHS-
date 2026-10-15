# Validação de repositórios universitários por OAI-PMH — 15/10/2026

Foram feitas requisições `Identify` e `ListRecords` com `metadataPrefix=oai_dc`. Em seguida, o
coletor do projeto executou uma simulação de uma página e 50 registros por fonte, sem gravar no
banco (`--limit 50 --dry-run --max-pages 1`). Os totais abaixo são os informados pelos servidores no
momento da consulta e podem mudar.

| Instituição | Natureza | Endpoint validado | Total informado | Qualidade da primeira amostra de 100 | Dry-run |
|---|---|---|---:|---|---|
| UFPE | federal | `https://repositorio.ufpe.br/oai/request` | 12.381 | 100 títulos, 100 autorias, 100 resumos e 100 datas | Já integrada e colhida |
| UFMG | federal | `https://repositorio.ufmg.br/server/oai/request` | 80.144 | 100 títulos, 100 autorias, 85 resumos e 100 datas | 50 lidos; 50 seriam gravados; 0 ignorados |
| UFSCar | federal | `https://repositorio.ufscar.br/server/oai/request` | 23.518 | 100 títulos, 100 autorias, 100 resumos e 100 datas | 50 lidos; 50 seriam gravados; 0 ignorados |
| Unesp | estadual | `https://repositorio.unesp.br/server/oai/request` | 245.448 | 100 títulos, 100 autorias, 96 resumos e 100 datas | 50 lidos; 50 seriam gravados; 0 ignorados |
| UFRGS | federal | `https://lume.ufrgs.br/oai/request` | 305.077 | 100 títulos, 100 autorias, 1 resumo e 100 datas | 50 lidos; 50 seriam gravados; 0 ignorados |

Os quatro novos endereços foram incluídos em `config/oai_sources.yml` com `enabled: false`. Essa
decisão permite reproduzir a validação sem iniciar silenciosamente colheitas grandes nem alterar as
fontes visíveis na aplicação. A UFRGS merece avaliação por conjunto antes de ser habilitada, porque
a primeira página teve baixa cobertura de resumos.

Também foram tentados caminhos prováveis de OAI-PMH para UNICAMP, USP, UFC, UFRN e UFBA. Esses
caminhos específicos não entregaram uma resposta OAI válida; isso não prova que as instituições não
possuam outro endpoint.

