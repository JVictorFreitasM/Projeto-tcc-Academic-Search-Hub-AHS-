# Relatório da OS-027 — Tratamento dos riscos do OWASP Top 10 (2017)

**Data:** 2026-10-09

## O que foi feito
- `docs/SEGURANCA.md` reescrito como a tabela completa **risco → onde ocorre → controle (arquivo) → teste** dos dez riscos de 2017, mais limitações conhecidas e controles detalhados.
- `tests/unit/test_code_hygiene.py` (248 verificações): SQL nunca montado com texto variável (AST de todo `app/`), XML só por `defusedxml`, nada de `pickle`/`eval`/`exec`/`yaml.load`, frontend sem `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`/`eval`, HTML sem script/estilo/manipuladores embutidos nem recursos externos, token fora do `localStorage`, `.env` ignorado e `.env.example` sem valores, varredura de segredos nos arquivos versionados, sem `debug`/`reload`/CORS curinga.
- `tests/integration/test_security_owasp.py` (19 testes): A5 percorrendo **todas as rotas com `bearerAuth` do OpenAPI** (sem token → 401; usuário B nos objetos do usuário A → 404 sem vazar nada; listagens nunca trazem dados de outro usuário), A3, A6, A7 (XSS armazenado), A1 (textos maliciosos em todas as entradas) e A10 (eventos gerados).
- Um teste e2e novo de XSS armazenado nas páginas de favoritos e histórico.

## Decisões tomadas
- A rota de busca aceita visitantes, mas o OpenAPI a lista com `bearerAuth`; a exceção está declarada em `OPTIONAL_AUTH` no teste, e **qualquer outra** rota com `bearerAuth` precisa exigir token.
- Uma rota nova com parâmetro de id (`{algo_id}`) **faz o teste falhar** até que se acrescente o objeto do dono: a varredura não envelhece em silêncio.
- O texto de `SEGURANCA.md` evita "100% seguro" e diz que o que vale é o que foi testado.

## Desvios em relação à OS
Nenhum.

## Correções feitas
Nenhum defeito de código foi encontrado nas varreduras. Os únicos ajustes foram nos critérios dos próprios testes (3 falsos positivos das varreduras iniciais: um `server_default` JSON, um comentário que cita `localStorage` e o nome público `AcademicSearchHub` do agente do `robots.txt`).

## Comandos executados e resultados
`python tasks.py check` verde.

## Critérios de aceite
- [x] Cada linha da tabela de `SEGURANCA.md` tem controle, arquivo e teste referenciados
- [x] O teste parametrizado de A5 percorre todas as rotas protegidas — `test_a5_*`
- [x] As varreduras de higiene (SQL concatenado, `innerHTML`, `xml.etree`, `pickle`, `eval`) passam — `test_code_hygiene.py`
- [x] Qualquer correção feita está listada no relatório (nenhuma de código nesta OS; ver acima)

## Evidência para o TCC
`docs/SEGURANCA.md` (base da seção 4.6). A linha A9 depende da OS-028 (`pip-audit`).
