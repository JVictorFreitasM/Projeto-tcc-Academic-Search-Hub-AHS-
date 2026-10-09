# Relatório da OS-020 — Conta e direitos do titular (LGPD)

**Data:** 2026-10-09

## O que foi feito
- `app/api/v1/me.py`: `GET/PATCH/DELETE /me`, `POST /me/password`, `GET /me/data-export`, `POST /me/consent` e `GET /privacy` (público).
- `app/services/account_service.py` (correção, troca de senha, exportação, eliminação, consentimento) e novos esquemas em `app/schemas/user.py` (`MeUpdate`, `PasswordChange`, `AccountDelete`, `PrivacyPolicyOut`, `check_password_rules` compartilhada com o cadastro).
- `app/content/privacy_pt.md`: política em português claro, com o marcador `{CONTATO_DO_RESPONSAVEL}`.
- O login devolve `consent_required` quando a versão da política mudou.
- `docs/LGPD.md` com o mapa "direito do art. 18 → rota → teste". 13 testes de integração.

## Decisões tomadas
- Senha atual errada → 403 com `code=invalid_password` (não 401, que a interface trata como sessão expirada).
- Na exclusão, o evento `account_deleted` é gravado com `user_id` nulo: o identificador do titular é dado pessoal pseudonimizado e a eliminação vale para ele também.
- `DELETE /me` exige a senha no corpo da requisição.
- A política fala em "180 dias" para os eventos de segurança (padrão previsto na OS-029); se a OS-029 mudar o valor, atualizar o texto.
- `/auth/me` (OS-015) continua existindo; `/me` é o ponto oficial dos direitos do titular.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde.

## Critérios de aceite
- [x] Excluir a conta apaga usuário, favoritos e histórico (conta linhas antes e depois) — `test_delete_account_removes_everything_keeps_event_without_personal_data`
- [x] Exclusão exige senha correta — `test_delete_account_requires_the_right_password`
- [x] O JSON de `data-export` tem todos os dados do usuário e nenhum de outro — `test_data_export_has_all_own_data_and_nothing_from_others`
- [x] Após a exclusão, o token antigo falha (401) — `test_old_token_fails_after_deletion`
- [x] `security_events` mantém `account_deleted` sem e-mail — mesmo teste da exclusão
- [x] `PATCH /me` com e-mail repetido → 409 genérico — `test_patch_with_a_taken_email_gives_generic_409`
- [x] Mudança de versão da política — `test_policy_version_change_requires_new_consent`

## Evidência para o TCC
`docs/LGPD.md` e o texto da política (`app/content/privacy_pt.md`). **Pendente (desenvolvedor):** preencher o contato do responsável e revisar o texto antes de publicar.
