# Segurança (OWASP Top 10, 2017)

> O TCC cita a lista de **2017** (A1 a A10). Se o autor trocar para a de 2021, esta página e a
> OS-027 precisam ser atualizadas juntas (registrar em `docs/DECISOES.md`).
>
> Este documento diz o que **foi verificado por teste**. Não afirma que o sistema é "100%
> seguro": nenhuma ferramenta ou conjunto de testes prova isso. A análise estática (OS-028) tem
> seção própria no fim.

## Tabela: risco → onde ocorre → controle → teste

| Risco (2017) | Onde pode ocorrer neste sistema | Controle implementado (arquivo) | Teste |
|---|---|---|---|
| **A1 Injeção** | Texto da busca (`q`, `sources`, `type`), filtros, favoritos (`q`, anotação), cadastro/login, busca local (`oai_records`), exportação CSV | Consultas com SQLAlchemy e parâmetros ligados; nenhum SQL montado com texto (`app/connectors/oai_local.py`, `app/services/*`); `websearch_to_tsquery` com o texto como parâmetro; `ILIKE` com `%`/`_` escapados (`favorite_service.py`); CSV neutraliza fórmulas (`export_service.py::csv_safe`) | `tests/unit/test_code_hygiene.py::test_a1_sql_is_never_built_from_dynamic_strings` (AST em todo `app/`); `tests/integration/test_security_owasp.py::test_a1_malicious_text_in_every_text_input_is_harmless`; `tests/integration/test_oai_local.py::test_malicious_text_causes_no_sql_error`; `tests/unit/test_export_service.py::test_csv_neutralizes_formula_injection` |
| **A2 Autenticação quebrada** | Cadastro, login, troca de senha, tokens | Argon2id (padrões da biblioteca); mensagem única e tempo semelhante no login; limite de tentativas (`RATE_LIMIT_AUTH`, 5/min por IP) com evento `rate_limited`; JWT HS256 com algoritmo fixo, `exp`, `iss`, `iat`, `sub`, `jti` obrigatórios; sem `SECRET_KEY` não emite nem valida (`app/core/security.py`, `app/services/auth_service.py`, `app/core/rate_limit.py`) | `tests/unit/test_security.py`; `tests/integration/test_auth.py` (`test_wrong_password_and_unknown_email_look_identical`, `test_sixth_login_in_a_minute_is_429_and_records_event`, `test_me_requires_a_valid_token`, `test_password_never_appears_in_logs_or_responses`) |
| **A3 Exposição de dados sensíveis** | Respostas da API, logs, eventos, repositório Git, transporte | `password_hash` nunca sai (`UserOut`); IP só como HMAC com sal de `SECRET_KEY` (`hash_ip`); logs mascaram `password`, `token`, `authorization`, `api_key`, `secret` e silenciam o logger do `httpx`; erros genéricos sem *stack trace*; HSTS em produção; `.env` fora do Git | `test_security_owasp.py::test_a3_*`; `tests/unit/test_logging.py`; `tests/unit/test_errors.py`; `tests/unit/test_code_hygiene.py::test_a3_*` (`.env` ignorado, `.env.example` sem valores, varredura de segredos nos arquivos versionados) |
| **A4 Entidades externas XML (XXE)** | Colheita OAI-PMH (único ponto que lê XML externo) | Todo XML por `defusedxml` com `forbid_dtd=True` (`app/harvest/oai_client.py`); nenhum `xml.etree`/`lxml`/`xml.dom`/`xml.sax` no código | `tests/unit/test_oai_client.py::test_dtd_and_external_entities_are_refused` (com `malicious_dtd.xml`); `tests/integration/test_harvester.py::test_xxe_response_marks_run_as_error`; `test_code_hygiene.py::test_a4_*` (importações proibidas) |
| **A5 Controle de acesso quebrado** | Favoritos, histórico, conta, exportação | Toda consulta filtra por `user_id`; outro usuário recebe **404** (não 403); rotas protegidas exigem token (`get_current_user`); a exclusão da conta invalida o token | `test_security_owasp.py::test_a5_every_protected_route_rejects_requests_without_token` e `test_a5_user_b_cannot_reach_user_a_objects_on_any_protected_route` (**percorrem todas as rotas com `bearerAuth` do OpenAPI**; uma rota nova com parâmetro de id falha o teste até ser coberta); `test_a5_listing_routes_never_leak_other_users_data`; `test_favorites.py::test_user_b_gets_404_for_user_a_favorite` |
| **A6 Configuração incorreta de segurança** | Cabeçalhos, CORS, documentação, depuração, mensagens de erro | CSP sem `unsafe-inline`, `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`; CORS só para `ALLOWED_ORIGINS` (nunca `*` em produção); `DOCS_ENABLED=false` desliga `/api/docs` e `/api/openapi.json`; sem `debug` nem `reload` no servidor (`app/main.py`, `app/core/security_headers.py`, `app/run.py`) | `tests/integration/test_app_base.py`; `test_security_owasp.py::test_a6_*`; `test_code_hygiene.py::test_a6_*` |
| **A7 Cross-site scripting (XSS)** | Títulos, resumos, autores, anotações e histórico exibidos no navegador; política de privacidade | Frontend só usa `textContent`/criação de elementos (nenhum `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`); links só `http`/`https`; conversor de Markdown próprio que nunca interpreta HTML; CSP sem `unsafe-inline`; HTML sem `<script>`, `style` nem `onclick` embutidos | `test_code_hygiene.py::test_a7_*` (varredura de todos os `.js` e `.html`); e2e: `test_search_page.py::test_malicious_title_is_shown_as_text_and_never_executed`, `test_favorites_ui.py::test_stored_xss_in_title_note_and_history_is_not_executed`, `test_auth_ui.py::test_privacy_page_renders_markdown_without_executing_html`; API: `test_security_owasp.py::test_a7_stored_xss_payloads_are_returned_inert_as_json` |
| **A8 Desserialização insegura** | Qualquer leitura de dados externos (YAML de fontes, JSON, respostas das fontes) | Sem `pickle`, `marshal`, `shelve`, `eval`, `exec`; YAML só com `yaml.safe_load`; JSON só por `json`/Pydantic | `test_code_hygiene.py::test_a8_*` (AST de todo `app/`) |
| **A9 Componentes com vulnerabilidades conhecidas** | Dependências Python | Versões travadas (`uv.lock`, `requirements.lock`); `pip-audit` na OS-028 | Seção "Análise estática" abaixo |
| **A10 Registro e monitoramento insuficientes** | Autenticação, limite de requisições, conta | Logs estruturados em JSON com `X-Request-ID`; tabela `security_events` (`login_failed`, `login_success`, `rate_limited`, `account_registered`, `password_changed`, `data_exported`, `account_deleted`), sem dados pessoais; consulta e retenção pela CLI (OS-029) | `test_security_owasp.py::test_a10_security_relevant_events_are_recorded`; `test_auth.py`; `test_me.py`; `tests/unit/test_logging.py` |

## Limitações conhecidas

### Limite de requisições em memória (OS-014)

O `slowapi` guarda os contadores **na memória do processo**. Com mais de um processo (`uvicorn
--workers N`, vários contêineres) cada processo conta separado e o limite por IP deixa de valer.
Por isso a aplicação deve ser executada com **um único processo** (`python -m app.run`). Redis está
fora do escopo do projeto. Atrás de proxy reverso, o IP do cliente vem do cabeçalho
`X-Forwarded-For`, aceito só de `127.0.0.1` (`forwarded_allow_ips` em `app/run.py`).

### CSP da página `/api/docs` (OS-014)

A política padrão (`default-src 'self'`, sem `unsafe-inline`) vale para a API e para o frontend. O
Swagger UI do FastAPI carrega os arquivos do CDN `cdn.jsdelivr.net` e tem um script embutido, então
**somente a página `/api/docs`** recebe uma política própria: o script embutido é liberado por
**hash SHA-256** (calculado na inicialização), o CDN é liberado e `style-src` aceita `unsafe-inline`
(o Swagger UI injeta estilos). Em produção, `DOCS_ENABLED=false` desliga `/api/docs` e
`/api/openapi.json`.

### Outras

- **JWT sem revogação individual:** o token vale até expirar (`ACCESS_TOKEN_EXPIRE_MINUTES`, padrão
  60). Excluir a conta o invalida (o usuário deixa de existir) e desativar a conta (`is_active`)
  também; não há lista de tokens revogados nem *refresh token* (fora do escopo).
- **Validação de e-mail sintática:** a posse do e-mail não é verificada (envio de e-mail está fora
  do escopo).
- **Rota opcional de busca:** `GET /api/v1/search` aceita visitantes; o OpenAPI a lista com
  `bearerAuth` porque o token é opcional (o teste A5 declara essa exceção explicitamente).
- O sistema depende de TLS fornecido pelo proxy reverso (OS-037); a aplicação em si fala HTTP.

## Controles detalhados

### A2/A3: autenticação e dados sensíveis (OS-015)

Os parâmetros do Argon2id são os **padrões da biblioteca** `argon2-cffi` (perfil de baixa memória
da RFC 9106), sem valores inventados; ver `docs/DECISOES.md`.

### A5: favoritos por objeto (OS-017)

Todo acesso a favorito filtra por `user_id` **e** `id` (`app/services/favorite_service.py`,
`_get_owned`). Quando o favorito não existe **ou** pertence a outro usuário, a resposta é a mesma:
**404** (nunca 403), de modo que a API não revela se um id existe. Sem token, as quatro rotas
respondem 401. Limites contra abuso de armazenamento: retrato de até 20 KB, anotação de até 1.000
caracteres e 2.000 favoritos por usuário.

### A6: cabeçalhos (OS-014)

Presentes em todas as respostas (`app/core/security_headers.py`): `X-Content-Type-Options:
nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy` restritiva
e `Content-Security-Policy`; `Strict-Transport-Security` quando `APP_ENV=production`.

## Correções feitas durante a OS-027

Nenhum defeito de código foi encontrado pelas varreduras e testes novos. Foram ajustados apenas os
próprios testes (critérios de falso positivo em varredura de segredos e de comentários). Defeitos
de segurança encontrados em OS anteriores, já corrigidos: vazamento da chave de API pelo logger do
`httpx` (OS-006) e mutação de objetos do conector em `is_favorite` (OS-012).

## Análise estática

Preenchida na OS-028.
