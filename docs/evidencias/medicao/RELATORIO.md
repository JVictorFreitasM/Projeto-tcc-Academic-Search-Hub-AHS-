# Relatório da medição e do cenário controlado de busca

## Escopo e método

As medições foram executadas em 15/10/2026 com respostas reais da aplicação. Foram usadas cinco
consultas e quatro fontes operacionais: CORE, OpenAlex, BDTD e o índice local da UFPE. A UFPE foi
colhida integralmente antes do ensaio. SciELO, UESPI, UFPI, UFMG, UFSCar, Unesp e UFRGS estavam
intencionalmente desabilitadas e não contam como falhas operacionais.

O trabalho contém dois recortes complementares:

1. três execuções por consulta para medir tempo de resposta, resultados exibidos, duplicatas
   fundidas e estabilidade das fontes;
2. uma execução por consulta para examinar a primeira página quanto a aderência lexical e presença
   de autoria, ano, resumo, DOI, PDF e idioma.

O perfil do estudante é fictício e não houve participante real. A comparação com a busca
convencional é apenas procedimental: conta quantas submissões da mesma consulta seriam necessárias,
sem estimar tempo humano, satisfação ou facilidade de uso.

| Item | Valor |
|---|---|
| Data da medição | 15/10/2026 |
| Consultas | letramento digital; acessibilidade web; segurança em aplicações web; repositórios institucionais; educação a distância |
| Participantes | nenhum; cenário controlado sem participante real |
| Execuções temporizadas | 3 por consulta, 15 no total |
| Página analisada | primeira página, até 20 itens |
| Fontes operacionais | CORE, OpenAlex, BDTD e UFPE no índice local |

## Resultados da aplicação

| Consulta | Tempo médio | Faixa | Exibidos (média) | Duplicatas fundidas |
|---|---:|---:|---:|---:|
| letramento digital | 1.404 ms | 1.156–1.831 ms | 17,0 | 9 |
| acessibilidade web | 1.508 ms | 1.144–2.177 ms | 17,0 | 9 |
| segurança em aplicações web | 2.379 ms | 1.996–3.099 ms | 17,7 | 2 |
| repositórios institucionais | 899 ms | 821–1.022 ms | 12,0 | 3 |
| educação a distância | 1.739 ms | 1.246–1.990 ms | 15,0 | 0 |

### Estabilidade por fonte

| Fonte | Respostas com dados | Ocorrências sem dados | Duração média |
|---|---:|---:|---:|
| BDTD | 15 | 0 | 333 ms |
| OpenAlex | 15 | 0 | 928 ms |
| UFPE (índice local) | 15 | 0 | 22 ms |
| CORE | 8 | 7 (`rate_limited`) | 1.141 ms* |

\* Média das respostas que informaram duração.

### Completude da primeira página

| Consulta | Autoria | Ano | Resumo | DOI | PDF | Idioma |
|---|---:|---:|---:|---:|---:|---:|
| letramento digital | 100,0% | 100,0% | 100,0% | 26,7% | 33,3% | 93,3% |
| acessibilidade web | 100,0% | 100,0% | 100,0% | 23,5% | 29,4% | 88,2% |
| segurança em aplicações web | 100,0% | 100,0% | 89,5% | 21,1% | 21,1% | 89,5% |
| repositórios institucionais | 94,1% | 100,0% | 100,0% | 23,5% | 41,2% | 88,2% |
| educação a distância | 100,0% | 100,0% | 95,0% | 25,0% | 40,0% | 100,0% |

A aderência lexical foi de 100% nas cinco consultas segundo o critério objetivo de presença de ao
menos uma palavra relevante da consulta no título ou resumo. Isso não equivale a julgamento humano
de relevância.

## Comparação procedimental

No fluxo convencional simulado, cada uma das cinco consultas teria de ser repetida nas quatro fontes
operacionais, totalizando 20 submissões, além da cópia e consolidação. Na aplicação foram feitas 5
submissões, e a consolidação ocorreu automaticamente. Isso representa 75% menos submissões da mesma
consulta, mas não demonstra redução de tempo humano.

## Achados positivos e negativos

Positivos:

- BDTD, OpenAlex e UFPE responderam em todas as 15 execuções;
- a busca continuou funcionando quando o CORE limitou requisições;
- autoria, ano e resumo tiveram alta completude;
- houve fusão de duplicatas em quatro dos cinco temas;
- uma submissão substituiu quatro submissões separadas no cenário avaliado.

Negativos:

- o CORE limitou 7 das 15 requisições;
- DOI e ligação direta para PDF apareceram em menos da metade dos itens;
- a primeira página e cinco temas não representam todo o universo de pesquisa;
- não foram medidos satisfação, carga cognitiva, tempo humano ou relevância julgada por pessoas;
- fontes desabilitadas reduzem a cobertura do escopo originalmente previsto.

## Colheita da UFPE

A colheita integral processou 12.381 registros: 12.366 ativos e 15 removidos. Dos ativos, 12.365
continham resumo, todos continham ano e 7 continham DOI. O resultado comprova o fluxo OAI-PMH até o
PostgreSQL e evidencia que a completude depende do campo e do repositório de origem.

## Arquivos brutos

- `resultado-20261015.csv`: 15 execuções temporizadas e estados por fonte;
- `resultado-20261015.md`: agregação da medição temporal;
- `analise-resultados-20261015.json`: dados de completude e aderência;
- `analise-resultados-20261015.md`: tabelas da análise multidimensional.

## Limitações

- Rede, carga e limites externos variam entre execuções.
- O total estimado é a soma declarada pelas fontes e pode conter duplicatas fora da página exibida.
- O cenário não substitui um estudo de usabilidade com participantes.
- A aderência lexical não avalia a qualidade científica nem a relevância semântica do trabalho.
- Os resultados descrevem a configuração e o momento da medição.
