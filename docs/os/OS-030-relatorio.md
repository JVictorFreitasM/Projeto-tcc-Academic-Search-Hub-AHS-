# OS-030 — Consolidação da suíte, bloqueio de rede e cobertura medida

## O que foi feito

- `tests/conftest.py`: marcador automático por pasta (`unit`, `integration`, `contract`, `e2e`, `a11y`) e
  bloqueio de rede em toda a sessão (só loopback passa; o resto levanta `NetworkBlockedError`).
- `tasks.py`: alvos `test-unit`, `test-integration`, `test-contract`, `test-e2e`, `test-stats`; `test` com
  limiar de cobertura de 80%.
- `scripts/test_stats.py`: conta testes por marcador e resume a cobertura a partir do `coverage.xml`
  (grava `docs/evidencias/os-030-cobertura.txt`).
- Testes novos: `tests/unit/test_suite_guards.py` (marcadores, bloqueio de rede, `STRICT_FIXTURES`),
  `tests/unit/test_run_entrypoint.py`, `tests/contract/test_fixtures_contract.py`.
- `docs/TESTES.md`: como rodar, marcadores, banco de teste, fixtures sintéticas e o que é manual.

## Medições (executadas, não digitadas)

- `python tasks.py check` rodou duas vezes seguidas, ambas verdes: 1056 aprovados, 1 pulado.
- Cobertura de linhas de `app/`: 98,04% (3051 de 3112 linhas). Limiar de 80% ligado depois da medição.
- Testes por marcador (coleta): unit 704, integration 227, contract 8, e2e 118, a11y 0 (OS-031), total 1057.
- Evidência: `docs/evidencias/os-030-cobertura.txt`.

## Pendências

- Fixtures sintéticas continuam no lugar das respostas reais (passo manual das OS-007 a OS-010);
  `STRICT_FIXTURES=1` lista as que faltam.
- Validação com chaves reais e fontes OAI reais é do desenvolvedor.
