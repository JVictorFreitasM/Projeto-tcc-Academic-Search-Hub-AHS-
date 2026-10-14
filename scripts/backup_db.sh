#!/usr/bin/env bash
# Cópia de segurança do banco (OS-037): pg_dump compactado, nome com data e retenção local.
#
# Uso:  scripts/backup_db.sh
#
# Configuração, por variáveis de ambiente (a senha nunca vai na linha de comando):
#   DATABASE_URL  endereço do banco. Se ausente, é lido da linha DATABASE_URL= do ENV_FILE
#   ENV_FILE      arquivo de ambiente (padrão: .env no diretório atual); não é executado, só lido
#   BACKUP_DIR    onde guardar as cópias (padrão: ./backups)
#   BACKUP_KEEP   quantas cópias manter (padrão: 7)
#
# Gera $BACKUP_DIR/academic_search-AAAAMMDD-HHMMSS.dump (formato "custom" do pg_dump, já
# compactado) e apaga as mais antigas além de BACKUP_KEEP. A cópia só recebe o nome final depois
# de verificada com `pg_restore --list`; uma falha não deixa arquivo parcial.
# Restauração: docs/IMPLANTACAO.md. Códigos de saída: 0 ok; 1 falha ao copiar; 2 configuração
# ou ferramenta ausente.
set -euo pipefail
umask 077 # as cópias têm dados pessoais: só o dono lê

die() {
  echo "backup_db: $1" >&2
  exit "${2:-1}"
}

urldecode() {
  local text="$1"
  printf '%b' "${text//%/\\x}"
}

env_file="${ENV_FILE:-.env}"
dir="${BACKUP_DIR:-./backups}"
keep="${BACKUP_KEEP:-7}"

[[ "$keep" =~ ^[0-9]+$ ]] && ((keep >= 1)) || die "BACKUP_KEEP deve ser um inteiro maior que zero" 2

url="${DATABASE_URL:-}"
if [[ -z "$url" && -f "$env_file" ]]; then
  url="$(grep -E '^DATABASE_URL=' "$env_file" | tail -n 1 | cut -d= -f2- || true)"
  url="${url%$'\r'}"
  url="${url#\"}"
  url="${url%\"}"
fi
[[ -n "$url" ]] || die "DATABASE_URL não definida (nem no ambiente nem em $env_file)" 2

# postgresql[+driver]://usuario[:senha]@host[:porta]/banco (aceita o endereço do SQLAlchemy)
url_re='^postgres(ql)?(\+[A-Za-z0-9_]+)?://([^:@/]+)(:([^@]*))?@([^:/?]+)(:([0-9]+))?/([^?]+)'
[[ "$url" =~ $url_re ]] || die "DATABASE_URL em formato não reconhecido" 2
db_user="$(urldecode "${BASH_REMATCH[3]}")"
db_pass="$(urldecode "${BASH_REMATCH[5]:-}")"
db_host="${BASH_REMATCH[6]}"
db_port="${BASH_REMATCH[8]:-5432}"
db_name="${BASH_REMATCH[9]}"

command -v pg_dump >/dev/null 2>&1 || die "pg_dump não encontrado no PATH (instale o cliente do PostgreSQL)" 2

mkdir -p "$dir"
chmod 700 "$dir" 2>/dev/null || true
final="$dir/academic_search-$(date +%Y%m%d-%H%M%S).dump"
partial="$final.partial"
trap 'rm -f "$partial"' EXIT

PGPASSWORD="$db_pass" pg_dump --format=custom --no-owner --no-privileges \
  --host="$db_host" --port="$db_port" --username="$db_user" --dbname="$db_name" \
  --file="$partial" || die "pg_dump falhou" 1

[[ -s "$partial" ]] || die "a cópia gerada está vazia" 1
if command -v pg_restore >/dev/null 2>&1; then
  pg_restore --list "$partial" >/dev/null || die "a cópia gerada está corrompida (pg_restore --list falhou)" 1
else
  echo "backup_db: aviso: pg_restore ausente; a cópia não foi verificada" >&2
fi
mv "$partial" "$final"

# Retenção: mantém as BACKUP_KEEP mais recentes (o nome carrega a data, então ordena por nome).
# O diretório vai entre aspas e só o padrão do arquivo é expandido: assim espaços, colchetes e as
# barras invertidas de um caminho do Windows (Git Bash) não são tratados como curinga.
shopt -s nullglob
files=("$dir"/academic_search-*.dump)
if ((${#files[@]} > keep)); then
  mapfile -t all < <(printf '%s\n' "${files[@]}" | sort -r)
  for old in "${all[@]:keep}"; do
    rm -f -- "$old"
  done
fi
files=("$dir"/academic_search-*.dump)

echo "backup_db: gerado $final ($(wc -c <"$final") bytes); ${#files[@]} cópia(s) mantida(s) em $dir"
