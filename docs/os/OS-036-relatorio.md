# OS-036 — Avaliação de usabilidade

## O que foi feito

- `docs/USABILIDADE.md`: avaliação heurística com as dez heurísticas de **Nielsen**, tabela de dez
  heurísticas para cada uma das seis telas (busca, resultados, filtros, favoritos e histórico,
  conta, política de privacidade), resumo de 13 problemas com severidade (1 a 3) e decisão,
  correções, limites e o roteiro opcional de teste com usuários (4 tarefas).
- Método registrado em `docs/DECISOES.md`: Nielsen. Não se aplicou Cybis et al. nem Prates e Barbosa,
  então o TCC não deve citá-los como método desta avaliação.

## Resultado

| Severidade | Problemas | Corrigidos | Mitigados | Abertos | Aceitos |
|---|---|---|---|---|---|
| 3 | 2 | 1 (P1) | 0 | 1 (P2) | 0 |
| 2 | 3 | 2 (P3, P4) | 1 (P5) | 0 | 0 |
| 1 | 8 | 0 | 0 | 0 | 8 |

Os de severidade 1 ficaram **aceitos com justificativa** (a OS permite corrigir ou justificar).

## Correções de interface (cada uma com teste)

- **P1, o mais grave:** quem entrava sem marcar "manter conectado" era deslogado ao abrir outra
  página, inclusive ao ser devolvido à busca depois de "Entre para salvar". Achado durante os fluxos
  de ponta a ponta da OS-032 e confirmado na inspeção. A caixa passa a vir marcada, e o cadastro
  também guarda a sessão na aba. **É uma divergência da OS-021**, registrada em `DECISOES.md`, com
  o jeito de reverter. Os três testes novos falham com o código antigo e passam com o novo.
- **P3:** menu e título "Favoritos" passam a "Favoritos e histórico" (teste de que o cabeçalho não
  transborda em 600, 640 e 768 px).
- **P4:** aviso "Alterações ainda não salvas." na anotação.
- **P5:** o cadastro avisa que não há recuperação de senha por e-mail.

## Aberto

- **P2 (severidade 3):** a política de privacidade mostra o marcador `{CONTATO_DO_RESPONSAVEL}`.
  Só o autor sabe o contato. Está em `docs/PENDENCIAS_DESENVOLVEDOR.md`.

## O que NÃO foi feito

- **Nenhum teste com usuários.** Não há participantes; o roteiro está pronto e os campos de registro
  estão em branco. Nenhum resultado foi inventado nem calculado.
- **A avaliação é de um só avaliador, a IA que construiu o sistema**, sem especialista em
  usabilidade. Está escrito em "Limites".
- As heurísticas de Nielsen foram resumidas de memória: o autor deve conferir a redação e as
  referências na fonte original.

## Verificação

Testes de interface das telas alteradas passam (autenticação e conta, favoritos, base da página).
A suíte completa é rodada antes do commit.
