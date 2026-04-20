#!/usr/bin/env bash
# rollback.sh — Roll back to the previous release tag.
#
# Usage:
#   bash deploy/rollback.sh                 # roll back to the previous tag
#   bash deploy/rollback.sh --to v0.1.0     # roll back to a specific tag
#   bash deploy/rollback.sh --dry-run       # print plan without executing
#
# Strategy:
#   1. Look up previous tag (2nd most recent, sorted by semver-ish)
#   2. Confirm with operator (unless --yes)
#   3. Delegate to deploy.sh --ref <previous-tag>
#
# DB migrations are NOT automatically rolled back. Prisma migrations are
# forward-only; if the rollback target is behind a breaking migration,
# restore from backup first (see RUNBOOK §7).

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/-botmarketplace-site}"
TARGET=""
ASSUME_YES=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --to)      TARGET="$2"; shift 2 ;;
    --yes|-y)  ASSUME_YES=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help)
      sed -n '2,15p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd "$APP_DIR"

CURRENT=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)

git fetch origin --tags --quiet

if [[ -z "$TARGET" ]]; then
  # Pick the 2nd-most-recent tag by version sort (first is typically current release)
  TARGET=$(git tag --sort=-version:refname | sed -n '2p')
  if [[ -z "$TARGET" ]]; then
    echo "No previous tag found. Tags available:"
    git tag --sort=-version:refname | head -5
    exit 1
  fi
fi

if ! git rev-parse -q --verify "refs/tags/$TARGET" >/dev/null; then
  echo "Tag not found: $TARGET"
  echo "Available tags (most recent first):"
  git tag --sort=-version:refname | head -10
  exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  BotMarketplace ROLLBACK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Current: $CURRENT"
echo "  Target : $TARGET"
echo ""
echo "  Commits that will be reverted:"
git log --oneline "$TARGET..HEAD" | head -20 | sed 's/^/    /'
echo ""

cat <<'WARN'
  ⚠ DB migrations are forward-only. If the rollback target predates a
    breaking schema change (dropped column, type change), this script
    will NOT restore the old schema. Restore from backup instead:
        journalctl -u botmarket-backup -n 20
        bash deploy/backup.sh --restore <dump>
    See docs/runbooks/RUNBOOK.md §7.
WARN
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] Would execute: bash deploy/deploy.sh --ref $TARGET"
  exit 0
fi

if [[ $ASSUME_YES -eq 0 ]]; then
  read -r -p "Proceed with rollback to $TARGET? [y/N] " answer
  case "$answer" in
    [yY]|[yY][eE][sS]) ;;
    *) echo "Aborted."; exit 1 ;;
  esac
fi

echo "Rolling back to $TARGET…"
bash "$APP_DIR/deploy/deploy.sh" --ref "$TARGET"
