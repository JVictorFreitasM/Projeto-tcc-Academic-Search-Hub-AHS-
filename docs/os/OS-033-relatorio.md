# OS-033 — Medição: busca manual versus aplicação

## O que foi feito (instrumentos, não medições)

- `scripts/measure_search.py`: para cada consulta de `consultas.txt`, busca N vezes em
  `/api/v1/search` e grava `resultado-AAAAMMDD.csv` (uma linha por consulta, execução e fonte) e
  `.md` (resumo). Registra tempo total (cronômetro do cliente), `sources_status.duration_ms`,
  resultados por fonte, duplicatas fundidas e fontes que falharam. Falha de conexão ou erro HTTP
  vira linha na planilha, sem derrubar a medição.
- `scripts/summarize_manual.py`: lê a planilha da medição manual (vírgula ou ponto e vírgula; tempo
  em segundos ou `mm:ss`) e calcula média, mínimo e máximo por método e por consulta. Não compara
  métodos nem calcula percentuais.
- `docs/evidencias/medicao/`: `consultas.txt` (vazio de propósito), `ROTEIRO_MANUAL.md`,
  `planilha_modelo.csv` (só o cabeçalho) e `RELATORIO.md`.
- `tests/unit/test_measure_scripts.py`: 32 testes com dados falsos e sem rede (`httpx.MockTransport`).

## O que NÃO foi feito

- **Nenhuma medição foi executada.** Não há chaves reais, nem fontes OAI colhidas, nem medição
  manual. Por isso o `RELATORIO.md` não contém nenhum número: tudo o que depende de medição está
  `PENDENTE (desenvolvedor)`.
- As 5 consultas **não foram escolhidas**: são do desenvolvedor (definem o que o TCC afirma ter
  medido). Rodar `measure_search.py` com o arquivo vazio termina com erro claro (código 2); um teste
  garante que o arquivo entregue está vazio.
- O critério de "resultado útil" também fica para o desenvolvedor registrar antes de medir.

## Decisão sobre "duplicatas fundidas"

A resposta da busca não informa quantas duplicatas foram fundidas. O script deriva: registros
devolvidos pelas fontes menos resultados exibidos. Porém a página corta o resultado ao `page_size`,
o que se misturaria com a fusão. Por isso o valor só é calculado quando a soma das fontes não passa
do `page_size`; caso contrário fica vazio ("não determinável"), em vez de um número enganoso.

## Verificação

- Testes unitários dos dois scripts passam (aritmética conferida com valores fictícios: médias,
  mínimos e máximos, formatos de tempo, planilha do Excel, erros com número da linha).
- Teste garante que o resumo manual nunca escreve percentual nem "reduz".

## Para o TCC

Se o desenvolvedor não fizer a medição manual, o TCC deve **remover** a afirmação de que a aplicação
reduz o tempo de busca.
