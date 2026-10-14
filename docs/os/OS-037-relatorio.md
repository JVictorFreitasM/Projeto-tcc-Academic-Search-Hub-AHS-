# OS-037 — Implantação, colheita agendada e backup

## O que foi feito

- `scripts/backup_db.sh`: `pg_dump` compactado, nome com data, 7 cópias, verificação com
  `pg_restore --list`, senha só por `PGPASSWORD`, sem arquivo parcial em caso de falha. 17 testes em
  `tests/unit/test_backup_script.py`, com `pg_dump` falso (16 rodam no Windows; o de permissões é
  só POSIX).
- `deploy/`: `academic-search.service` (systemd), `academic-search.env.example` (sem segredos),
  `nginx.conf.example`, `Caddyfile.example` e `crontab.example` (colheita diária, backup e purga
  semanal de eventos). 12 testes em `tests/unit/test_deploy_files.py` conferem a ausência de
  segredos e a coerência (um só processo, sem `add_header` de segurança, `ALLOWED_ORIGINS` sem `*`).
- `docs/IMPLANTACAO.md`: requisitos, usuário sem privilégios, instalação, variáveis em produção,
  serviço, proxy e HTTPS, colheita agendada, backup e restauração passo a passo, lista de verificação
  preenchida e atualização.
- `.gitattributes` (LF em `*.sh` e `deploy/*`) e a nota de LGPD sobre as cópias (`docs/LGPD.md`).

## Verificações reais feitas (14/10/2026, máquina de desenvolvimento, Windows)

1. **Backup e restauração de verdade**, com `pg_dump` e `pg_restore` do PostgreSQL 18: banco de
   origem com migrações e dados fictícios; cópia gerada pelo script (código 0); restauração num
   banco novo por um usuário **sem** privilégio de superusuário e **sem** pré-criar extensões.
   Linhas, MD5 do conteúdo de cada tabela e uma busca em português sem acento deram **iguais**; o
   gatilho do índice, a função `immutable_unaccent` e as extensões voltaram. Bancos de teste
   apagados no fim. `docs/evidencias/os-037/teste-restauracao.txt`.
2. **Aplicação em modo produção** (sem proxy): `health` 200; `/api/docs` e `/api/openapi.json` dão 404
   com `DOCS_ENABLED=false` e 200 com `true`; presentes `Strict-Transport-Security`,
   `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e
   `X-Request-ID`; `SECRET_KEY` vazia e `ALLOWED_ORIGINS=*` recusadas.
   `docs/evidencias/os-037/verificacao-local.txt`.

## Erros meus no caminho (corrigidos e registrados)

- **A primeira execução do teste de restauração foi inválida:** os dados fictícios não foram inseridos
  (aspas do JSON removidas pelo PowerShell no `psql -c`) e o roteiro comparou tabelas vazias, mas
  imprimiu "mesmos dados". Percebi ao ler o resultado, corrigi o roteiro (inserção por arquivo SQL,
  e recusa de continuar se alguma tabela estiver vazia) e refiz. O que está nas evidências é a
  versão corrigida.
- **Defeito real do `backup_db.sh`**, achado nessa execução real: o curinga tratava a barra invertida
  de um caminho do Windows como escape, a retenção nunca achava os arquivos e o script saía com erro
  **depois** de gerar a cópia (no cron, apareceria como falha). Corrigido e coberto por um teste com
  pasta de nome difícil.
- Um caso de `SECRET_KEY` vazia ficou em branco na primeira execução, porque no Windows
  `$env:X=''` apaga a variável e o `.env` do desenvolvedor assumiu; refiz sem ler o `.env`.

## O que NÃO foi feito (e por quê)

- **Serviço systemd, Nginx/Caddy, certificado e cron: não executados.** Não há servidor nem domínio.
  Estão como exemplos, e a lista de verificação marca esses itens como **PENDENTE**.
- **Colheita agendada rodando e `status` mostrando o resultado:** depende de fontes OAI validadas e
  habilitadas (`docs/FONTES_CANDIDATAS.md`).
- **O serviço sobe sozinho depois de reiniciar a máquina:** não testável aqui.
- **Restauração no servidor real:** a restauração verificada foi na máquina de desenvolvimento, com
  poucos dados. O procedimento precisa ser repetido no servidor.
- **Cópia dos backups para fora da máquina:** não automatizada.

## Divergência da OS

A OS pede que o Nginx "sirva o frontend". O exemplo encaminha tudo para a aplicação, para os
cabeçalhos de segurança virem de um lugar só. Registrado em `docs/DECISOES.md`.
