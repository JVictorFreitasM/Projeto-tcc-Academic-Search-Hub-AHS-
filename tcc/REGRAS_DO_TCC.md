# REGRAS DE ESCRITA DO TCC — LEIA ANTES DE ALTERAR QUALQUER TEXTO

**Trabalho:** Desenvolvimento de uma aplicação web para automação de busca e raspagem de dados em repositórios acadêmicos de acesso aberto
**Autor:** João Victor de Freitas Martins
**Instituição:** Universidade Estadual do Piauí — **UESPI**
**Curso:** Tecnólogo em Sistemas para a Internet

**Arquivo de trabalho:** `TCC_COMPLETO_Joao_Victor.docx`
**Versão deste arquivo de regras:** 2.0 — 15/10/2026, escrita sobre o conteúdo real do `.docx`

---

## 0. COMO USAR ESTE ARQUIVO

Você é uma IA editando o texto de um TCC. Este arquivo é a **autoridade** sobre forma, voz e citações. Se uma instrução do desenvolvedor contrariar uma regra marcada como **inviolável**, pare e pergunte em vez de obedecer.

O documento de trabalho é a **versão anotada**: ele contém, de propósito, texto em **vermelho e itálico** que são avisos ao autor, e **não** fazem parte do TCC. A seção 3 deste arquivo explica como tratar cada tipo.

**Antes de editar:** leia a regra que se aplica ao trecho.
**Depois de editar:** percorra a lista de verificação da seção 13.

**Três proibições que valem para o documento inteiro:**

1. **Não invente dado bibliográfico.** Nenhum volume, número, página, ano, DOI, editora ou cidade que não tenha sido lido na fonte.
2. **Não invente número de resultado.** Nenhuma porcentagem, tempo, quantidade ou ganho que não tenha saído de uma medição feita pelo projeto.
3. **Não acrescente comentário novo seu ao documento.** Os avisos em vermelho que já existem são do autor e seguem as regras da seção 3. Dúvidas suas vão na resposta ao desenvolvedor.

---

## 1. ESTADO REAL DO DOCUMENTO

O `.docx` começa direto em `1 INTRODUÇÃO`. Confira antes de supor qualquer coisa.

| Parte | Está no arquivo? | Estado |
|---|---|---|
| Capa, folha de rosto, folha de aprovação | **não** | a montar |
| Dedicatória, agradecimentos | **não** | a montar |
| Resumo, abstract, palavras-chave | **não** | a escrever |
| Listas de figuras, quadros, siglas | **não** | a montar |
| Sumário | **não** | o Word gera |
| 1 INTRODUÇÃO | sim | **pronta** |
| 2 REFERENCIAL TEÓRICO (2.1 a 2.6) | sim | **pronto**, com 3 marcações pendentes |
| 3 DELINEAMENTO METODOLÓGICO | sim | **pronto** |
| 4 RESULTADOS E DISCUSSÕES (4.1 a 4.6) | sim | **só os títulos**, com roteiro em vermelho |
| 5 CONCLUSÕES | sim | **roteiro em vermelho** + lista de trabalhos futuros pronta |
| REFERÊNCIAS | sim | 36 entradas, com lacunas marcadas |
| APÊNDICE — NOTAS PARA O AUTOR | sim | 18 notas, **todo o apêndice é descartável** |

**Atenção:** a seção 5 **não** tem subtítulo `5.1`. A lista de trabalhos futuros vem solta, depois da frase "Como perspectivas para a continuidade do projeto…". Não crie o `5.1` sem o desenvolvedor pedir.

**Nota fora de ordem:** no apêndice, a nota 13 aparece **depois** da 18. É só ordem de exibição; se mexer no apêndice, pode reordenar.

**Títulos, exatamente como estão** (não renomeie, não renumere):

`1 INTRODUÇÃO` · `2 REFERENCIAL TEÓRICO` · `2.1 PESQUISA ACADÊMICA E ACESSO ABERTO NO BRASIL` · `2.2 REPOSITÓRIOS, INTEROPERABILIDADE E COLETA DE DADOS` · `2.3 ARQUITETURA DE SOFTWARE: REST E JSON` · `2.4 TECNOLOGIAS DE DESENVOLVIMENTO: PYTHON, FASTAPI, POSTGRESQL E FRONT-END WEB` · `2.5 INTERFACE, USABILIDADE, ACESSIBILIDADE E ORGANIZAÇÃO DA INFORMAÇÃO` · `2.6 SEGURANÇA E LGPD` · `3 DELINEAMENTO METODOLÓGICO` · `4 RESULTADOS E DISCUSSÕES` · `4.1 APRESENTAÇÃO DO ARTEFATO DESENVOLVIDO` · `4.2 INTEGRAÇÃO, NORMALIZAÇÃO E COLETA DE DADOS` · `4.3 ARQUITETURA E TECNOLOGIAS` · `4.4 INTERFACE, USABILIDADE E ACESSIBILIDADE` · `4.5 FAVORITOS E EXPORTAÇÃO DE RESULTADOS` · `4.6 SEGURANÇA E PRIVACIDADE (LGPD)` · `5 CONCLUSÕES` · `REFERÊNCIAS`

---

## 2. A VOZ DE CADA SEÇÃO (REGRAS INVIOLÁVEIS)

Esta é a regra mais importante do trabalho. Cada seção tem uma voz e um regime de citação próprios.

| Seção | Tempo verbal | Citações | Voz |
|---|---|---|---|
| 1 Introdução | presente | **nenhuma, jamais** | impessoal |
| 2 Referencial | presente | **somente citações** | dos autores |
| 3 Delineamento | **passado** | **nenhuma** | impessoal |
| 4 Resultados | **passado** | obrigatórias, retomando o referencial | do autor |
| 5 Conclusões | passado | poucas ou nenhuma | do autor |

### 2.1 Introdução: zero citação

**Inviolável.** Não existe citação na Introdução. Nem autor-data, nem nota, nem "segundo", nem "de acordo com". Nenhuma.

Pode nomear coisas do mundo (CORE, SciELO, OpenAlex, BDTD, UESPI, UFPI, OAI-PMH, Python, FastAPI, PostgreSQL) sem citar ninguém.

- ERRADO: `Segundo Lynch (2003), os repositórios institucionais preservam a produção intelectual.`
- CERTO: `Os repositórios institucionais e o movimento de acesso aberto ampliaram a disponibilidade de literatura científica gratuita.`

### 2.2 Referencial: somente citações, nunca a voz do autor

**Inviolável.** Cada parágrafo do capítulo 2 é atribuído a alguém. Não pode haver frase que soe como opinião, escolha ou conclusão do autor do TCC.

Todo período precisa de uma destas amarrações: `Segundo X (ano)`, `De acordo com X (ano)`, `Conforme X (ano)`, `X (ano) afirma/descreve/mostra/propõe/analisa`, ou `… (X, ano)` no fim.

Proibido no capítulo 2:
- Frase sem autor nenhum, mesmo que verdadeira.
- Juízo de valor: "a melhor opção", "a tecnologia mais adequada", "é fundamental", "nota-se que".
- Decisão de projeto: "optou-se por", "neste trabalho foi escolhido", "o sistema utiliza".
- Ligação que o autor faz entre duas fontes e que nenhuma das duas faz.

Onde isso vai? **Decisão de projeto vai para a seção 4**, retomando a fonte. A escolha de REST pertence à 4.3, não à 2.3.

- ERRADO: `O JSON é o formato mais indicado para APIs modernas, por isso foi adotado neste trabalho.`
- CERTO: `Bray (2017) especifica o JSON (JavaScript Object Notation) como um formato textual, legível e independente de linguagem para representar estruturas de dados.`

**Exceção de forma:** os três parágrafos da 2.4 começam com um rótulo em negrito (`Servidor.`, `Banco de dados.`, `Interface.`). O rótulo é organização, não voz do autor. Mantenha.

### 2.3 Delineamento: passado e zero citação

**Inviolável.** O capítulo 3 descreve o que **foi feito**, no passado, e **sem citar ninguém**. Nem Gil, nem Marconi e Lakatos, nem ninguém.

- ERRADO: `Segundo Gil (2002), a pesquisa aplicada busca…`
- ERRADO: `O trabalho caracteriza-se como pesquisa aplicada.` (presente)
- CERTO: `O presente trabalho caracterizou-se como uma pesquisa aplicada, pois buscou propor uma solução tecnológica para reduzir o esforço de busca…`

### 2.4 Resultados: voz do autor, passado, retomando o referencial

Aqui, e só aqui, o autor fala. Cada subseção de 4 deve **retomar explicitamente** os autores da seção correspondente de 2. Ver o mapa da seção 6.

- CERTO: `A API foi construída sem guardar estado entre requisições, conforme o estilo descrito por Fielding (2000).`

### 2.5 Conclusões

Só o que foi medido ou observado. Nenhuma afirmação de ganho sem a medição da seção 8.

---

## 3. O TEXTO EM VERMELHO: TRÊS TIPOS, TRÊS TRATAMENTOS

Todo texto vermelho e itálico do documento é aviso ao autor e **não** é conteúdo do TCC. Há três tipos, e cada um sai de uma forma diferente.

### Tipo A — Roteiros das seções 4 e 5

Parágrafos que começam com `ROTEIRO (apagar):`, logo abaixo de `4`, `4.1` a `4.6` e `5`.

**O que fazer:** ao escrever a seção, **substitua** o roteiro pelo texto real. O roteiro é a instrução do que escrever ali; leia antes e apague depois. Nunca deixe o roteiro conviver com o texto final, e nunca apague o roteiro sem escrever a seção.

### Tipo B — Marcações dentro do referencial

São **três**, e cada uma sinaliza uma citação ou referência com problema. Estão no meio de parágrafos que no resto estão prontos.

| Onde | Marcação | Decisão pendente |
|---|---|---|
| 2.4, parágrafo `Banco de dados.` | `[VERIFICAR esta citação: ver nota 3 no apêndice]` | Jung et al. (2015) não foi localizada |
| 2.4, parágrafo `Interface.` | `[VERIFICAR qual documento do W3C: ver nota 5]` | o documento de CSS citado como (W3C, 2018a) não foi identificado |
| 2.5, parágrafo da acessibilidade | `[VERIFICAR esta citação: ver nota 4]` | Nagaraju, Chawla e Rana (2019) não foi localizada |

**O que fazer:** a marcação só sai junto com a decisão. Duas saídas legítimas para cada uma:

- **Confirmar:** o desenvolvedor traz a fonte real. Corrija os dados na referência, apague a marcação e pronto.
- **Remover:** a fonte não se confirma. Retire a citação do parágrafo, retire a referência órfã da lista e apague a marcação. Depois, reescreva o período para continuar correndo bem.

**Proibido:** apagar a marcação e deixar a citação. Isso transforma um problema sinalizado em erro escondido.

### Tipo C — Lacunas nas referências e o apêndice

Trechos como `[COMPLETAR …]`, `[conferir …]`, `[inserir a data]`, `[prenome]`, `[título]` dentro das entradas de REFERÊNCIAS, mais o `APÊNDICE — NOTAS PARA O AUTOR` inteiro, com as 18 notas.

**O que fazer:** cada lacuna sai quando o dado real entra. O apêndice inteiro é **descartável**: apague do primeiro ao último parágrafo antes da entrega, inclusive o título.

### A regra que une os três

**Nenhum texto vermelho pode chegar à versão entregue.** Mas "limpar o vermelho" não é uma tarefa de formatação: cada marca só sai quando o problema que ela aponta foi resolvido. Se o desenvolvedor pedir só para limpar as cores, avise o que ainda está pendente e pergunte antes.

---

## 4. FORMATAÇÃO

**Aviso:** o manual de normalização da UESPI tem prioridade sobre tudo nesta seção. Se o desenvolvedor trouxer o manual, siga o manual e avise que mudou.

| Item | Valor no arquivo |
|---|---|
| Fonte | Times New Roman, 12 |
| Margens | 3 cm superior e esquerda, 2 cm inferior e direita |
| Espaçamento do corpo | 1,5 |
| Recuo da primeira linha | 1,25 cm |
| Alinhamento do corpo | justificado |
| Espaçamento das referências | simples, com uma linha em branco entre entradas |
| Alinhamento das referências | à esquerda, sem recuo |
| Idioma | português do Brasil |

**Títulos:** maiúsculas e negrito, tanto nas seções primárias quanto nas secundárias. Sem ponto depois do número (`1 INTRODUÇÃO`, não `1. INTRODUÇÃO`) e sem ponto no fim. `REFERÊNCIAS` e os pré-textuais não são numerados.

**Figuras e quadros:** legenda acima, numerada, e a fonte abaixo. Para tela do próprio sistema: `Fonte: Elaborado pelo Autor (2026)`.

**Proibido no texto final:** cor, emoji, marcador de tarefa, comentário do Word, colchete de aviso. Itálico só para palavra estrangeira não incorporada e para título de obra citado dentro do texto.

**Estrangeirismos:** `web scraping`, `stateless`, `tsvector` em itálico na primeira aparição. `Web`, `site`, `software`, `online` e `e-mail` já estão incorporados: sem itálico.

---

## 5. CITAÇÕES (ABNT, SISTEMA AUTOR-DATA)

| Caso | Dentro da frase | Fim da frase |
|---|---|---|
| 1 autor | `Suber (2012)` | `(SUBER, 2012)` |
| 2 autores | `Chan e Zeng (2006)` | `(CHAN; ZENG, 2006)` |
| 3 autores | `Priem, Piwowar e Orr (2022)` | `(PRIEM; PIWOWAR; ORR, 2022)` |
| 4 ou mais | `Lagoze et al. (2002)` | `(LAGOZE et al., 2002)` |
| Instituição | `o OWASP (2017)` | `(OWASP, 2017)` |
| Sem data | `Pathak, Mamloda e Patel (s.d.)` | `(PATHAK; MAMLODA; PATEL, [s. d.])` |
| Mesmo autor e ano | `(W3C, 2018a)` e `(W3C, 2018b)` | a letra vai no texto **e** na lista |

Dentro da frase: só a inicial maiúscula. No fim: tudo em maiúsculas, dentro dos parênteses.

**Citação direta:** até 3 linhas, no corpo, entre aspas, com página. Mais de 3 linhas, recuo de 4 cm, fonte 10, espaçamento simples, sem aspas. Para lei, cita artigo e inciso, não página: `(BRASIL, 2018, art. 6º, incisos III, VII e VIII)`.

**Citação direta já no texto:** a 2.1 traz `"armazenar, preservar, organizar e permitir o amplo acesso do repertório da produção intelectual"`, de UESPI (2024). Ela veio de um PDF com falhas de reconhecimento de texto; confira a grafia no original antes da entrega.

**Duas regras de ouro:**

- **Nunca cite uma fonte que não foi lida.** Se faltar fonte para sustentar uma afirmação, diga que falta, em vez de escolher um autor plausível.
- **Nunca atribua a uma fonte algo que ela não diz.** Caso real deste trabalho: Santarém Segundo e Vidotti (2011) tratam de tags e folksonomia, **não** de exportação de referências.

---

## 6. MAPA OBRIGATÓRIO: SEÇÃO 2 → SEÇÃO 4

Ao escrever cada subseção de Resultados, retome estes autores. O roteiro em vermelho de cada subseção repete isso; os dois precisam continuar dizendo a mesma coisa.

| Subseção de 4 | Autores a retomar |
|---|---|
| 4.1 Artefato | nenhum obrigatório; aqui entram as telas |
| 4.2 Integração e coleta | Lagoze et al. (2002); Almeida e Dias (2023); UESPI (2024); Chan e Zeng (2006); Zeng e Chan (2006); Vargiu e Urru (2012) |
| 4.3 Arquitetura | Fielding (2000); Rodríguez et al. (2016); Palma et al. (2017); Bray (2017); Ramírez (2018); Stonebraker e Kemnitz (1991); Krocz, Kizun e Skublewska-Paszkowska (2020) |
| 4.4 Interface | Bader e Hammouri (2016); W3C (2018b); Cybis, Betiol e Faust (2010); Prates e Barbosa (2003) |
| 4.5 Favoritos e exportação | Santarém Segundo e Vidotti (2011), **só** para organização por tags |
| 4.6 Segurança e LGPD | Brasil (2018); OWASP (2017); Nunes et al. (2018) |

**Condição para 4.3:** Rodríguez et al. (2016) e Palma et al. (2017) só podem ser retomados junto com a autoavaliação da própria API (verbo HTTP, nome do recurso, código de status, ausência de estado). Citar sem essa tabela é citação decorativa.

**Condição para 4.4:** Cybis, Betiol e Faust (2010) e Prates e Barbosa (2003) tratam de **métodos de avaliação**. Só entram se uma avaliação de usabilidade tiver sido feita. Se o método aplicado for de outro autor, cite esse outro autor.

---

## 7. TERMOS FIXOS (USE SEMPRE A MESMA FORMA)

| Use | Nunca use |
|---|---|
| UESPI | UEPI, U.E.S.P.I. |
| OAI-PMH | OAI, oai-pmh |
| BDTD, por extenso na primeira vez | BDTD/IBICT |
| SciELO | Scielo, SCIELO |
| OpenAlex, CORE | Open Alex, Core |
| LGPD, por extenso na primeira vez | Lei Geral de Proteção de Dados sem a sigla |
| WCAG 2.1 | WCAG, WCAG 2.0 |
| OWASP Top 10 (2017) | OWASP Top Ten |
| web scraping, ou raspagem de dados | scraping |
| aplicação web | app, sistema web, plataforma |
| estudante de graduação | usuário final, cliente |

**As seis fontes, sempre nesta ordem:** CORE, SciELO, OpenAlex, BDTD, UFPI e UESPI.

Toda sigla é escrita por extenso na primeira aparição, com a sigla entre parênteses, e depois só a sigla.

---

## 8. AFIRMAÇÕES QUE EXIGEM MEDIÇÃO

**Inviolável.** Estas frases não podem existir no TCC sem um dado medido pelo próprio projeto:

- "reduz o tempo de busca", "economiza X minutos", "é mais rápido que"
- "cobre X% da literatura", "a maior parte dos trabalhos"
- "melhora a experiência do usuário", "é mais fácil de usar"
- qualquer porcentagem, qualquer tempo, qualquer contagem

**Se a medição não existir, a frase sai do texto.** Não substitua por versão mais branda ("tende a reduzir", "pode reduzir"): a frase sai.

**Porcentagem com amostra pequena é proibida.** Com 3 a 5 participantes, descreva o que aconteceu; não calcule percentual.

A justificativa da Introdução pode falar de **esforço repetitivo** e de **consultar vários sistemas**: isso descreve o problema, não mede resultado.

---

## 9. DIVERGÊNCIAS CONHECIDAS, A DECLARAR NA SEÇÃO 4

1. **Tags contra anotação.** A 2.5 cita organização por tags. O sistema guarda **anotação em texto livre**. Na 4.5, descreva a anotação e diga que a organização por tags discutida por Santarém Segundo e Vidotti (2011) não foi implementada nesta versão.
2. **Raspagem.** Ela não supre fonte sem interface programática: as seis fontes têm API ou OAI-PMH. Ela completa campo ausente, como o resumo, e fica **desligada por padrão**. Se não for ligada, diga na 4.2 que foi especificada e não usada.
3. **Total estimado.** O total de resultados é **estimativa**, somando os totais das fontes. Escreva sempre a palavra "estimativa"; nunca apresente como contagem exata.
4. **Repositório da UESPI.** Pode não expor OAI-PMH. Se não expuser, é **limitação declarada** na 4.2 e nas Conclusões. Não é motivo para raspar o repositório, e não se resolve escrevendo que funciona.

---

## 10. ESCOPO (NÃO PROMETA O QUE O SISTEMA NÃO FAZ)

**Dentro:** busca unificada nas seis fontes · filtros por ano e tipo · favoritos com anotação · exportação em BibTeX, RIS, JSON e CSV · histórico de buscas · cadastro e login · API pública REST em JSON documentada em OpenAPI · interface responsiva · acessibilidade WCAG 2.1 · LGPD · OWASP Top 10 (2017).

**Fora, e já listado como trabalho futuro na seção 5:** aplicativo móvel nativo · recomendação de trabalhos · repositórios de outras universidades · alertas de novas publicações · integração direta com Zotero e Mendeley · outros idiomas · autenticação em dois fatores.

- Não acrescente função ao escopo sem o desenvolvedor pedir.
- A lista de trabalhos futuros da seção 5 e a lista de fora do escopo das Ordens de Serviço precisam dizer a mesma coisa. Se mudar uma, avise que a outra muda.
- **Não descreva na seção 4 tela ou função que ainda não existe.** Se só a busca, os resultados e os filtros foram implementados, a 4.5 e a 4.6 continuam com o roteiro, não com texto inventado.

---

## 11. REFERÊNCIAS

São **36 entradas**, em ordem alfabética, sem numeração. Sobrenome em maiúsculas, título da obra ou do periódico em negrito. Toda entrada com endereço eletrônico precisa de `Disponível em:` e `Acesso em:`. Dado desconhecido usa `[s. l.]`, `[s. n.]`, `[s. d.]`. Edição só aparece a partir da segunda.

**Regra de integridade:** toda citação do texto tem entrada na lista, e toda entrada da lista é citada no texto. Ao remover uma citação, remova a referência órfã; ao acrescentar uma citação, acrescente a referência.

### 11.1 Conferidas — não altere os dados

Almeida e Dias (2023) · Bader e Hammouri (2016) · Brasil (2018) · Chan e Zeng (2006) · Fielding (2000) · Knoth e Zdrahal (2012) · Krocz, Kizun e Skublewska-Paszkowska (2020) · Lagoze et al. (2002) · Nunes et al. (2018) · Palma et al. (2017) · Priem, Piwowar e Orr (2022) · Rodríguez et al. (2016) · Santarém Segundo e Vidotti (2011) · Stonebraker e Kemnitz (1991) · UESPI (2024) · Vargiu e Urru (2012) · Zeng e Chan (2006)

Duas delas têm pendência pequena, já marcada na própria entrada: em Almeida e Dias, o volume (21) não combina com o DOI (v20); em Nunes et al., confirmar se é esse o artigo lido.

### 11.2 Incompletas — o dado real tem de vir do desenvolvedor

Bray (2017) · Cybis, Betiol e Faust (2010) · Flanagan (2013) · IBICT (2005) · Lynch (2003) · Menezes (2010) · OWASP (2017) · Packer (1998) · Pathak, Mamloda e Patel (s.d.) · Prates e Barbosa (2003) · Ramírez (2018) · Suber (2012) · Teruel (2014) · Van Rossum (1991) · W3C (2014) · W3C (2018a) · W3C (2018b)

Cada uma traz, em vermelho, o que falta. **Não preencha essas lacunas de memória.** Atualize só com o dado que o desenvolvedor trouxer.

### 11.3 Duas entradas sem fonte localizada

- **JUNG et al. (2015)**, citada na 2.4. O trabalho não foi localizado; o artigo mais próximo é de 2017 e compara MongoDB com MySQL, não com PostgreSQL. A entrada na lista está só com os campos em branco.
- **NAGARAJU, CHAWLA e RANA (2019)**, citada na 2.5. Não localizada. O artigo que diz exatamente aquilo é *Web Accessibility Challenges*, de Abuaddous, Jali e Basir, no **International Journal of Advanced Computer Science and Applications**, v. 7, n. 10, p. 172-181, 2016, DOI 10.14569/IJACSA.2016.071023. Se o desenvolvedor adotar essa fonte, troque o nome na 2.5, na 4.4 e na lista.

Enquanto não houver decisão, as duas ficam como estão, com a marcação. **Não complete os campos em branco com dados plausíveis.**

### 11.4 Decisão aberta sobre o OWASP

O texto cita a edição de **2017**. Existe a de 2021. Escolha uma e use a mesma em todo o trabalho, inclusive no arquivo de Ordens de Serviço.

---

## 12. CORREÇÕES JÁ APLICADAS (NÃO DESFAÇA)

| Era | Virou | Motivo |
|---|---|---|
| UEPI | UESPI | sigla correta |
| Hammouri e Bader (2016) | **Bader e Hammouri (2016)** | a ordem dos autores no artigo é Bader primeiro |
| raspagem supre fonte sem API | raspagem completa campo ausente | as seis fontes têm API ou OAI-PMH |
| Santarém Segundo e Vidotti para exportação | para organização por tags | é disso que o artigo trata |
| (W3C, 2018) duas vezes | (W3C, 2018a) e (W3C, 2018b) | mesmo autor e ano exigem letra |
| três repositórios | seis fontes | BDTD, UFPI e UESPI entraram no escopo |

---

## 13. LISTA DE VERIFICAÇÃO ANTES DE ENTREGAR UMA EDIÇÃO

- [ ] A Introdução continua **sem nenhuma** citação.
- [ ] Todo parágrafo do capítulo 2 está atribuído a um autor; nenhuma frase soa como opinião ou decisão do autor do TCC.
- [ ] O capítulo 3 está no passado e sem citação.
- [ ] Nenhum título foi criado, renomeado ou renumerado.
- [ ] Nenhum número sem medição entrou no texto.
- [ ] Nenhum dado bibliográfico foi inventado nem preenchido de memória.
- [ ] Nenhuma marcação em vermelho foi apagada sem o problema ter sido resolvido.
- [ ] Nenhum roteiro foi apagado sem a seção ter sido escrita.
- [ ] Toda citação tem referência, e toda referência é citada.
- [ ] A lista de referências continua em ordem alfabética.
- [ ] Siglas por extenso na primeira aparição; termos da seção 7 na forma fixa.
- [ ] As seis fontes aparecem na ordem CORE, SciELO, OpenAlex, BDTD, UFPI e UESPI.
- [ ] Nenhuma função fora do escopo foi prometida, e nenhuma tela inexistente foi descrita.
- [ ] A seção 4 declara as divergências da seção 9 que se aplicam.

### 13.1 Checagem extra, só na versão que vai ser entregue

- [ ] Zero texto vermelho ou itálico de aviso no documento.
- [ ] Zero `ROTEIRO (apagar):`, `[VERIFICAR`, `[COMPLETAR`, `[conferir`, `[inserir`.
- [ ] O `APÊNDICE — NOTAS PARA O AUTOR` foi apagado inteiro, título incluído.
- [ ] Os pré-textuais da seção 1 deste arquivo foram montados.
- [ ] O sumário foi gerado depois de aplicar os estilos de título.

---

## 14. ARQUIVOS DO PROJETO

| Arquivo | O que é |
|---|---|
| `TCC_COMPLETO_Joao_Victor.docx` | **o arquivo de trabalho**: texto do TCC + avisos em vermelho + apêndice de notas. É aqui que se edita |
| `TCC_versao_para_o_professor.docx` | versão limpa gerada a partir dele, para mostrar. Fica **desatualizada** a cada edição do arquivo de trabalho |
| `REFERENCIAS_TCC.docx` | as referências separadas, com as lacunas marcadas |
| `ORDENS_DE_SERVICO_SISTEMA_v1.2.md` | as 37 ordens de serviço do sistema, com a Fatia 1 para gerar as telas |
| `REGRAS_DO_TCC.md` | este arquivo |

**Regra:** edite o arquivo de trabalho. Quando o texto mudar, avise que a versão para o professor precisa ser gerada de novo.

**Relação com as Ordens de Serviço:** se uma alteração no TCC mudar o que o sistema precisa fazer, avise que a OS correspondente também muda. O caminho inverso vale igual: se o sistema entregar algo diferente do que o TCC afirma, o **TCC** se ajusta ao sistema, e não o contrário.

---

## 15. QUANDO PARAR E PERGUNTAR

- For preciso uma fonte para sustentar uma afirmação e nenhuma das confirmadas servir.
- O desenvolvedor pedir citação na Introdução ou no Delineamento.
- O desenvolvedor pedir um número que não foi medido.
- O desenvolvedor pedir para "limpar as marcações" sem resolver o que elas apontam.
- A alteração exigir criar, renomear ou renumerar título.
- O manual de normalização da UESPI contrariar a seção 4 deste arquivo.
- Surgir função nova, fora da lista da seção 10.
- Faltar o dado bibliográfico de uma referência que precisa ser acrescentada.
