# LGPD: dados tratados e direitos do titular

> Documento vivo. A OS-029 acrescenta os eventos de segurança (o que é registrado e por quanto
> tempo). Base legal: **consentimento** (LGPD, art. 7º, I), registrado no cadastro com a data e a
> versão da política aceita.

## Dados tratados e minimização (art. 6º, III)

| Dado | Para que serve | Onde fica | Retenção |
|---|---|---|---|
| Nome e e-mail | identificar a conta e entrar | `users` | até a exclusão da conta |
| Hash da senha (Argon2id) | autenticar | `users.password_hash` (nunca sai da API) | até a exclusão da conta |
| Data e versão do consentimento | prova do aceite (art. 8º) | `users` | até a exclusão da conta |
| Favoritos e anotações | função "salvar trabalhos" | `favorites` | até a exclusão da conta ou do favorito |
| Histórico de buscas | função "histórico" | `search_history` | 200 mais recentes por usuário |
| Eventos de segurança (IP só em *hash*) | segurança e auditoria (art. 46) | `security_events` | período limitado definido pelo projeto (OS-029) |

Não há telefone, CPF, data de nascimento, *cookies* de rastreamento nem *analytics*. O texto da
busca é enviado às fontes consultadas ao vivo (OpenAlex e CORE), o que consta na política de
privacidade (`app/content/privacy_pt.md`, servida em `GET /api/v1/privacy`).

## Mapa dos direitos do art. 18 → rota → teste

| Direito (LGPD art. 18) | Rota | Teste |
|---|---|---|
| I, II. Confirmação e **acesso** aos dados | `GET /api/v1/me` | `test_get_me_returns_account_data` |
| II, V. Acesso completo e **portabilidade** (arquivo JSON com conta, favoritos e histórico) | `GET /api/v1/me/data-export` | `test_data_export_has_all_own_data_and_nothing_from_others` |
| III. **Correção** de dados incompletos, inexatos ou desatualizados | `PATCH /api/v1/me` (nome e e-mail), `POST /api/v1/me/password` | `test_patch_*`, `test_change_password` |
| IV, VI. **Eliminação** dos dados tratados com consentimento | `DELETE /api/v1/me` (exige a senha); `DELETE /api/v1/history[/{id}]`; `DELETE /api/v1/favorites/{id}` | `test_delete_account_removes_everything_keeps_event_without_personal_data` |
| VIII, IX. Informação sobre o consentimento e sua **revogação** | `GET /api/v1/privacy`; `POST /api/v1/me/consent` (novo aceite); excluir a conta revoga | `test_policy_version_change_requires_new_consent`, `test_privacy_policy_is_public` |

### Detalhes de implementação

- **Exclusão:** apaga o usuário, os favoritos e o histórico (`ON DELETE CASCADE`). Fica um evento de
  segurança `account_deleted` **sem e-mail e sem identificador do usuário** (`user_id` nulo).
- **Troca de e-mail:** exige a senha atual; se o e-mail já estiver em uso, a resposta é a mesma
  mensagem genérica (409), para não revelar quem tem conta.
- **Nova versão da política:** se `PRIVACY_POLICY_VERSION` mudar, o login devolve
  `consent_required: true` e o novo aceite é registrado em `POST /api/v1/me/consent`.
- **Pendência do desenvolvedor:** preencher o contato do responsável (`{CONTATO_DO_RESPONSAVEL}`)
  em `app/content/privacy_pt.md` antes de publicar.

## Eventos de segurança (OS-029)

- **O que é registrado** (tabela `security_events`): apenas o **tipo** do evento (`account_registered`,
  `login_success`, `login_failed`, `rate_limited`, `password_changed`, `data_exported`,
  `account_deleted`), a data e um **hash** do IP (HMAC-SHA256 com sal derivado de `SECRET_KEY`).
  Alguns eventos trazem `details` técnicos sem dado pessoal (ex.: o caminho da rota no
  `rate_limited`). O identificador do usuário fica nos eventos da conta, **exceto** em
  `account_deleted`, que é gravado sem ele.
- **O que nunca é registrado:** e-mail, nome, senha, token, User-Agent nem o IP em claro. A função
  única `record_event` **recusa** detalhes com essas chaves (mesmo aninhadas) e com valores que
  pareçam e-mail ou IP.
- **Por que:** segurança e auditoria (LGPD art. 46; OWASP A10), com o mínimo de dados (art. 6º, III).
- **Retenção:** período limitado definido **pelo projeto** (180 dias, escolha de projeto, não
  exigência legal). O comando `python -m app.cli_security purge --older-than-days N` apaga o que for
  mais antigo; o administrador deve rodá-lo periodicamente (por exemplo, no `cron`).
- **Consulta:** `python -m app.cli_security events [--type X] [--since AAAA-MM-DD] [--limit N]`, só
  por linha de comando (não há painel nem rota de administração).

## Histórico de buscas (OS-018)

- **Quem tem histórico:** somente usuários com conta. Buscas de visitantes **não são gravadas**.
- **O que é gravado:** o texto da busca (até 200 caracteres), os filtros (fontes, anos, tipos,
  ordenação), o total estimado de resultados e a data. Nada além disso.
- **Retenção limitada:** as **200 buscas mais recentes** por usuário; ao gravar a 201ª, a mais
  antiga é apagada.
- **Sem repetição:** repetir a mesma consulta com os mesmos filtros em sequência imediata não gera
  novo item (trocar de página também não).
- **Eliminação pelo titular:** `DELETE /api/v1/history/{id}` (um item) e `DELETE /api/v1/history`
  (tudo); excluir a conta apaga o histórico em cascata.
- **Acesso:** cada usuário só enxerga o próprio histórico (`GET /api/v1/history`).
- **Efeito sobre a busca:** a gravação ocorre depois da resposta e, se falhar, a busca não é afetada.
