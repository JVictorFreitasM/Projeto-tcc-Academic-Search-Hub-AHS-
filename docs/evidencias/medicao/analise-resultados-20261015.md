# Análise multidimensional do cenário controlado (15/10/2026)

Os dados vieram de respostas reais da aplicação, com uma execução por consulta e 20 itens 
na primeira página. O cenário representa um perfil fictício de estudante e não corresponde 
a um participante. A aderência lexical indica apenas a presença de ao menos uma palavra 
relevante da consulta no título ou resumo; não é uma avaliação humana de relevância.

## Resultado por consulta

| Consulta | Tempo | Total estimado | Exibidos | Fontes OK | Aderência lexical | Mult fonte |
|---|---:|---:|---:|---|---:|---:|
| letramento digital | 12032.1 ms | 50943 | 15 | bdtd, openalex, ufpe | 100.0% | 0 |
| acessibilidade web | 5983.6 ms | 49782 | 17 | bdtd, core, openalex, ufpe | 100.0% | 3 |
| segurança em aplicações web | 13606.4 ms | 36465 | 19 | bdtd, core, openalex, ufpe | 100.0% | 1 |
| repositórios institucionais | 5047.6 ms | 32134 | 17 | bdtd, core, openalex, ufpe | 100.0% | 1 |
| educação a distância | 3794.4 ms | 286440 | 20 | bdtd, core, openalex, ufpe | 100.0% | 0 |

## Completude da primeira página

| Consulta | Autoria | Ano | Resumo | DOI | PDF | Idioma |
|---|---:|---:|---:|---:|---:|---:|
| letramento digital | 100.0% | 100.0% | 100.0% | 26.7% | 33.3% | 93.3% |
| acessibilidade web | 100.0% | 100.0% | 100.0% | 23.5% | 29.4% | 88.2% |
| segurança em aplicações web | 100.0% | 100.0% | 89.5% | 21.1% | 21.1% | 89.5% |
| repositórios institucionais | 94.1% | 100.0% | 100.0% | 23.5% | 41.2% | 88.2% |
| educação a distância | 100.0% | 100.0% | 95.0% | 25.0% | 40.0% | 100.0% |

## Disponibilidade das fontes

| Fonte | Respostas OK | Respostas não OK |
|---|---:|---:|
| bdtd | 5 | 0 |
| core | 4 | 1 |
| openalex | 5 | 0 |
| scielo | 0 | 5 |
| uespi | 0 | 5 |
| ufmg | 0 | 5 |
| ufpe | 5 | 0 |
| ufpi | 0 | 5 |
| ufrgs | 0 | 5 |
| ufscar | 0 | 5 |
| unesp | 0 | 5 |

## Comparação procedural do cenário

Na busca convencional simulada, o mesmo texto teria de ser submetido separadamente às quatro fontes operacionais avaliadas (CORE, OpenAlex, BDTD e índice UFPE), seguido de cópia e consolidação dos resultados. Na aplicação, cada tema exigiu uma submissão e a consolidação ocorreu no serviço de busca. Para cinco temas, isso corresponde a 20 submissões repetidas no fluxo convencional contra 5 na aplicação. Essa contagem mede etapas do procedimento, não tempo humano nem facilidade percebida.

## Limitações

- Uma execução de completude por consulta; os resultados das fontes mudam com o tempo.
- O total é estimado pela soma informada pelas fontes e pode conter duplicatas.
- A primeira página não representa todo o conjunto recuperado.
- O cenário não mede satisfação, compreensão, carga cognitiva nem desempenho de pessoas.
