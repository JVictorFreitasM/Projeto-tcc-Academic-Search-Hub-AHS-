# Relatório da OS-029 — Registro de eventos de segurança

**Data:** 2026-10-13

## O que foi feito
- `app/services/security_events.py`: `record_event(session, event_type, user_id=None, request=None, details=None)` como **única** porta de gravação. Calcula o `ip_hash` a partir da requisição e **recusa** `details` com chaves proibidas (`email`, `password`, `token`, `name`, `ip`, `user_agent`; também aninhadas) ou valores que pareçam e-mail/IPv4. Também `list_events` e `purge_older_than`.
- `app/cli_security.py`: `python -m app.cli_security events [--type X] [--since AAAA-MM-DD] [--limit N]` (mostra só o início do hash) e `purge --older-than-days N` (padrão 180).
- Todas as rotas que geram eventos (cadastro, login, limite de requisições, troca de senha, exportação, exclusão) já usavam essa função desde as OS-015 e OS-020; a OS-009 (colheita) não grava eventos de segurança.
- `docs/LGPD.md` (o que é registrado e por quanto tempo) e 22 testes novos.

## Decisões tomadas
Em `docs/DECISOES.md`: retenção de 180 dias como escolha do projeto, validação também de valores, `client_ip_hash` movido para `app/core/security.py` (import circular).
O parâmetro `ip_hash` continua aceito (além de `request`) para camadas de serviço sem acesso à requisição.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde.

## Critérios de aceite
- [x] Registrar `details={"email": "..."}` falha — `tests/unit/test_security_events.py::test_personal_data_in_details_is_refused`
- [x] Os eventos da lista de 6.6 são gerados nas rotas correspondentes — `tests/integration/test_security_events.py::test_every_event_type_of_the_model_is_produced_by_a_route`
- [x] `purge` apaga só eventos antigos — `test_purge_deletes_only_old_events`, `test_cli_purge_default_and_custom_retention`
- [x] O IP nunca aparece em claro (teste varre o banco) — `test_database_never_contains_clear_ip_email_or_password`

## Evidência para o TCC
`docs/evidencias/os-029.txt`: saída do `events` e do `purge` com **eventos sintéticos** (o arquivo avisa).
