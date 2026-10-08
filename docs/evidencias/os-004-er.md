# Modelo entidade-relacionamento (OS-004)

Gerado a partir dos modelos em `app/models/`. `security_events.user_id` **não** tem chave
estrangeira de propósito: os eventos sobrevivem à exclusão da conta. `oai_records` e `harvest_runs`
se relacionam com a fonte apenas pelo texto `source` (o slug de `config/oai_sources.yml`).

```mermaid
erDiagram
    users ||--o{ favorites : "ON DELETE CASCADE"
    users ||--o{ search_history : "ON DELETE CASCADE"
    users }o..o{ security_events : "user_id sem FK"

    users {
        uuid id PK
        text email UK "minúsculas (CHECK)"
        text full_name
        text password_hash
        timestamptz consent_at "NOT NULL"
        text consent_policy_version "NOT NULL"
        timestamptz created_at
        timestamptz updated_at
        timestamptz last_login_at
        bool is_active
    }
    favorites {
        uuid id PK
        uuid user_id FK
        text record_id "UK com user_id"
        jsonb record_snapshot
        text note "até 1000 caracteres"
        timestamptz created_at
    }
    search_history {
        uuid id PK
        uuid user_id FK
        varchar query "até 200"
        jsonb filters
        int result_count_estimated
        timestamptz created_at
    }
    security_events {
        uuid id PK
        uuid user_id "sem FK"
        text event_type "lista fechada (CHECK)"
        text ip_hash
        timestamptz created_at
        jsonb details
    }
    oai_records {
        uuid id PK
        text source "UK com oai_identifier"
        text oai_identifier
        timestamptz datestamp
        bool deleted
        text title
        jsonb authors
        text abstract
        int year
        text doi
        text url
        text pdf_url
        text type "article|thesis|preprint|book|other"
        text language
        jsonb keywords
        jsonb raw_types
        tsvector search_vector "gatilho; GIN; pesos A/B/C"
        timestamptz harvested_at
    }
    harvest_runs {
        uuid id PK
        text source
        timestamptz started_at
        timestamptz finished_at
        text status "running|ok|error|partial"
        int records_read
        int records_upserted
        int records_deleted
        text last_resumption_token
        text error_message
    }
```
