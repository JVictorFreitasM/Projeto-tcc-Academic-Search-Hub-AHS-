# Raspagem complementar de resumo (OS-013)

## Quando a raspagem entra

- **Desligada por padrão** (`SCRAPING_ENABLED=false`). Com ela desligada, nenhuma requisição de
  raspagem é feita (teste `test_scraping_disabled_makes_no_call`).
- Só roda **depois** da busca e da deduplicação, e só para registros com `abstract` vazio e `url`
  `http`/`https`: no máximo **5 por busca**, com tempo total limitado.
- Só o **resumo** é extraído. Registros que já têm resumo nunca são raspados.
- Falhas são silenciosas (log de nível INFO) e **não** alteram o estado das fontes
  (`sources_status`); o esquema `Record` não muda.

## Como respeita as regras do site

- Lê e guarda o `robots.txt` de cada domínio e **não requisita** o que ele proíbe para
  `AcademicSearchHub`. `robots.txt` ausente (4xx) = permitido; erro de servidor (5xx) ou de rede =
  **proibido**, por prudência.
- Pausa mínima de **2 s por domínio** (inclusive entre o `robots.txt` e a página).
- Redirecionamentos são seguidos manualmente (até 3), e o destino passa de novo por `robots.txt` e
  pausa; páginas que respondem 401/403 (login) são ignoradas.
- Identifica-se com `User-Agent: AcademicSearchHub/<versão> (+contato: <CONTACT_EMAIL>)`, nunca com
  agente de navegador. Aceita só `text/html` com até 1 MB. Não contorna CAPTCHA nem bloqueio.

## Ordem de extração (sem heurística de parágrafo)

`citation_abstract` → `DC.description` → `og:description` (só com 200+ caracteres) → JSON-LD de um
`ScholarlyArticle` (`abstract` ou `description`).

## Medição

**Nenhuma medição foi feita ainda.** O script `scripts/measure_scraping.py` conta, em uma busca
real, quantos registros sem resumo tiveram o resumo completado. Rodar com a rede e as fontes
configuradas e só então citar o número que ele imprimir:

```
uv run python scripts/measure_scraping.py "tema do curso" --pages 2
```
