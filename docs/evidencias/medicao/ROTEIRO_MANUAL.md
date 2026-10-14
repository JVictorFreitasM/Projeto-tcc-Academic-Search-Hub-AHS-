# Roteiro da medição manual (passo do desenvolvedor ou de voluntários)

Objetivo: comparar, com tempos medidos, o esforço de achar trabalhos sobre um tema **buscando à mão
nas seis fontes** com o esforço de fazer o mesmo **na aplicação**. A IA não pode fazer esta medição:
ela exige pessoas, cronômetro e as fontes reais.

## Preparação

1. Defina as 5 consultas em `consultas.txt` (temas dos cursos da UESPI). As mesmas 5 valem para os
   dois métodos.
2. Garanta que a aplicação esteja pronta: chaves OpenAlex e CORE configuradas e as fontes OAI
   colhidas (OS-007 a OS-010). Sem isso a comparação não é justa: anote o que estava faltando.
3. Copie `planilha_modelo.csv` para `planilha_preenchida.csv` e preencha uma linha por medição.
4. Reúna quem vai medir (você e, se possível, outras pessoas). Cada pessoa mede **todas** as
   consultas nos dois métodos. Alterne quem começa pelo método manual e quem começa pela aplicação,
   para o aprendizado de uma consulta não favorecer sempre o mesmo método.

## Para cada consulta

### Método manual

1. Zere o cronômetro. Inicie ao abrir o primeiro site.
2. Nas **seis fontes** (CORE, SciELO, OpenAlex, BDTD, UFPI, UESPI): abra o site, digite a consulta e
   veja os resultados.
3. Copie para um documento os resultados **relevantes** (critério fixo, igual para todas as pessoas:
   escreva-o abaixo antes de começar) e **remova as duplicatas à mão**.
4. Pare o cronômetro ao ter a lista final pronta. Anote o tempo e quantos resultados úteis ficaram.

### Método aplicação

1. Zere o cronômetro. Inicie ao abrir a aplicação.
2. Digite a consulta, busque, e copie a lista (ou exporte) dos resultados **relevantes**, pelo mesmo
   critério de relevância. A aplicação já remove duplicatas; confira o que sobrou.
3. Pare o cronômetro ao ter a lista final pronta. Anote o tempo e quantos resultados úteis ficaram.

### Critério de relevância (preencher antes de medir)

PENDENTE (desenvolvedor): escreva aqui, em uma ou duas frases, o que conta como "resultado útil"
(por exemplo: título e resumo tratam do tema da consulta). Use o mesmo critério para todos.

## Planilha

Colunas de `planilha_modelo.csv`:

| Coluna | O que escrever |
|---|---|
| `consulta` | O texto exato da consulta, igual ao de `consultas.txt` |
| `metodo` | `manual` ou `aplicacao` |
| `pessoa` | Um código (P1, P2...). Não escreva nomes |
| `tempo` | Segundos (`95`) ou `mm:ss` (`1:35`), do cronômetro |
| `resultados_uteis` | Quantos resultados relevantes e sem duplicata ficaram na lista final |
| `observacoes` | O que atrapalhou: fonte fora do ar, desafio anti-robô, rede lenta, etc. |

Abra no Excel ou em outro editor e salve como CSV (aceita vírgula ou ponto e vírgula).

## Depois de medir

```
uv run python scripts/summarize_manual.py docs/evidencias/medicao/planilha_preenchida.csv --out docs/evidencias/medicao/resumo_manual.md
uv run python scripts/measure_search.py --base-url http://127.0.0.1:8000 --runs 5
```

O primeiro comando calcula média, mínimo e máximo por método e consulta. O segundo mede o tempo da
aplicação em si (rede e fontes), em `resultado-AAAAMMDD.csv` e `.md`. Depois preencha
`RELATORIO.md` copiando os números **como saíram**, sem arredondar para melhor nem tirar conclusões
que os dados não sustentem.

## Cuidados

- Meça em horário e rede comuns; anote se houve algo fora do normal.
- Não treine uma consulta antes de medi-la (a primeira busca já ensina onde estão os resultados).
- Sem medição manual, o TCC **não pode** afirmar que a aplicação reduz o tempo de busca: remova a
  afirmação.
