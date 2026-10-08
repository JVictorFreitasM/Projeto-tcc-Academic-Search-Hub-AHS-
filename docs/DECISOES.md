# Registro de decisões e divergências

Registro vivo. Uma linha por entrada, a mais recente no fim.

| Data | OS | Decisão | Motivo | Impacto |
|---|---|---|---|---|
| 2026-10-08 | OS-001 | Alvos de desenvolvimento em `tasks.py` em vez de `Makefile` | `make` não está instalado no Windows do desenvolvedor; a OS permite `tasks.py` | Comandos são `python tasks.py <alvo>` |
| 2026-10-08 | OS-001 | Gerenciador de dependências: `uv` (`uv.lock` + `requirements.lock` exportado) | Livre pela OS; `uv` já instalado | `requirements.lock` é gerado por `uv export` |
| 2026-10-08 | OS-001 | `PyYAML` não foi adicionado | Não consta na seção 4, mas a OS-005 precisa ler `oai_sources.yml` | Decidir com o desenvolvedor na OS-005 |
| 2026-10-08 | OS-002 | Em development, SECRET_KEY vazia é aceita; fora dele exige 32+ caracteres | A OS só exige o mínimo fora de development | Quem usar JWT em desenvolvimento deve definir a chave (a OS-015 deve recusar emitir token sem chave) |
