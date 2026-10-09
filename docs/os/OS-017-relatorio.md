# Relatório da OS-017 — Favoritos

**Data:** 2026-10-09

## O que foi feito
- `app/schemas/favorite.py`, `app/services/favorite_service.py` (`add`, `list_favorites`, `update_note`, `remove`, `favorite_ids_for`) e `app/api/v1/favorites.py`: `POST /favorites` (201; 200 se já existir), `GET /favorites?page&page_size&q`, `PATCH /favorites/{id}`, `DELETE /favorites/{id}` (204).
- Controle de acesso por objeto (404 para favorito de outro usuário), retrato de até 20 KB, anotação de até 1.000 caracteres, limite de 2.000 por usuário.
- `docs/CONFORMIDADE_TCC.md` iniciado com a divergência das tags; A5 em `docs/SEGURANCA.md`.
- 16 testes de integração.

## Decisões tomadas
Em `docs/DECISOES.md`: limites, anotação em branco = `null`, `ILIKE` escapado na busca dos favoritos, tags não implementadas. Conflito de criação simultânea tratado com `SAVEPOINT` + consulta ao existente.

## Desvios em relação à OS
Nenhum. A rota `GET /favorites/export` (OS-019) deverá ser declarada **antes** de `/favorites/{id}`.

## Comandos executados e resultados
`python tasks.py check` verde.

## Critérios de aceite
- [x] Criar o mesmo favorito duas vezes não duplica — `test_creating_the_same_favorite_twice_does_not_duplicate`
- [x] Usuário B recebe 404 ao ler/alterar/apagar favorito do usuário A — `test_user_b_gets_404_for_user_a_favorite`
- [x] Sem token → 401 — `test_without_token_is_401`
- [x] `note` acima de 1000 caracteres → 422 — `test_note_validation`
- [x] `record` com `url` inválida → 422 — `test_record_with_invalid_url_is_422`
- [x] A busca (OS-016) marca `is_favorite=true` para itens salvos — `test_search_marks_saved_items_as_favorite`
- [x] Limite de 2.000 — `test_limit_of_2000_favorites`

## Evidência para o TCC
Controle de acesso por objeto descrito em `docs/SEGURANCA.md` (A5); divergência das tags em `docs/CONFORMIDADE_TCC.md`.
