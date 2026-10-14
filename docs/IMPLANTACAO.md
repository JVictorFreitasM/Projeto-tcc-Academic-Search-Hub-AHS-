# Implantação, colheita agendada e backup

Como colocar o sistema no ar de forma contínua, com a colheita periódica das fontes e uma cópia de
segurança do banco. Sem Docker e sem fila: **systemd** para manter o servidor, **cron** para as
tarefas agendadas e um **proxy reverso** (Nginx ou Caddy) para o HTTPS.

## 0. O que foi verificado e o que não foi

Esta seção existe para ninguém descrever um ambiente que não existe.

| Parte | Situação |
|---|---|
| Aplicação em modo produção, saúde, documentação, cabeçalhos, recusa de configuração insegura | **Verificado** em 14/10/2026, na máquina de desenvolvimento (Windows), sem proxy e sem HTTPS. Evidência: `docs/evidencias/os-037/verificacao-local.txt` |
| Script de backup (`scripts/backup_db.sh`) | **Verificado**: testes automáticos com `pg_dump` falso e uma execução real com `pg_dump` do PostgreSQL 18 |
| Backup real **restaurado** num banco novo, com dados conferidos | **Verificado** em 14/10/2026, na máquina de desenvolvimento, com dados fictícios. Evidência: `docs/evidencias/os-037/teste-restauracao.txt` |
| Serviço systemd, Nginx/Caddy, certificado, cron | **Exemplos escritos, NÃO executados.** Não há servidor nem domínio neste projeto |
| Colheita agendada rodando e `status` mostrando o resultado | **Pendente**: depende de fontes OAI validadas e habilitadas (`docs/PENDENCIAS_DESENVOLVEDOR.md`) |

**Se o sistema for rodar só na máquina do autor para a defesa, o TCC deve dizer isso** em vez de
descrever um ambiente de produção que não existe. Os itens "pendente" da seção 10 são o que falta
para poder afirmar uma implantação.

## 1. Requisitos do servidor

- Linux com systemd (os exemplos supõem Debian ou Ubuntu), acesso de administrador (`sudo`).
- Python 3.11 ou mais novo e [uv](https://docs.astral.sh/uv/).
- PostgreSQL 14 ou mais novo, com as extensões `unaccent`, `pg_trgm` e `pgcrypto`, e o cliente
  (`pg_dump`, `pg_restore`) **de versão igual ou mais nova** que a do servidor.
- Nginx **ou** Caddy, `cron`, `bash` e `flock`.
- Um domínio apontando para o servidor e as portas 80 e 443 abertas.

## 2. Usuário do sistema sem privilégios

A aplicação **não** roda como administrador:

```
sudo useradd --system --home-dir /opt/academic-search-hub --shell /usr/sbin/nologin academicsearch
sudo install -d -o academicsearch -g academicsearch /opt/academic-search-hub
```

## 3. Instalação

```
sudo -u academicsearch git clone <endereço-do-repositório> /opt/academic-search-hub
cd /opt/academic-search-hub
sudo -u academicsearch uv sync --no-dev --frozen    # só as dependências de execução
```

## 4. Banco de dados

Crie o usuário, o banco e as extensões como superusuário (`docs/EXECUCAO.md`, seção 1), depois aplique
as migrações com o ambiente de produção carregado:

```
sudo -u academicsearch bash -c 'cd /opt/academic-search-hub && set -a && . /etc/academic-search-hub/env && set +a && .venv/bin/alembic upgrade head'
```

## 5. Variáveis de ambiente em produção

O modelo é `deploy/academic-search.env.example`. No servidor:

```
sudo install -d -m 0750 /etc/academic-search-hub
sudo install -m 0600 deploy/academic-search.env.example /etc/academic-search-hub/env
sudo nano /etc/academic-search-hub/env            # preencher
```

| Variável | Em produção |
|---|---|
| `APP_ENV` | `production`. Passa a exigir `SECRET_KEY` e a recusar `ALLOWED_ORIGINS=*`, e a resposta envia `Strict-Transport-Security` |
| `SECRET_KEY` | Gerada **no servidor** (`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`). Nunca a do desenvolvimento. Vazia, a aplicação não sobe (de propósito) |
| `ALLOWED_ORIGINS` | O endereço público (`https://exemplo.org`), **sem `*`** |
| `DOCS_ENABLED` | `true` mantém `/api/docs` público; `false` o desliga (404). Decisão sua |
| `DATABASE_URL` | Com a senha do banco do servidor; caracteres especiais codificados (`@` vira `%40`) |
| `OPENALEX_API_KEY`, `CORE_API_KEY`, `CONTACT_EMAIL` | Suas chaves e o e-mail de contato da colheita |

O arquivo `/etc/academic-search-hub/env` guarda segredos: dono root, modo 0600 e **nunca** vai para o
Git. Nada em `deploy/` tem segredo (`tests/unit/test_deploy_files.py` confere).

## 6. Serviço (systemd)

```
sudo cp deploy/academic-search.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now academic-search      # sobe agora e a cada reinicialização
systemctl status academic-search
journalctl -u academic-search -f                 # logs (JSON)
```

O serviço roda **um único processo** do Uvicorn (`python -m app.run`), reinicia sozinho em caso de
falha (`Restart=on-failure`) e escuta só em `127.0.0.1:8000`. Não use `--workers`: o limite de
requisições é em memória e deixaria de valer por IP (`docs/SEGURANCA.md`).

## 7. Proxy reverso e HTTPS

Escolha um:

- **Nginx** (`deploy/nginx.conf.example`): copie para `/etc/nginx/sites-available/`, troque
  `exemplo.org`, ative e teste com `nginx -t`.
- **Caddy** (`deploy/Caddyfile.example`): obtém e renova o certificado sozinho.

Certificado gratuito (Let's Encrypt) com o Nginx, por exemplo com o certbot:

```
sudo certbot certonly --webroot -w /var/www/certbot -d exemplo.org
systemctl list-timers | grep certbot     # confira que a renovação automática existe
```

**Os cabeçalhos de segurança vêm da aplicação**, não do proxy: o exemplo do Nginx encaminha tudo,
inclusive os arquivos do frontend, e **não** tem `add_header`. Se servir os estáticos pelo Nginx,
terá de repetir ali o CSP e os demais cabeçalhos. Depois de publicar, confira que não há
duplicatas: `curl -sI https://exemplo.org/ | sort`.

## 8. Colheita agendada

`deploy/crontab.example` roda `run-all` **uma vez por dia, às 03:00** (a colheita é incremental, então
basta), com a saída em `/var/log/academic-search/colheita.log`, e o backup às 03:30. Instale como o
usuário do serviço:

```
sudo install -d -o academicsearch -g academicsearch /var/log/academic-search
sudo crontab -u academicsearch /opt/academic-search-hub/deploy/crontab.example
```

Ver o resultado, com o ambiente carregado:

```
cd /opt/academic-search-hub && set -a && . /etc/academic-search-hub/env && set +a \
  && .venv/bin/python -m app.harvest.cli status
tail -n 40 /var/log/academic-search/colheita.log
```

O comando termina com código de erro se alguma fonte falhar e o motivo fica no log. Só as fontes com
`enabled: true` em `config/oai_sources.yml` são colhidas. O mesmo `crontab` apaga a cada semana os
eventos de segurança com mais de 180 dias (`docs/LGPD.md`).

## 9. Backup e restauração

### O que o script faz

`scripts/backup_db.sh` usa `pg_dump` no formato "custom" (já compactado) e grava
`academic_search-AAAAMMDD-HHMMSS.dump` em `BACKUP_DIR`:

- lê o endereço do banco de `DATABASE_URL` (ambiente) ou da linha `DATABASE_URL=` do arquivo
  `ENV_FILE`, **sem executar** o arquivo, e passa a senha pela variável `PGPASSWORD`, nunca na linha
  de comando;
- só dá o nome final à cópia depois de `pg_restore --list` aprová-la; uma falha não deixa arquivo
  parcial;
- guarda as **7 cópias mais recentes** (`BACKUP_KEEP`) e apaga as mais antigas;
- cria a pasta e os arquivos só legíveis pelo dono (modo 0700 e 0600).

Códigos de saída: 0 ok, 1 falha ao copiar, 2 configuração ou ferramenta ausente.

### Onde ficam as cópias e quem tem acesso

Em `/var/backups/academic-search-hub` (definido no `crontab.example`), dono `academicsearch`, só ele
e o administrador (root) leem. **Elas têm dados pessoais** (nome, e-mail, hash da senha, favoritos,
histórico): a mesma proteção do banco vale para elas. **Uma cópia só na mesma máquina não protege
contra a perda da máquina:** copie periodicamente para outro lugar também restrito (por exemplo, com
`rsync` por SSH ou um disco externo). Isso não está automatizado aqui.

**LGPD:** uma conta excluída continua nas cópias antigas até serem substituídas (**até 7 dias**), e
restaurar uma cópia traz de volta o que foi excluído depois dela. Ver `docs/LGPD.md`.

### Restaurar (procedimento)

Restaure **primeiro num banco ao lado**, nunca direto sobre o de produção:

```
# 1. Crie um banco vazio, ao lado do de produção
sudo -u postgres createdb -O app_user academic_search_restauracao

# 2. Restaure a cópia (a senha vem de ~/.pgpass, modo 0600, ou de PGPASSWORD; não na linha de comando)
pg_restore --no-owner --no-privileges --exit-on-error \
  -h 127.0.0.1 -U app_user -d academic_search_restauracao \
  /var/backups/academic-search-hub/academic_search-AAAAMMDD-HHMMSS.dump

# 3. Confira: contagem de linhas das tabelas e uma busca
psql -h 127.0.0.1 -U app_user -d academic_search_restauracao \
  -c "select (select count(*) from users) usuarios, (select count(*) from oai_records) registros"
```

Para pôr a cópia no lugar do banco de produção: pare o serviço (`systemctl stop academic-search`),
renomeie o banco atual e o restaurado (`ALTER DATABASE ... RENAME TO ...`), suba o serviço e confira
`/api/v1/health`. Guarde o banco antigo até ter certeza.

A restauração funcionou com um usuário **sem** privilégio de superusuário e **sem** criar as
extensões antes: as extensões `unaccent`, `pg_trgm` e `pgcrypto` são "confiáveis" e o dono do banco
consegue recriá-las.

### Teste de restauração feito (14/10/2026)

Máquina de desenvolvimento (Windows, Git Bash, PostgreSQL 18), dados **fictícios**. Banco de origem
com as migrações aplicadas e 2 usuários, 1 favorito, 1 item de histórico, 2 registros OAI e 1 evento;
o script gerou uma cópia de 19.198 bytes (código 0, 3,2 s); a restauração num banco novo levou 1,2 s;
as contagens, um hash (MD5) do conteúdo de cada tabela e uma busca em português sem acento
(`educacao` achando "Educação") deram **os mesmos resultados** na origem e na restauração, e o gatilho
do índice de texto, a função `immutable_unaccent` e as extensões estavam lá. Detalhes em
`docs/evidencias/os-037/teste-restauracao.txt`.

Limites desse teste: foi na máquina de desenvolvimento, com pouquíssimos dados e sem proxy. **Repita
no servidor real**, com o banco real, e anote aqui a data e o resultado: PENDENTE (desenvolvedor).

**Defeito achado no próprio teste:** uma primeira versão do script saía com erro mesmo depois de gerar
a cópia (o curinga tratava a barra invertida do caminho do Windows como escape e a retenção nunca
achava os arquivos). Foi corrigido e ganhou testes (`tests/unit/test_backup_script.py`).

## 10. Lista de verificação depois de publicar

| # | O que conferir | Como | Resultado |
|---|---|---|---|
| 1 | `health` responde | `curl https://exemplo.org/api/v1/health` | **Local (produção, sem proxy):** HTTP 200 `{"status":"ok","database":"ok"}`. No servidor: **PENDENTE** |
| 2 | `/api/docs` conforme `DOCS_ENABLED` | `curl -I https://exemplo.org/api/docs` | **Local:** `false` → 404 (e `/api/openapi.json` 404); `true` → 200. No servidor: **PENDENTE** |
| 3 | HTTPS válido | Abrir no navegador; `curl -I https://exemplo.org` sem `-k` | **PENDENTE** (sem servidor nem domínio) |
| 4 | Cabeçalhos presentes e sem duplicata | `curl -sI https://exemplo.org/ \| sort` | **Local:** `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e `X-Request-ID` presentes. Atrás do proxy: **PENDENTE** |
| 5 | Configuração insegura é recusada em produção | `SECRET_KEY` vazia e `ALLOWED_ORIGINS=*` | **Verificado:** as duas recusadas, com mensagem sem expor valores |
| 6 | Uma busca real funciona | Buscar um tema no site | **PENDENTE** (precisa de chaves e de fontes colhidas) |
| 7 | O serviço sobe sozinho depois de reiniciar a máquina | `systemctl is-enabled academic-search` e reiniciar | **PENDENTE** |
| 8 | A colheita agendada rodou | `status` da CLI e `colheita.log` | **PENDENTE** (depende das fontes OAI) |
| 9 | Um backup foi gerado | `ls -l /var/backups/academic-search-hub` | **Verificado** na máquina de desenvolvimento; no servidor: **PENDENTE** |
| 10 | Um backup foi restaurado em banco de teste | Seção 9 | **Verificado** na máquina de desenvolvimento; no servidor: **PENDENTE** |
| 11 | Nenhum segredo nos arquivos de `deploy/` | `tests/unit/test_deploy_files.py` | **Verificado** por teste automático |

Os itens "local" foram medidos com o servidor da aplicação em modo produção na máquina de
desenvolvimento (`docs/evidencias/os-037/verificacao-local.txt`); **não** provam o que o proxy e o
HTTPS fazem.

## 11. Atualizar uma instalação

```
cd /opt/academic-search-hub
sudo -u academicsearch git pull
sudo -u academicsearch uv sync --no-dev --frozen
sudo -u academicsearch bash -c 'set -a && . /etc/academic-search-hub/env && set +a && .venv/bin/alembic upgrade head'
sudo systemctl restart academic-search
curl https://exemplo.org/api/v1/health
```

Faça um backup antes (`scripts/backup_db.sh`) se a atualização tiver migração.
