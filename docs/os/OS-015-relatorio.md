# Relatório da OS-015 — Cadastro e login (JWT, Argon2id)

**Data:** 2026-10-09

## O que foi feito
- `app/core/security.py`: `hash_password`, `verify_password`, `needs_rehash`, `dummy_password_hash`, `create_access_token`, `decode_access_token` (HS256 fixo; `sub`, `iat`, `exp`, `iss`, `jti`).
- `app/schemas/user.py`: `UserCreate` (nome 2–120, e-mail normalizado, senha 10–128 com letra e número e sem o e-mail, consentimento obrigatório), `LoginIn`, `UserOut`, `TokenOut`.
- `app/services/auth_service.py` (`register`, `authenticate`) e `app/services/security_events.py` (`record_event`, recusa chaves proibidas).
- `app/api/v1/auth.py`: `POST /auth/register` (201), `POST /auth/login`, `GET /auth/me`; `app/api/deps.py` com `get_current_user`/`get_optional_user`.
- `app/core/rate_limit.py`: limites configuráveis e tratador do 429 que grava o evento `rate_limited`.
- `docs/SEGURANCA.md` (A2, A3, A7 e A6) e 46 testes novos (24 unitários, 22 de integração).

## Decisões tomadas
Em `docs/DECISOES.md`: Argon2id com padrões da biblioteca, e-mail por regex, eventos que sobrevivem ao 401, limites lidos a cada requisição.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`ruff`, `mypy` e os testes da OS passam; `python tasks.py check` verde.

## Critérios de aceite
- [x] Cadastro sem aceitar a política → 422 — `test_register_without_accepting_policy_is_422`
- [x] E-mail repetido → 409 genérico; e-mail inexistente e senha errada → mesma mensagem e status — `test_duplicate_email_gives_generic_409`, `test_wrong_password_and_unknown_email_look_identical`
- [x] Token `alg=none` e token expirado → 401 — `test_me_requires_a_valid_token`, `test_security.py`
- [x] Sexto login errado no minuto → 429 e evento `rate_limited` — `test_sixth_login_in_a_minute_is_429_and_records_event`
- [x] `password_hash` nunca é devolvido — `test_register_returns_user_without_hash_and_stores_consent`

## Evidência para o TCC
Tabela parcial "controle → risco OWASP" (A2, A3, A7) em `docs/SEGURANCA.md`.
