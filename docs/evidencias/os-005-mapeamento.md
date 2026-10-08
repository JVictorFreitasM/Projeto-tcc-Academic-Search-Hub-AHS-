# Mapeamento "campo da fonte → campo unificado" (OS-005)

Tabela viva: cada conector (OS-007 a OS-010) confirma a sua coluna com uma resposta real e
registra aqui o que mudou. Os itens `[VERIFICAR]` ainda não foram conferidos com resposta real.

| Campo unificado (`Record`) | OpenAlex (OS-007) | CORE (OS-008) | Fontes OAI `oai_dc` (OS-009) |
|---|---|---|---|
| `id` | `doi:<doi>` ou `src:openalex:<W...>` | `doi:<doi>` ou `src:core:<id>` | `doi:<doi>` ou `src:<slug>:<oai_identifier>` |
| `title` | `title` (ou `display_name`) | `title` | primeiro `dc:title` |
| `authors[].name` | `authorships[].author.display_name` `[VERIFICAR]` | `authors[].name` | cada `dc:creator` |
| `authors[].orcid` | `authorships[].author.orcid` `[VERIFICAR]` | — | — |
| `abstract` | `abstract_inverted_index` (reconstruído) | `abstract` | `dc:description` mais longo |
| `year` | `publication_year` | campo de ano `[VERIFICAR]` ou `publishedDate` | primeiro `dc:date` válido |
| `doi` | `doi` | `doi` | `dc:identifier`/`dc:relation` com DOI |
| `url` | `primary_location.landing_page_url` `[VERIFICAR]`, senão DOI, senão `open_access.oa_url` | página CORE (`/works/<id>`) ou `sourceFulltextUrls` | primeiro `dc:identifier` `http(s)` que não seja só o DOI nem `.pdf` |
| `pdf_url` | `primary_location.pdf_url` / `best_oa_location.pdf_url` | `downloadUrl` | `dc:identifier`/`dc:relation` terminado em `.pdf` ou com `/bitstream/` |
| `type` | `type` → tabela `OPENALEX_TYPE_MAP` | `documentType` → `CORE_TYPE_MAP` `[VERIFICAR]` | todos os `dc:type` → `map_oai_type` + `type_map`/`default_type` da fonte |
| `language` | `language` (ISO 639-1) | campo `[VERIFICAR]` | `dc:language` → `normalize_language` |
| `keywords` | `keywords[].display_name` | — | `dc:subject` |
| `sources[]` | `openalex` / id curto / URI | `core` / `id` / página CORE | `<slug>` / `oai_identifier` / `url` |

Funções usadas (todas em `app/services/`): `normalize_doi`, `clean_text`, `normalize_author`,
`parse_year`, `normalize_language`, `safe_url`, `build_record_id`, `map_openalex_type`,
`map_core_type`, `map_oai_type`.
