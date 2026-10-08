# Registro de decisões e divergências

Registro vivo. Uma linha por entrada, a mais recente no fim.

| Data | OS | Decisão | Motivo | Impacto |
|---|---|---|---|---|
| 2026-10-08 | OS-001 | Alvos de desenvolvimento em `tasks.py` em vez de `Makefile` | `make` não está instalado no Windows do desenvolvedor; a OS permite `tasks.py` | Comandos são `python tasks.py <alvo>` |
| 2026-10-08 | OS-001 | Gerenciador de dependências: `uv` (`uv.lock` + `requirements.lock` exportado) | Livre pela OS; `uv` já instalado | `requirements.lock` é gerado por `uv export` |
| 2026-10-08 | OS-001 | `PyYAML` não foi adicionado | Não consta na seção 4, mas a OS-005 precisa ler `oai_sources.yml` | Decidir com o desenvolvedor na OS-005 |
| 2026-10-08 | OS-002 | Em development, SECRET_KEY vazia é aceita; fora dele exige 32+ caracteres | A OS só exige o mínimo fora de development | Quem usar JWT em desenvolvimento deve definir a chave (a OS-015 deve recusar emitir token sem chave) |
| 2026-10-08 | OS-003 | Função immutable_unaccent e configuração pt_unaccent | unaccent() é STABLE e não pode ser usada em índice nem coluna gerada; o wrapper IMMUTABLE fixa o dicionário. pt_unaccent copia portuguese e põe unaccent antes do stemmer, para 'educacao' casar com 'Educação' | Todas as buscas locais usam pt_unaccent |
| 2026-10-08 | OS-003 | Ambiente local: PostgreSQL 18 próprio do projeto na porta 5433 (dados em C:\Users\Copperline\pgdata-tcc, fora do repositório), usuário pp_user | Não havia a senha do superusuário do PostgreSQL do sistema (porta 5432) e ele não foi alterado | O .env local aponta para a porta 5433; em outra máquina use a porta e as credenciais próprias |
| 2026-10-08 | OS-003 | downgrade da 0001 não remove as extensões | Criá-las pode exigir privilégio e outros objetos podem depender delas | downgrade base deixa unaccent, pg_trgm e pgcrypto instaladas |
| 2026-10-08 | OS-004 | search_vector mantido por gatilho, não por coluna gerada | Coluna gerada exige função imutável e não há função imutável para achatar o JSONB de palavras-chave sem criar coluna extra (proibida pela OS) | Gatilho 	rg_oai_records_search_vector; pesos A (título), B (palavras-chave), C (resumo) |
