#!/usr/bin/env bash
# backup.sh — PostgreSQL backup with optional offsite upload (§4.4).
#
# Default mode (no args): dump → gzip → local /var/backups/botmarketplace,
# rotate files older than KEEP_DAYS, then upload offsite if configured.
#
# Subcommands:
#   bash deploy/backup.sh                    # create + upload
#   bash deploy/backup.sh --restore <file>   # restore from a local .sql.gz
#   bash deploy/backup.sh --pull <key>       # fetch an offsite file → local
#   bash deploy/backup.sh --list             # list local + offsite backups
#
# Offsite upload (choose one or both; empty = no upload — backward compatible):
#   BACKUP_S3_BUCKET        e.g. "my-bucket"          (uses `aws s3 cp`, awscli required)
#   BACKUP_S3_PREFIX        e.g. "botmarket/prod"     (optional, default: "botmarket")
#   BACKUP_RCLONE_REMOTE    e.g. "b2-prod:botmarket"  (uses `rclone copy`, rclone required)
#
# Both backends get the SAME file; having both is redundant but safe. Pick
# whichever your ops stack already has installed. See RUNBOOK §4.4 for setup.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/botmarketplace}"
KEEP_DAYS="${KEEP_DAYS:-7}"
ENV_FILE="${ENV_FILE:-/opt/-botmarketplace-site/.env}"

# Validate arg shape up front so unknown args fail with a clear error
# instead of the downstream "DATABASE_URL not set" message.
case "${1:-}" in
  ""|--restore|--pull|--list|-h|--help) ;;
  *) echo "Unknown arg: $1" >&2; exit 1 ;;
esac

# --help doesn't need env + DB parsing — short-circuit here.
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,21p' "$0"
  exit 0
fi

# Load env vars to get DATABASE_URL + BACKUP_* vars
if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
fi

# --list works offline (BACKUP_DIR + whichever offsite backends are set)
if [[ "${1:-}" == "--list" ]]; then
  : # handled below after helper definitions
fi

if [[ "${1:-}" != "--list" && -z "${DATABASE_URL:-}" ]]; then
  echo "[backup] ERROR: DATABASE_URL not set" >&2
  exit 1
fi

# Parse connection string: postgresql://user:pass@host:port/dbname
if [[ -n "${DATABASE_URL:-}" ]]; then
  DB_USER=$(echo "$DATABASE_URL" | sed -E 's|.*://([^:]+):.*|\1|')
  DB_PASS=$(echo "$DATABASE_URL" | sed -E 's|.*://[^:]+:([^@]+)@.*|\1|')
  DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+)[:/].*|\1|')
  DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')
  DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^?]+).*|\1|')
fi

# ─── offsite helpers ────────────────────────────────────────────────────

offsite_s3_uri() {
  local name="$1"
  local prefix="${BACKUP_S3_PREFIX:-botmarket}"
  echo "s3://${BACKUP_S3_BUCKET}/${prefix}/${name}"
}

upload_offsite() {
  local file="$1"
  local name
  name=$(basename "$file")
  local did_any=0

  if [[ -n "${BACKUP_S3_BUCKET:-}" ]]; then
    did_any=1
    if ! command -v aws >/dev/null; then
      echo "[backup] WARN: BACKUP_S3_BUCKET set but 'aws' CLI missing — skipping S3 upload" >&2
    else
      local uri
      uri=$(offsite_s3_uri "$name")
      echo "[backup] uploading → $uri"
      aws s3 cp --only-show-errors "$file" "$uri"
    fi
  fi

  if [[ -n "${BACKUP_RCLONE_REMOTE:-}" ]]; then
    did_any=1
    if ! command -v rclone >/dev/null; then
      echo "[backup] WARN: BACKUP_RCLONE_REMOTE set but 'rclone' missing — skipping rclone upload" >&2
    else
      echo "[backup] uploading → ${BACKUP_RCLONE_REMOTE}/${name}"
      rclone copy --quiet "$file" "${BACKUP_RCLONE_REMOTE}/"
    fi
  fi

  if [[ "$did_any" -eq 0 ]]; then
    echo "[backup] offsite upload not configured (BACKUP_S3_BUCKET / BACKUP_RCLONE_REMOTE empty)"
  fi
}

pull_offsite() {
  local key="$1"
  local dest="$BACKUP_DIR/$key"
  mkdir -p "$BACKUP_DIR"

  if [[ -n "${BACKUP_S3_BUCKET:-}" ]] && command -v aws >/dev/null; then
    local uri
    uri=$(offsite_s3_uri "$key")
    echo "[backup] pulling ← $uri"
    aws s3 cp --only-show-errors "$uri" "$dest"
    echo "$dest"
    return 0
  fi

  if [[ -n "${BACKUP_RCLONE_REMOTE:-}" ]] && command -v rclone >/dev/null; then
    echo "[backup] pulling ← ${BACKUP_RCLONE_REMOTE}/${key}"
    rclone copyto --quiet "${BACKUP_RCLONE_REMOTE}/${key}" "$dest"
    echo "$dest"
    return 0
  fi

  echo "[backup] ERROR: no offsite backend configured (BACKUP_S3_BUCKET / BACKUP_RCLONE_REMOTE)" >&2
  return 1
}

list_backups() {
  echo "== Local ($BACKUP_DIR) =="
  ls -lh "$BACKUP_DIR"/botmarket_*.sql.gz 2>/dev/null || echo "  (none)"

  if [[ -n "${BACKUP_S3_BUCKET:-}" ]] && command -v aws >/dev/null; then
    local prefix="${BACKUP_S3_PREFIX:-botmarket}"
    echo ""
    echo "== S3 (s3://${BACKUP_S3_BUCKET}/${prefix}/) =="
    aws s3 ls "s3://${BACKUP_S3_BUCKET}/${prefix}/" || true
  fi

  if [[ -n "${BACKUP_RCLONE_REMOTE:-}" ]] && command -v rclone >/dev/null; then
    echo ""
    echo "== rclone (${BACKUP_RCLONE_REMOTE}) =="
    rclone ls "$BACKUP_RCLONE_REMOTE" || true
  fi
}

restore_from_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "[backup] ERROR: file not found: $file" >&2
    return 1
  fi

  echo "[backup] Restoring from $file"
  echo "[backup] ⚠ This will overwrite database: $DB_NAME on $DB_HOST:$DB_PORT"
  read -r -p "  Proceed? [y/N] " answer
  case "$answer" in
    [yY]|[yY][eE][sS]) ;;
    *) echo "Aborted."; return 1 ;;
  esac

  if [[ "$file" == *.gz ]]; then
    gunzip -c "$file" | PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
  else
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" < "$file"
  fi
  echo "[backup] Restore complete. Run smoke-test: bash deploy/smoke-test.sh"
}

# ─── main ───────────────────────────────────────────────────────────────

if [[ $# -gt 0 ]]; then
  case "$1" in
    --restore)
      if [[ $# -lt 2 ]]; then echo "Usage: $0 --restore <file>" >&2; exit 1; fi
      restore_from_file "$2"
      exit $?
      ;;
    --pull)
      if [[ $# -lt 2 ]]; then echo "Usage: $0 --pull <key>" >&2; exit 1; fi
      pull_offsite "$2"
      exit $?
      ;;
    --list)
      list_backups
      exit 0
      ;;
  esac
fi

# Default: create a backup
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="$BACKUP_DIR/botmarket_${TIMESTAMP}.sql.gz"

echo "[backup] Starting backup → $FILENAME"

PGPASSWORD="$DB_PASS" pg_dump \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  "$DB_NAME" | gzip > "$FILENAME"

echo "[backup] Done: $(du -sh "$FILENAME" | cut -f1)"

# Offsite upload (no-op if neither BACKUP_S3_BUCKET nor BACKUP_RCLONE_REMOTE is set)
upload_offsite "$FILENAME"

# Remove local backups older than KEEP_DAYS (offsite retention is managed by
# bucket-side lifecycle policy — see RUNBOOK §4.4)
find "$BACKUP_DIR" -name "botmarket_*.sql.gz" -mtime +"$KEEP_DAYS" -delete
echo "[backup] Cleaned local backups older than ${KEEP_DAYS} days"
echo "[backup] Stored local backups: $(ls -1 "$BACKUP_DIR"/botmarket_*.sql.gz 2>/dev/null | wc -l)"
