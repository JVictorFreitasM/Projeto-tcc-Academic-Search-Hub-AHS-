# LGPD: dados tratados e direitos do titular

> Documento vivo. A OS-018 registra a retenção do histórico; a OS-020 acrescenta o mapa dos direitos
> do art. 18 → rotas → testes; a OS-029 acrescenta os eventos de segurança.

## Histórico de buscas (OS-018)

- **Quem tem histórico:** somente usuários com conta. Buscas de visitantes **não são gravadas**.
- **O que é gravado:** o texto da busca (até 200 caracteres), os filtros (fontes, anos, tipos,
  ordenação), o total estimado de resultados e a data. Nada além disso.
- **Retenção limitada:** as **200 buscas mais recentes** por usuário; ao gravar a 201ª, a mais
  antiga é apagada.
- **Sem repetição:** repetir a mesma consulta com os mesmos filtros em sequência imediata não gera
  novo item (trocar de página também não).
- **Eliminação pelo titular:** `DELETE /api/v1/history/{id}` (um item) e `DELETE /api/v1/history`
  (tudo); excluir a conta apaga o histórico em cascata (`ON DELETE CASCADE`).
- **Acesso:** cada usuário só enxerga o próprio histórico (`GET /api/v1/history`).
- **Efeito sobre a busca:** a gravação ocorre depois da resposta e, se falhar, a busca não é afetada.
