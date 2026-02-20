#!/usr/bin/env bash
# backup.sh — Daily PostgreSQL backup
# Managed by: deploy/botmarket-backup.timer (systemd)
# Manual run: bash deploy/backup.sh

set -euo pipefail

BACKUP_DIR="/var/backups/botmarketplace"
KEEP_DAYS=7
ENV_FILE="/opt/-botmarketplace-site/.env"

# Load env vars to get DATABASE_URL
if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "[backup] ERROR: DATABASE_URL not set" >&2
  exit 1
fi

# Parse connection string: postgresql://user:pass@host:port/dbname
DB_USER=$(echo "$DATABASE_URL" | sed -E 's|.*://([^:]+):.*|\1|')
DB_PASS=$(echo "$DATABASE_URL" | sed -E 's|.*://[^:]+:([^@]+)@.*|\1|')
DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+)[:/].*|\1|')
DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')
DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^?]+).*|\1|')

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

# Remove backups older than KEEP_DAYS
find "$BACKUP_DIR" -name "botmarket_*.sql.gz" -mtime +"$KEEP_DAYS" -delete
echo "[backup] Cleaned backups older than ${KEEP_DAYS} days"
echo "[backup] Stored backups: $(ls -1 "$BACKUP_DIR"/botmarket_*.sql.gz 2>/dev/null | wc -l)"
