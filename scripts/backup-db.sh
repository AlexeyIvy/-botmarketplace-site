#!/bin/bash
set -euo pipefail

BACKUP_DIR=/opt/backups
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

pg_dump "$DATABASE_URL" > "$BACKUP_DIR/botmarket_$TIMESTAMP.sql"

# Remove backups older than 14 days
find "$BACKUP_DIR" -name "*.sql" -mtime +14 -delete

echo "$(date): Backup completed — botmarket_$TIMESTAMP.sql" >> /var/log/botmarket-backup.log
