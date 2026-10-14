# API do Academic Search Hub

Visão humana da API REST, alinhada ao OpenAPI que a própria aplicação publica. A fonte da verdade é
o OpenAPI (`/api/openapi.json`, com a interface Swagger em `/api/docs` quando `DOCS_ENABLED=true`);
`scripts/check_api_docs.py` confere que toda rota do OpenAPI aparece neste documento.

- Base: `/api/v1`. Corpo e respostas em JSON (UTF-8), exceto as exportações (arquivo para download).
- Sem estado: cada requisição leva o que precisa (token no cabeçalho). Não há sessão no servidor.
- Toda resposta traz `X-Request-ID`, um UUID da requisição (também nos logs), útil para suporte.

## Autenticação

Cadastro e login devolvem um token JWT (HS256). Rotas marcadas com **token** exigem:

```
Authorization: Bearer <access_token>
```

- `POST /api/v1/auth/login` devolve `access_token`, `token_type` (`bearer`), `expires_in` (segundos) e
  `consent_required` (verdadeiro quando há uma versão nova da Política de Privacidade a aceitar).
- Token ausente, inválido ou expirado: `401`. O token expira em `ACCESS_TOKEN_EXPIRE_MINUTES`.
- `GET /api/v1/search` aceita visitante (sem token); com token, marca favoritos e grava o histórico.
- Senhas: 10 a 128 caracteres, ao menos uma letra e um número, sem conter o e-mail. Guardadas com
  Argon2id.

## Formato de erro

Todo erro tem o mesmo corpo:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Parâmetros de busca inválidos.",
    "details": [{ "field": "q", "issue": "a consulta deve ter de 2 a 200 caracteres" }]
  }
}
```

`details` só aparece quando há campos a apontar. Códigos (`error.code`):

| Código | Status | Quando |
|---|---|---|
| `validation_error` | 422 | Parâmetro ou corpo inválido |
| `unauthorized` | 401 | Sem token, token inválido, credencial errada |
| `forbidden` | 403 | Senha atual incorreta ao trocar senha, alterar e-mail ou excluir a conta |
| `not_found` | 404 | Favorito ou item de histórico que não existe (ou que é de outra pessoa) |
| `conflict` | 409 | E-mail já cadastrado (mensagem genérica) ou limite de favoritos atingido |
| `rate_limited` | 429 | Limite de requisições; vem com o cabeçalho `Retry-After` |
| `upstream_error` | 502 | Todas as fontes da busca falharam (veja `sources_status`) |
| `app_error` | 500 | Erro interno, sem detalhes |

## Limites

| O quê | Limite |
|---|---|
| Busca (`GET /search`), por IP | `RATE_LIMIT_SEARCH` (padrão `60/minute`) |
| Cadastro e login, por IP | `RATE_LIMIT_AUTH` (padrão `5/minute`) |
| Tamanho da página | padrão `DEFAULT_PAGE_SIZE` (20); máximo `MAX_PAGE_SIZE` (50) na busca |
| Exportar resultados (`POST /export`) | até 100 registros |
| Favoritos por pessoa | 2000 |
| Histórico | guarda e lista até 200 buscas |
| Anotação de favorito | até 1000 caracteres |

O limite de requisições é mantido em memória e vale para um único processo do servidor.

## Rotas

Resumo (auth = precisa de token):

| Método e caminho | Auth | Sucesso | O que faz |
|---|---|---|---|
| `GET /api/v1/health` | não | 200 | Saúde da API e do banco |
| `POST /api/v1/auth/register` | não | 201 | Cria conta (com consentimento) |
| `POST /api/v1/auth/login` | não | 200 | Entra e recebe o token |
| `GET /api/v1/auth/me` | sim | 200 | Dados da conta autenticada |
| `GET /api/v1/search` | opcional | 200 | Busca unificada nas fontes ativas |
| `GET /api/v1/sources` | não | 200 | Lista as fontes e se estão disponíveis |
| `GET /api/v1/favorites/export` | sim | 200 | Exporta todos os favoritos |
| `POST /api/v1/export` | não | 200 | Exporta registros de uma busca |
| `POST /api/v1/favorites` | sim | 201 ou 200 | Salva um trabalho (idempotente) |
| `GET /api/v1/favorites` | sim | 200 | Lista favoritos (paginado, com busca) |
| `PATCH /api/v1/favorites/{favorite_id}` | sim | 200 | Atualiza a anotação |
| `DELETE /api/v1/favorites/{favorite_id}` | sim | 204 | Remove um favorito |
| `GET /api/v1/history` | sim | 200 | Lista o histórico de buscas |
| `DELETE /api/v1/history` | sim | 204 | Limpa todo o histórico |
| `DELETE /api/v1/history/{history_id}` | sim | 204 | Remove um item do histórico |
| `GET /api/v1/me` | sim | 200 | Acesso: dados da conta (LGPD) |
| `PATCH /api/v1/me` | sim | 200 | Correção: nome e/ou e-mail |
| `DELETE /api/v1/me` | sim | 204 | Eliminação da conta e dos dados |
| `POST /api/v1/me/password` | sim | 204 | Troca a senha |
| `GET /api/v1/me/data-export` | sim | 200 | Portabilidade: baixa tudo em JSON |
| `POST /api/v1/me/consent` | sim | 200 | Registra o aceite da política atual |
| `GET /api/v1/privacy` | não | 200 | Texto da Política de Privacidade |

Em todas, `422` (parâmetro inválido), `429` (limite) e `500` (erro interno) também podem ocorrer.
Nos exemplos abaixo, `BASE` é o endereço do servidor (por exemplo `http://127.0.0.1:8000`) e `TOKEN`
é o `access_token` do login.

### `GET /api/v1/health`

```
curl BASE/api/v1/health
```

```json
{ "status": "ok", "database": "ok", "version": "0.1.0" }
```

Responde `200` mesmo com o banco fora do ar (`"database": "error"`), sem expor o motivo.

### `POST /api/v1/auth/register`

Corpo: `full_name` (2 a 120), `email`, `password`, `accept_privacy_policy` (deve ser `true`).
Resposta `201` com `UserOut` (`id`, `full_name`, `email`, `created_at`, `consent_at`,
`consent_policy_version`). E-mail repetido: `409` com mensagem genérica, que não revela se o e-mail
existe.

```
curl -X POST BASE/api/v1/auth/register -H "Content-Type: application/json" \
  -d '{"full_name":"Maria de Souza","email":"maria@exemplo.com","password":"Senha12345","accept_privacy_policy":true}'
```

```js
const resp = await fetch("/api/v1/auth/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ full_name: "Maria de Souza", email: "maria@exemplo.com",
                         password: "Senha12345", accept_privacy_policy: true }),
});
```

### `POST /api/v1/auth/login`

Corpo: `email`, `password`. Resposta `200` com `TokenOut`. Credencial inválida: `401` com mensagem
única ("E-mail ou senha inválidos.") e tempo de resposta semelhante, haja ou não a conta.

```
curl -X POST BASE/api/v1/auth/login -H "Content-Type: application/json" \
  -d '{"email":"maria@exemplo.com","password":"Senha12345"}'
```

```js
const { access_token } = await (await fetch("/api/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "maria@exemplo.com", password: "Senha12345" }),
})).json();
```

### `GET /api/v1/auth/me`

Token. Devolve `UserOut`. Equivale a `GET /api/v1/me`.

```
curl BASE/api/v1/auth/me -H "Authorization: Bearer TOKEN"
```

### `GET /api/v1/search`

Parâmetros de consulta:

| Parâmetro | Obrigatório | Descrição |
|---|---|---|
| `q` | sim | Termos (2 a 200 caracteres). Aspas para expressão exata e `-termo` para excluir valem nas fontes locais |
| `sources` | não | Fontes separadas por vírgula (padrão: todas as ativas) |
| `year_from`, `year_to` | não | Intervalo de anos (1900 até o ano atual + 1) |
| `type` | não | Tipos separados por vírgula: `article`, `thesis`, `preprint`, `book`, `other` |
| `page` | não | Página, a partir de 1 |
| `page_size` | não | Itens por página (padrão e máximo vêm da configuração) |
| `sort` | não | `relevance` (padrão) ou `year_desc` |

Resposta `200` (`SearchResponse`): `query`, `page`, `page_size`, `total_estimated`,
`total_is_estimate`, `results` (lista de registros) e `sources_status`, um objeto por fonte com
`status` (`ok`, `timeout`, `error`, `disabled`, `rate_limited`), `count`, `total`, `message` e
`duration_ms` (esta, **só com `APP_ENV=development`**; em produção o campo não é enviado).
**Falha parcial:** se algumas fontes falham, a resposta continua `200` com os
resultados das outras e o `status` de cada fonte. Só quando **todas** falham a resposta é `502`.

O total é uma **estimativa**: soma o que cada fonte informa e pode incluir duplicatas.

Cada registro (`RecordOut`): `id` (`doi:<doi>` ou `src:<fonte>:<id>`), `title`, `authors`
(`name`, `orcid`), `abstract`, `year`, `doi`, `url`, `pdf_url`, `type`, `language`, `keywords`,
`sources` (de quais fontes veio) e `is_favorite` (só com token).

```
curl "BASE/api/v1/search?q=letramento+digital&year_from=2018&type=article,thesis&page=1"
```

```js
const params = new URLSearchParams({ q: "letramento digital", year_from: "2018", type: "article" });
const data = await (await fetch(`/api/v1/search?${params}`)).json();
```

### `GET /api/v1/sources`

Lista as fontes: `slug`, `name`, `kind` (`api` ou `oai`), `enabled`, `status` (`ok` ou `disabled`) e
`message`. Não expõe endereços internos, chaves nem contagens.

```
curl BASE/api/v1/sources
```

### `POST /api/v1/export`

Sem login. Corpo: `format` (`bibtex`, `ris`, `json` ou `csv`) e `records` (até 100 registros, no
formato de `RecordOut`). Devolve o arquivo (`Content-Disposition: attachment;
filename="exportacao-AAAAMMDD.<ext>"`). Mais de 100 registros: `422`.

```
curl -X POST BASE/api/v1/export -H "Content-Type: application/json" -o saida.bib \
  -d '{"format":"bibtex","records":[{"id":"doi:10.1234/x","title":"Um trabalho"}]}'
```

### `GET /api/v1/favorites/export`

Token. Parâmetro obrigatório `format` (mesmos quatro formatos). Exporta todos os favoritos.

```
curl "BASE/api/v1/favorites/export?format=ris" -H "Authorization: Bearer TOKEN" -o favoritos.ris
```

### `POST /api/v1/favorites`

Token. Corpo: `record` (`RecordOut`) e `note` opcional (até 1000 caracteres). `201` se criou, `200` se
o trabalho já estava salvo (idempotente), `409` ao atingir o limite de 2000 favoritos.

```
curl -X POST BASE/api/v1/favorites -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"record":{"id":"doi:10.1234/x","title":"Um trabalho"},"note":"ler depois"}'
```

### `GET /api/v1/favorites`

Token. Parâmetros: `page`, `page_size` e `q` (texto no título ou na anotação). Resposta `200` com
`items` (cada um: `id`, `record`, `note`, `created_at`), `page`, `page_size` e `total`.

```
curl "BASE/api/v1/favorites?q=letramento" -H "Authorization: Bearer TOKEN"
```

### `PATCH /api/v1/favorites/{favorite_id}`

Token. Corpo: `note` (texto ou `null` para apagar). `200` com o favorito; `404` se não existir.

```
curl -X PATCH BASE/api/v1/favorites/ID -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" -d '{"note":"capítulo 3"}'
```

### `DELETE /api/v1/favorites/{favorite_id}`

Token. `204` sem corpo; `404` se não existir.

```
curl -X DELETE BASE/api/v1/favorites/ID -H "Authorization: Bearer TOKEN"
```

### `GET /api/v1/history`

Token. Parâmetros `page` e `page_size`. Lista as últimas buscas (até 200), da mais recente à mais
antiga: `id`, `query`, `filters`, `result_count_estimated`, `created_at`.

```
curl BASE/api/v1/history -H "Authorization: Bearer TOKEN"
```

### `DELETE /api/v1/history`

Token. Apaga todo o histórico. `204`.

```
curl -X DELETE BASE/api/v1/history -H "Authorization: Bearer TOKEN"
```

### `DELETE /api/v1/history/{history_id}`

Token. Remove um item. `204`; `404` se não existir.

```
curl -X DELETE BASE/api/v1/history/ID -H "Authorization: Bearer TOKEN"
```

### `GET /api/v1/me`

Token. Direito de **acesso** (LGPD, art. 18): devolve `UserOut`.

```
curl BASE/api/v1/me -H "Authorization: Bearer TOKEN"
```

### `PATCH /api/v1/me`

Token. Direito de **correção**. Corpo: `full_name` e/ou `email`; mudar o e-mail exige
`current_password`. `200` com `UserOut`; `403` senha incorreta; `409` e-mail já usado.

```
curl -X PATCH BASE/api/v1/me -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"full_name":"Maria S. Souza"}'
```

### `DELETE /api/v1/me`

Token. Direito de **eliminação**: apaga a conta, os favoritos e o histórico. Corpo: `password`.
`204`; `403` se a senha estiver incorreta. Não há como desfazer.

```
curl -X DELETE BASE/api/v1/me -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"password":"Senha12345"}'
```

### `POST /api/v1/me/password`

Token. Corpo: `current_password` e `new_password`. `204`; `403` senha atual incorreta.

```
curl -X POST BASE/api/v1/me/password -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" -d '{"current_password":"Senha12345","new_password":"OutraSenha678"}'
```

### `GET /api/v1/me/data-export`

Token. Direito de **acesso e portabilidade**: um JSON com a conta, os favoritos e o histórico
(`Content-Disposition: attachment`).

```
curl BASE/api/v1/me/data-export -H "Authorization: Bearer TOKEN" -o meus-dados.json
```

### `POST /api/v1/me/consent`

Token. Registra o aceite da versão atual da Política de Privacidade (usado quando o login informa
`consent_required`). `200` com `UserOut`.

```
curl -X POST BASE/api/v1/me/consent -H "Authorization: Bearer TOKEN"
```

### `GET /api/v1/privacy`

Público. Devolve `version` e `content` (a política, em Markdown).

```
curl BASE/api/v1/privacy
```

## Conformidade REST

Autoavaliação de cada rota, feita lendo o código e o OpenAPI (não é uma certificação). Critérios:
**(a)** o verbo HTTP corresponde à operação; **(b)** o caminho nomeia um substantivo no plural, não
um verbo; **(c)** o código de status é o adequado; **(d)** a resposta é sem estado. Rodríguez et al.
(2016) mostram que APIs declaradas REST muitas vezes não seguem os princípios, e Palma et al. (2017)
tratam de antipadrões na nomeação de recursos: esta tabela registra o que foi verificado neste
sistema, inclusive o que não atende.

Legenda: **Atende**; **Parcial** (atende com ressalva, escrita na observação); **Não atende**;
**N/A** (critério não se aplica).

| Rota | (a) verbo | (b) nome no plural | (c) status | (d) sem estado | Observação |
|---|---|---|---|---|---|
| `GET /api/v1/health` | Atende | N/A | Parcial | Atende | Recurso de monitoramento no singular, por convenção. Responde 200 mesmo com o banco fora (`database: error`), decisão da OS-014 para não expor o motivo; o usual seria 503 |
| `POST /api/v1/auth/register` | Atende | **Não atende** | Atende | Atende | `register` é verbo. Alternativa REST: `POST /users` (201) |
| `POST /api/v1/auth/login` | Atende | **Não atende** | Parcial | Atende | `login` é verbo; alternativa: `POST /sessions` ou `/tokens`. Responde 200 ao criar um token (o usual seria 201); 401 correto |
| `GET /api/v1/auth/me` | Atende | Parcial | Atende | Atende | `me` é recurso singleton, no singular. Duplica `GET /api/v1/me` |
| `GET /api/v1/search` | Atende | Parcial | Atende | Atende | `search` é substantivo, mas singular e não coleção; alternativa: `GET /records?q=`. 502 quando todas as fontes falham é adequado; falha parcial é 200 com `sources_status` |
| `GET /api/v1/sources` | Atende | Atende | Atende | Atende | Coleção no plural |
| `GET /api/v1/favorites/export` | Atende | **Não atende** | Atende | Atende | `export` é verbo no caminho. Alternativa: `GET /favorites?format=csv` ou escolha pelo cabeçalho `Accept` |
| `POST /api/v1/export` | Parcial | **Não atende** | Parcial | Atende | `export` é verbo. Usa POST porque recebe até 100 registros no corpo e não cria recurso guardado (por isso 200, não 201). Alternativa: `POST /exports` |
| `POST /api/v1/favorites` | Atende | Atende | Atende | Atende | 201 ao criar, 200 se já existia (idempotente), 409 no limite |
| `GET /api/v1/favorites` | Atende | Atende | Atende | Atende | Coleção paginada, com filtro `q` |
| `PATCH /api/v1/favorites/{favorite_id}` | Atende | Atende | Atende | Atende | Atualização parcial; 404 se não existir |
| `DELETE /api/v1/favorites/{favorite_id}` | Atende | Atende | Atende | Atende | 204 sem corpo; 404 se não existir |
| `GET /api/v1/history` | Atende | Parcial | Atende | Atende | `history` é substantivo coletivo, não o plural de um recurso (seria `/searches`) |
| `DELETE /api/v1/history` | Atende | Parcial | Atende | Atende | Apagar a coleção inteira com DELETE é válido; mesma ressalva do nome |
| `DELETE /api/v1/history/{history_id}` | Atende | Parcial | Atende | Atende | Mesma ressalva do nome |
| `GET /api/v1/me` | Atende | Parcial | Atende | Atende | Recurso singleton (a conta de quem chama), no singular |
| `PATCH /api/v1/me` | Atende | Parcial | Parcial | Atende | 403 para senha atual incorreta; há quem prefira 401 ou 422 |
| `DELETE /api/v1/me` | Parcial | Parcial | Parcial | Atende | A senha vai no corpo de um DELETE, que alguns clientes e proxies descartam; 403 para senha incorreta |
| `POST /api/v1/me/password` | Parcial | Parcial | Atende | Atende | Trocar atributo seria `PUT` ou `PATCH` no sub-recurso; `password` é singular. 204 adequado |
| `GET /api/v1/me/data-export` | Atende | Parcial | Atende | Atende | `data-export` é um substantivo composto no singular |
| `POST /api/v1/me/consent` | Atende | Parcial | Atende | Atende | Cria o registro de aceite; singular. Devolve 200 com a conta, em vez de 201 |
| `GET /api/v1/privacy` | Atende | Parcial | Atende | Atende | Política vigente, no singular (singleton) |

### Resumo e correções

- **(a) Verbo HTTP:** 19 rotas atendem; 3 atendem parcialmente (`POST /export`, `DELETE /me` com corpo,
  `POST /me/password`). Nenhuma usa um verbo claramente errado.
- **(b) Nome no plural:** 4 rotas **não atendem** (`/auth/register`, `/auth/login`,
  `/favorites/export`, `/export`: o caminho tem um verbo). Doze atendem parcialmente por nomearem um
  recurso singleton ou um substantivo no singular; `/health` não se aplica. Cinco seguem o padrão por
  completo: `/sources` e as quatro rotas de `/favorites`.
- **(c) Status:** adequados na maior parte; ressalvas em `/health` (200 com banco fora), login (200
  em vez de 201) e no uso de 403 para senha incorreta.
- **(d) Sem estado:** todas atendem. A autenticação é por token em cada requisição; nada de sessão no
  servidor. O contador do limite de requisições fica em memória, mas não é estado da sessão do cliente.

**Correção feita:** nenhuma renomeação. Os caminhos e os status foram definidos pelas Ordens de
Serviço do projeto (OS-014 a OS-026) e o frontend, os testes e o texto do TCC dependem deles;
renomeá-los quebraria o contrato documentado. A divergência fica **registrada aqui, em
`docs/DECISOES.md` e na lista de divergências da OS-035**, para o autor decidir: manter e escrever
no TCC que a API segue REST nos verbos e no formato, mas **não** na nomeação de quatro rotas de
ação; ou renomear (por exemplo `/users`, `/sessions`, `/exports`), o que exigiria mudar frontend,
testes e documentos.
