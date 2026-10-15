# Avisos sobre o TCC (versão 2, conforme REGRAS_DO_TCC.md)

Arquivo editado: `TCC_COMPLETO_Joao_Victor.docx` (o arquivo de trabalho). Arquivo editado: `tcc/TCC_COMPLETO_Joao_Victor.docx`; a versão anterior está em `tcc/TCC_COMPLETO_Joao_Victor_ANTES_DA_EDICAO.docx`. Pela regra 3, **nenhum aviso foi escrito dentro do documento**: tudo o que precisa de decisão sua está aqui.

A cópia de segurança anterior à revisão bibliográfica está em
`TCC_COMPLETO_Joao_Victor_ANTES_REFERENCIAS_20261015.docx`.

## 1. O que foi feito no documento

| Parte | O que mudou |
|---|---|
| 1 Introdução | Só uma frase: "busca unificada **por tema ou pelo nome do autor**". Continua sem citação e no presente |
| 3 Delineamento | O parágrafo que dizia que SciELO, BDTD, UFPI e UESPI "expõem" OAI-PMH foi reescrito: previu-se o OAI-PMH, a disponibilidade foi testada, a BDTD passou para a API REST e a UFPE entrou só para validar a colheita. Passado, sem citação |
| 4 (abertura) a 4.6 | Os 7 roteiros foram trocados pelo texto, retomando os autores do mapa da seção 6 das regras |
| 5 Conclusões | Atualizada com a validação adicional de UFMG, UFSCar, Unesp e UFRGS |
| Figuras | 6 telas reais (Figuras 1 a 6), com legenda acima e "Fonte: Elaborado pelo Autor (2026)." abaixo |
| Quadros | Quadro 1 (situação das fontes) e Quadro 2 (autoavaliação da API, rota por rota) |
| Referencial e referências | Lacunas bibliográficas corrigidas; a citação sem fonte primária suficiente foi removida |
| Apêndice de avisos | Removido integralmente do arquivo oficial |
| Página | Convertida de Carta para A4, com margens 3 cm × 2 cm |

## 2. Decisões que são suas

1. **Escopo das fontes.** O objetivo geral (Introdução) continua prometendo as seis fontes. O texto da 4.2 e da Conclusão diz que o objetivo foi **cumprido em parte**: CORE, OpenAlex e BDTD funcionam, e SciELO, UFPI e UESPI não. Se preferir reescrever o objetivo geral, me diga (é mudança na Introdução, que as regras dão como pronta).
2. **UFPE.** As regras listam "repositórios de outras universidades" como fora do escopo. A UFPE entrou **só para validar a colheita** OAI-PMH, e é assim que o texto a apresenta. Se o orientador não aceitar, a alternativa é tirar a UFPE e declarar que a colheita foi provada só com dados de teste.
3. **Trabalhos futuros.** A lista passou a indicar UFMG, UFSCar, Unesp e UFRGS como candidatas já
   validadas, ainda desabilitadas.
4. **OWASP 2017 ou 2021** (regra 11.4): o texto usa 2017, como o resto do trabalho.
5. **Tamanho da página:** corrigido para **A4** (21,0 × 29,7 cm).

## 3. Citações e fontes para você confirmar

- **Nielsen.** A 4.4 cita as heurísticas como "Nielsen (1994 apud PRATES; BARBOSA, 2003)", ou seja, citação de citação: não exige Nielsen nas referências, mas exige que o capítulo de Prates e Barbosa apresente a avaliação heurística e as dez heurísticas. **Confira no PDF**; se não estiver lá, me avise, que eu retiro.
- **Cybis, Betiol e Faust (2010)** foi retomado como obra que "discute" a avaliação heurística. Confira no livro.
- **Avaliação de usabilidade.** O texto registra que foi uma inspeção sem participação de usuários.
  Um teste com participantes continua pendente e não deve ser confundido com essa inspeção.
- **Almeida e Dias (2023)** foi retomado para dizer que a BDTD coleta por OAI-PMH, contrastando com o 404 encontrado. É o que o referencial já atribui a eles.
- **Krocz et al. (2020):** retomado só para dizer que a comparação de desempenho deles **não** foi reproduzida (o PostgreSQL foi escolhido pela busca textual em português).
- **Jung et al. (2015)** e **Nagaraju et al. (2019):** referências localizadas e completadas com
  congresso, páginas e DOI.

## 4. Números usados (todos medidos pelo projeto)

12.366 registros da UFPE; 11 casos do OpenAlex; 12 casos da BDTD; 34 execuções do axe (17 telas × 2 larguras) sem violações; contraste mínimo de 4,5:1; 13 problemas de usabilidade (2 de gravidade 3, 3 de gravidade 2 e 8 de gravidade 1); 3 tentativas de raspagem com 0 resumos; SAST de 14/10 com 0 achados (bandit, semgrep, pip-audit) e 3 falsos positivos (ruff); contagem de testes e cobertura do `check` de 15/10. **Nenhum tempo e nenhuma porcentagem de ganho.** Antes de entregar, rode `python tasks.py test-stats` e confira a contagem de testes.

## 5. O que continua pendente e só você resolve

- A citação direta da UESPI (2024) na 2.1: conferir a grafia no PDF original.
- Pré-textuais (capa, folha de rosto, aprovação, resumo, abstract, listas e sumário). Faltam dados do
  orientador e do campus; detalhes em `PENDENCIAS_FINAIS_2026-10-15.md`.
- As figuras são de 15/10/2026: os resultados das fontes mudam com o tempo, o que é normal.
