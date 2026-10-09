# Diagrama de sequência da busca (OS-012)

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário (navegador)
    participant API as FastAPI /api/v1/search
    participant S as SearchService
    participant OA as Conector OpenAlex
    participant CO as Conector CORE
    participant OL as Conectores OAI locais (SciELO, BDTD, UFPI, UESPI)
    participant DB as PostgreSQL (oai_records)
    participant D as Deduplicação

    U->>API: GET /search?q=...&year_from=...&type=...
    API->>S: search(SearchParams, usuário opcional)
    S->>S: valida fontes pedidas
    par disponibilidade (chave configurada? fonte já colhida?)
        S->>OA: availability()
        S->>CO: availability()
        S->>OL: availability()
        OL->>DB: existe registro?
    end
    S->>S: k = fontes ativas; por fonte = ceil(page_size / k)
    par consulta em paralelo, com tempo limite global por fonte
        S->>OA: search(página, filtros)
        OA-->>S: registros + total (ou timeout/erro/limite)
        S->>CO: search(página, filtros)
        CO-->>S: registros + total (ou timeout/erro/limite)
        S->>OL: search(página, filtros)
        OL->>DB: websearch_to_tsquery + filtros + ordenação
        DB-->>OL: linhas + COUNT
        OL-->>S: registros + total
    end
    S->>S: intercala (primeiro de cada fonte, depois o segundo...)
    S->>D: deduplicate(DOI, depois título+ano+autor)
    D-->>S: registros únicos com todas as fontes
    S->>S: corta em page_size; ordena por ano se pedido
    S->>DB: favoritos do usuário para os ids da página (se logado)
    S-->>API: SearchResponse (total estimado + sources_status)
    API-->>U: 200 JSON (ou 502 se todas as fontes falharam)
```

Falha parcial (D4): uma fonte com erro, timeout ou limite aparece em `sources_status` e as demais
seguem. Só quando **nenhuma** fonte responde (ou todas estão desabilitadas) a resposta é 502, com o
`sources_status` ao lado de `error`.
