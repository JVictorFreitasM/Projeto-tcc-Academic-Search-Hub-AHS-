# Relatório da medição: busca manual versus aplicação

> **Estado: nenhuma medição foi executada.** Este arquivo ainda não contém resultados. Os números
> só entram aqui depois que o desenvolvedor rodar a medição, e entram **exatamente como saíram** de
> `resultado-AAAAMMDD.csv` / `.md` e de `resumo_manual.md`. Nada neste relatório é estimado nem
> copiado de outros trabalhos.

## O que se pretende medir

- **Manual:** tempo para, à mão nas seis fontes (CORE, SciELO, OpenAlex, BDTD, UFPI, UESPI), chegar
  a uma lista de resultados relevantes e sem duplicatas, para cada uma das 5 consultas.
- **Aplicação:** tempo para chegar à mesma lista usando a aplicação.
- **Da aplicação em si:** tempo total da busca, duração por fonte, resultados por fonte,
  duplicatas fundidas e fontes que falharam, em N execuções por consulta.

Instrumentos: `scripts/measure_search.py` (aplicação), `ROTEIRO_MANUAL.md` e `planilha_modelo.csv`
(manual) e `scripts/summarize_manual.py` (resumo da planilha). Testados com dados falsos em
`tests/unit/test_measure_scripts.py`; esses testes provam a aritmética dos scripts, não medem nada.

## Método (a preencher quando a medição for feita)

| Item | Valor |
|---|---|
| Data da medição | PENDENTE (desenvolvedor) |
| Consultas (`consultas.txt`) | PENDENTE (desenvolvedor) |
| Pessoas que mediram | PENDENTE (desenvolvedor) |
| Execuções por consulta na aplicação (N) | PENDENTE (desenvolvedor) |
| Critério de resultado útil | PENDENTE (desenvolvedor) |
| Fontes ativas e colhidas na medição | PENDENTE (desenvolvedor) |

## Resultados

### Aplicação (`measure_search.py`)

PENDENTE (desenvolvedor): colar aqui o resumo gerado.

### Manual (`summarize_manual.py`)

PENDENTE (desenvolvedor): colar aqui o resumo gerado.

## Limitações (valem para qualquer resultado que venha a ser registrado)

- **Poucos participantes e poucas consultas** (5): os números descrevem esta medição, não o uso em
  geral. Não se generaliza para outras pessoas, temas ou épocas.
- **Rede e carga variáveis:** o tempo da aplicação depende da rede e do momento em que cada fonte
  responde. Uma execução lenta pode ser da fonte, não do sistema.
- **O índice local depende da colheita feita:** as fontes OAI (BDTD, UFPI, UESPI, SciELO) só
  respondem com o que foi colhido antes; uma colheita antiga ou parcial muda os resultados e a
  comparação.
- **A medição manual depende de quem a faz:** familiaridade com as fontes, cansaço e a ordem das
  consultas influenciam o tempo. O critério de "resultado útil" é humano.
- **Duração por fonte:** a API só a envia com `APP_ENV=development`. Medindo em produção, essa
  coluna fica vazia e vale só o tempo total; anote em qual modo a medição foi feita.
- **Cache e primeira execução:** a primeira busca de uma consulta pode ser mais lenta que as
  seguintes; o script grava todas as execuções, sem descartar nenhuma.
- **Duplicatas fundidas:** só são calculadas quando a página não corta resultados; caso contrário o
  campo fica "não determinável".
- O tempo da aplicação medido pelo script **não inclui** o tempo de uma pessoa ler e escolher
  resultados; só o tempo manual (cronômetro) inclui.

## O que o TCC pode afirmar

- Só o que estiver nas tabelas acima, com as limitações.
- Se a medição manual **não** for feita, o TCC deve **remover** qualquer afirmação de que a aplicação
  reduz o tempo ou o esforço de busca. Não escrever "reduz em X%" sem os dados.
