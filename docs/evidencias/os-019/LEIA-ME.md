# Exemplos de exportação (OS-019)

Arquivos `exemplo.bib`, `exemplo.ris`, `exemplo.csv` e `exemplo.json`, gerados por
`app/services/export_service.py` com **dois registros fictícios** (não são resultados reais).

## Teste manual de importação (pendente — desenvolvedor)

A importação em um gerenciador de referências é um passo manual. Roteiro:

1. Abrir o Zotero (ou o Mendeley) e importar `exemplo.bib`; depois `exemplo.ris`.
2. Conferir: título, autores (ordem e sobrenome), ano, DOI, URL, resumo e palavras-chave; o tipo da
   tese (`@thesis` no BibTeX e `THES` no RIS) e o artigo (`@article` / `JOUR`).
3. Registrar abaixo o gerenciador e a versão, o que importou corretamente e o que falhou.

| Arquivo | Gerenciador e versão | Resultado | Observações |
|---|---|---|---|
| exemplo.bib | *(preencher)* | *(preencher)* | |
| exemplo.ris | *(preencher)* | *(preencher)* | |

Ponto a observar: o BibTeX usa `@thesis` (tipo do BibLaTeX) para teses e dissertações, pois o
sistema não distingue mestrado de doutorado. Se algum gerenciador não reconhecer o tipo, registrar
em `docs/DECISOES.md`.
