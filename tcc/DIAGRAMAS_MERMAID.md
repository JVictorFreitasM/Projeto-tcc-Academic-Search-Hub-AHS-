# Diagramas Mermaid do Academic Search Hub

Os diagramas abaixo foram derivados das rotas, serviços, conectores, modelos SQLAlchemy e migrações
existentes no projeto em 15/10/2026.

## 1. Diagrama de casos de uso

O Mermaid não possui uma notação UML nativa para casos de uso; o `flowchart` abaixo preserva os
atores, a fronteira do sistema e as relações funcionais.

```mermaid
flowchart LR
    visitante[Visitante]
    usuario[Usuário autenticado]
    administrador[Administrador técnico]

    subgraph sistema[Academic Search Hub]
        pesquisar([Pesquisar por tema ou autor])
        filtrar([Filtrar e ordenar resultados])
        consultar([Abrir trabalho ou PDF])
        exportar([Exportar resultados])
        cadastrar([Criar conta])
        autenticar([Entrar na conta])
        favoritos([Gerenciar favoritos e anotações])
        historico([Consultar ou limpar histórico])
        perfil([Gerenciar perfil e senha])
        dados([Exportar dados pessoais])
        excluir([Excluir conta])
        politica([Consultar política de privacidade])
        fontes([Consultar estado das fontes])
        colher([Validar e colher fonte OAI-PMH])
        monitorar([Consultar saúde da aplicação])
    end

    visitante --> pesquisar
    visitante --> filtrar
    visitante --> consultar
    visitante --> exportar
    visitante --> cadastrar
    visitante --> autenticar
    visitante --> politica
    visitante --> fontes

    usuario --> pesquisar
    usuario --> filtrar
    usuario --> consultar
    usuario --> exportar
    usuario --> favoritos
    usuario --> historico
    usuario --> perfil
    usuario --> dados
    usuario --> excluir
    usuario --> politica
    usuario --> fontes

    administrador --> colher
    administrador --> monitorar

    filtrar -. estende .-> pesquisar
    consultar -. estende .-> pesquisar
    favoritos -. estende .-> pesquisar
    historico -. incluído quando autenticado .-> pesquisar
```

## 2. Diagrama de sequência — busca unificada

```mermaid
sequenceDiagram
    actor Pessoa
    participant Frontend
    participant API as API FastAPI
    participant Search as SearchService
    participant OA as OpenAlexConnector
    participant Core as CoreConnector
    participant BDTD as BdtdConnector
    participant Local as OaiLocalConnector
    participant DB as PostgreSQL

    Pessoa->>Frontend: informa consulta, campo e filtros
    Frontend->>API: GET /api/v1/search
    API->>API: valida parâmetros e token opcional
    API->>Search: search(SourceQuery)
    par consultas externas e local
        Search->>OA: search(query)
        OA-->>Search: SourcePage ou falha controlada
    and
        Search->>Core: search(query)
        Core-->>Search: SourcePage ou falha controlada
    and
        Search->>BDTD: search(query)
        BDTD-->>Search: SourcePage ou falha controlada
    and
        Search->>Local: search(query)
        Local->>DB: busca textual em oai_records
        DB-->>Local: registros locais
        Local-->>Search: SourcePage
    end
    Search->>Search: normaliza, intercala e deduplica
    Search->>Search: ordena e recorta a página
    alt ao menos uma fonte respondeu
        Search-->>API: resultados e estado das fontes
        opt usuário autenticado
            API-)DB: registra histórico
        end
        API-->>Frontend: 200 JSON
        Frontend-->>Pessoa: resultados e avisos parciais
    else todas as fontes falharam
        Search-->>API: falha agregada
        API-->>Frontend: 502 e estado das fontes
        Frontend-->>Pessoa: mensagem de indisponibilidade
    end
```

## 3. Diagrama de sequência — autenticação e favorito

```mermaid
sequenceDiagram
    actor Pessoa
    participant Frontend
    participant API as API FastAPI
    participant Auth as AuthService
    participant Fav as FavoriteService
    participant DB as PostgreSQL

    Pessoa->>Frontend: envia e-mail e senha
    Frontend->>API: POST /api/v1/auth/login
    API->>Auth: authenticate(credentials, ip_hash)
    Auth->>DB: consulta usuário pelo e-mail
    DB-->>Auth: usuário e hash Argon2id
    Auth->>Auth: verifica senha e situação da conta
    Auth->>DB: registra evento de segurança
    Auth-->>API: usuário autenticado
    API-->>Frontend: token JWT
    Frontend-->>Pessoa: sessão iniciada

    Pessoa->>Frontend: seleciona Salvar favorito
    Frontend->>API: POST /api/v1/favorites com Bearer JWT
    API->>API: valida JWT e consentimento
    API->>Fav: add(user_id, record)
    Fav->>DB: procura duplicata por usuário e record_id
    alt favorito ainda não existe
        Fav->>DB: grava snapshot do registro
        DB-->>Fav: favorito criado
        Fav-->>API: FavoriteOut
        API-->>Frontend: 201 JSON
    else favorito já existe
        Fav-->>API: conflito
        API-->>Frontend: 409 JSON
    end
    Frontend-->>Pessoa: confirma resultado da operação
```

## 4. Diagrama entidade-relacionamento

```mermaid
erDiagram
    USERS ||--o{ FAVORITES : possui
    USERS ||--o{ SEARCH_HISTORY : realiza

    USERS {
        uuid id PK
        text email UK
        text full_name
        text password_hash
        timestamptz consent_at
        text consent_policy_version
        timestamptz created_at
        timestamptz updated_at
        timestamptz last_login_at
        boolean is_active
    }

    FAVORITES {
        uuid id PK
        uuid user_id FK
        text record_id
        jsonb record_snapshot
        text note
        timestamptz created_at
    }

    SEARCH_HISTORY {
        uuid id PK
        uuid user_id FK
        varchar query
        jsonb filters
        integer result_count_estimated
        timestamptz created_at
    }

    OAI_RECORDS {
        uuid id PK
        text source
        text oai_identifier
        timestamptz datestamp
        boolean deleted
        text title
        jsonb authors
        text abstract
        integer year
        text doi
        text url
        text pdf_url
        text type
        text language
        jsonb keywords
        jsonb raw_types
        tsvector search_vector
        tsvector author_vector
        timestamptz harvested_at
    }

    HARVEST_RUNS {
        uuid id PK
        text source
        timestamptz started_at
        timestamptz finished_at
        text status
        integer records_read
        integer records_upserted
        integer records_deleted
        text last_resumption_token
        text error_message
    }

    SECURITY_EVENTS {
        uuid id PK
        uuid user_id
        text event_type
        text ip_hash
        jsonb details
        timestamptz created_at
    }
```

Notas: `FAVORITES` possui unicidade composta em `user_id + record_id`; `OAI_RECORDS`, em
`source + oai_identifier`. `SECURITY_EVENTS.user_id` não é chave estrangeira, pois o registro de
segurança deve sobreviver à exclusão da conta. `OAI_RECORDS` e `HARVEST_RUNS` não pertencem a uma
conta de usuário.

## 5. Diagrama de classes

```mermaid
classDiagram
    direction LR

    class Connector {
        <<interface>>
        +slug: str
        +name: str
        +kind: str
        +is_enabled: bool
        +availability() SourceStatus
        +search(SourceQuery) SourcePage
    }

    class SearchService {
        -connectors: list~Connector~
        -source_timeout: float
        +search(SearchParams, user_id) SearchResponse
        -run_source(Connector, SourceQuery) SourcePage
        -merge_pages(list~SourcePage~) list~RecordOut~
    }

    class OpenAlexConnector {
        +search(SourceQuery) SourcePage
    }
    class CoreConnector {
        +search(SourceQuery) SourcePage
    }
    class BdtdConnector {
        +search(SourceQuery) SourcePage
    }
    class OaiLocalConnector {
        -source_slug: str
        +search(SourceQuery) SourcePage
    }

    class SourceQuery {
        +q: str
        +field: str
        +year_from: int
        +year_to: int
        +types: list
        +page: int
        +page_size: int
        +sort: str
    }

    class SourcePage {
        +records: list~RecordOut~
        +total: int
        +status: SourceStatus
        +message: str
        +duration_ms: int
    }

    class RecordOut {
        +id: str
        +title: str
        +authors: list~AuthorOut~
        +abstract: str
        +year: int
        +doi: str
        +url: str
        +pdf_url: str
        +type: RecordType
        +language: str
        +keywords: list~str~
        +sources: list~SourceRef~
    }

    class OaiClient {
        -base_url: str
        +identify() dict
        +list_sets() list
        +list_records(prefix, token, from) page
    }

    class OaiSourceConfig {
        +slug: str
        +name: str
        +base_url: str
        +metadata_prefix: str
        +set_spec: str
        +enabled: bool
        +default_type: str
        +type_map: dict
    }

    class HarvestSummary {
        +source: str
        +status: str
        +records_read: int
        +records_upserted: int
        +records_deleted: int
    }

    Connector <|.. OpenAlexConnector
    Connector <|.. CoreConnector
    Connector <|.. BdtdConnector
    Connector <|.. OaiLocalConnector
    SearchService o-- Connector
    SearchService ..> SourceQuery
    SearchService ..> SourcePage
    SourcePage *-- RecordOut
    OaiLocalConnector ..> OaiRecord : consulta
    OaiClient --> OaiSourceConfig
    OaiClient ..> HarvestSummary
    OaiClient ..> OaiRecord : origina
```

