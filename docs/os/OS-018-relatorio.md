# Relatório da OS-018 — Histórico de buscas

**Data:** 2026-10-09

## O que foi feito
- `app/services/history_service.py`: `record_search` (sem repetição imediata, máximo de 200 por usuário), `list_history`, `delete_one`, `clear_all`, `filters_of`.
- `app/api/v1/history.py`: `GET /history`, `DELETE /history/{id}`, `DELETE /history`; `app/schemas/history.py`.
- A rota de busca (OS-016) passa a gravar o histórico de usuários logados por `BackgroundTasks`, depois da resposta.
- `docs/LGPD.md` iniciado com a retenção do histórico. 12 testes de integração.

## Decisões tomadas
- "Mesma consulta" = mesmo texto e mesmos filtros (fontes e tipos sem ordem, anos, ordenação); a página não conta.
- Só se compara com a busca imediatamente anterior: A, B, A grava as três.
- A gravação usa sessão própria (a da requisição já terminou) e `search_history` guarda apenas texto, filtros, total estimado e data.
- Removemos o "gravador vazio" provisório da OS-016: o padrão agora é o real; os testes ainda podem trocar `app.state.history_recorder`.

## Desvios em relação à OS
Nenhum.

## Comandos executados e resultados
`python tasks.py check` verde.

## Critérios de aceite
- [x] Busca de visitante não grava nada — `test_visitor_search_records_nothing`
- [x] Busca repetida em sequência grava uma vez — `test_repeated_search_in_sequence_is_recorded_once`
- [x] A 201ª busca apaga a mais antiga — `test_the_201st_search_removes_the_oldest`
- [x] Usuário só vê o próprio histórico — `test_user_only_sees_own_history`, `test_delete_one_and_clear_all_only_touch_own_rows`
- [x] Erro ao gravar histórico não altera o status da busca — `test_history_failure_does_not_change_the_search_status`

## Evidência para o TCC
Texto sobre retenção limitada (200) e eliminação em `docs/LGPD.md`.
