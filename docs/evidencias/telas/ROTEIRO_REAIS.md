# Roteiro: capturas com dados reais das fontes (passo manual do desenvolvedor)

As capturas geradas por `scripts/capture_screens.py` usam dados de **demonstração** e a API simulada.
Para ilustrar a integração com as fontes de verdade (seção 4.1), faça estas capturas à mão. A IA não
pode fazê-las: dependem das suas chaves e das fontes reais.

## Antes de começar

1. Preencha `OPENALEX_API_KEY` e `CORE_API_KEY` no `.env` (OS-007 e OS-008) e suba a aplicação
   (`python tasks.py run`, ver `docs/EXECUCAO.md`).
2. Para as fontes OAI (BDTD, UFPI, UESPI, SciELO): confirme os endereços reais, habilite cada fonte
   em `config/sources.yaml` e rode a colheita (OS-009/OS-010). Fontes não colhidas aparecem como
   indisponíveis; isso também pode ser capturado, mas registre o motivo.
3. Navegador em janela de computador (cerca de 1280 px) e, para as de celular, o modo de dispositivo
   do navegador (390 px de largura).

## Buscas, na ordem

| # | O que fazer | O que a captura mostra |
|---|---|---|
| R1 | Buscar `letramento digital` sem filtros | Resultados reunidos de várias fontes, com os selos de origem |
| R2 | Na mesma busca, abrir um resultado que tenha mais de uma fonte | Registro fundido (deduplicação por DOI) |
| R3 | Aplicar o filtro de ano (ex.: 2018 a 2024) e tipo "Tese ou dissertação" | Filtros ativos sobre dados reais |
| R4 | Buscar uma frase entre aspas, ex.: `"ensino médio"` | Busca por expressão exata nas fontes locais |
| R5 | Com uma fonte desligada ou sem chave, repetir R1 | Aviso de erro parcial real |
| R6 | Entrar, favoritar dois resultados e abrir `favoritos.html` | Favoritos com dados reais (use conta de teste) |

## Antes de guardar cada imagem (obrigatório)

- **Remova ou cubra a chave de API.** Ela não aparece na interface, mas confira a aba de rede se
  houver captura das ferramentas do navegador.
- **Não mostre e-mail nem nome verdadeiros.** Use uma conta de teste (ex.: `teste@example.org`) e
  confira o cabeçalho ("Minha conta (...)") e a tela de conta.
- Não mostre o token (`ash.token`) nem o conteúdo de `.env`.
- Confira a barra de endereço: sem parâmetros que identifiquem você.

## Onde guardar e como citar

Salve em `docs/evidencias/telas/reais/` com nomes `4.1-R1-resultados-reais.png` etc. e acrescente
uma linha por imagem em `INDICE.md`, com a data da captura e a legenda
**Fonte: Elaborado pelo Autor (2026)**. No texto do TCC, deixe claro que essas imagens são de
dados reais e que as demais, geradas por script, são de demonstração.
