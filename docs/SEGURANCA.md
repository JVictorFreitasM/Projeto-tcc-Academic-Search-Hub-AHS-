# Segurança (OWASP Top 10, 2017)

> Documento vivo. A OS-015 acrescenta A2, A3 e A7; a OS-027 consolida os dez riscos; a OS-028
> acrescenta os resultados da análise estática.

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

## Controles por risco (parcial; a OS-027 consolida os dez)

| Risco (2017) | Controle | Onde | Teste |
|---|---|---|---|
| A2 Autenticação quebrada | Senhas com **Argon2id** (padrões do `argon2-cffi`), com novo hash quando os parâmetros mudam | `app/core/security.py` | `tests/unit/test_security.py`, `test_rehash_on_login_when_parameters_are_weaker` |
| A2 | Mensagem e tempo semelhantes para e-mail inexistente e senha errada (verificação contra hash falso) | `app/services/auth_service.py` | `test_wrong_password_and_unknown_email_look_identical` |
| A2 | Cadastro com e-mail repetido devolve 409 genérico (não revela se o e-mail existe) | `auth_service.register` | `test_duplicate_email_gives_generic_409` |
| A2 | Limite de tentativas: `RATE_LIMIT_AUTH` (padrão 5/minuto por IP) em login e cadastro, com evento `rate_limited` | `app/core/rate_limit.py`, `app/api/v1/auth.py` | `test_sixth_login_in_a_minute_is_429_and_records_event` |
| A2 | JWT HS256 com algoritmo **fixo**, `exp`, `iss`, `iat`, `sub` e `jti` obrigatórios; recusa `alg=none`, expirado, adulterado, outro emissor e outra chave; sem `SECRET_KEY` não emite nem valida | `app/core/security.py` | `test_security.py`, `test_me_requires_a_valid_token` |
| A3 Exposição de dados sensíveis | `password_hash` nunca sai em respostas (`UserOut`); senha não aparece em log, resposta nem evento | `app/schemas/user.py`, filtro de log | `test_password_never_appears_in_logs_or_responses` |
| A3 | IP só em hash HMAC-SHA256 com sal derivado de `SECRET_KEY`; `security_events.details` sem e-mail, senha, token ou nome | `hash_ip`, `app/services/security_events.py` | `test_ip_is_never_stored_in_clear_and_events_have_no_email` |
| A7 XSS | `Content-Security-Policy` sem `unsafe-inline` na API e no frontend; o frontend (Fase 3) não usa `innerHTML` com dados externos | `app/core/security_headers.py` | `test_security_headers_on_every_response` |

### A5 Controle de acesso quebrado: favoritos (OS-017)

Todo acesso a favorito filtra por `user_id` **e** `id` (`app/services/favorite_service.py`,
`_get_owned`). Quando o favorito não existe **ou** pertence a outro usuário, a resposta é a mesma:
**404** (nunca 403), de modo que a API não revela se um id existe. Sem token, as quatro rotas
respondem 401. Limites contra abuso de armazenamento: retrato de até 20 KB, anotação de até 1.000
caracteres e 2.000 favoritos por usuário. Testes: `tests/integration/test_favorites.py`
(`test_user_b_gets_404_for_user_a_favorite`, `test_without_token_is_401`).

Os parâmetros do Argon2id são os **padrões da biblioteca** `argon2-cffi` (perfil de baixa memória da
RFC 9106), sem valores inventados; ver `docs/DECISOES.md`.

## Cabeçalhos de segurança (A6)

Presentes em todas as respostas (`app/core/security_headers.py`; teste
`tests/integration/test_app_base.py`): `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: no-referrer`, `Permissions-Policy` restritiva e `Content-Security-Policy`;
`Strict-Transport-Security` quando `APP_ENV=production`. A CORS aceita apenas as origens de
`ALLOWED_ORIGINS` (nunca `*` em produção).
