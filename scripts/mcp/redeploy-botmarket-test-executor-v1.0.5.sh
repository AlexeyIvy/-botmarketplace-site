#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

die(){ echo "TEST_EXECUTOR_REDEPLOY_REVIEW:$*" >&2; exit 2; }

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
INSTALLER="$SCRIPT_DIR/install-botmarket-test-executor-v1.sh"
FREEZE="$REPO_ROOT/docs/infrastructure/botmarket-test-executor-installation-freeze-v1.0.5.json"
SERVICE="botmarket-test-executor.service"

for c in git bash sha256sum python3 sudo systemctl runuser grep; do
  command -v "$c" >/dev/null || die "MISSING_COMMAND:$c"
done

[[ -f "$INSTALLER" ]] || die "INSTALLER_MISSING:$INSTALLER"
[[ -f "$FREEZE" ]] || die "FREEZE_MISSING:$FREEZE"
[[ "$(git -C "$REPO_ROOT" rev-parse --show-toplevel 2>/dev/null)" == "$REPO_ROOT" ]] || die "NOT_REPO_ROOT:$REPO_ROOT"
[[ -z "$(git -C "$REPO_ROOT" status --porcelain=v1 --untracked-files=all)" ]] || die "WORKTREE_NOT_CLEAN:$REPO_ROOT"

LOCAL_HEAD="$(git -C "$REPO_ROOT" rev-parse HEAD)"
ORIGIN_HEAD="$(git -C "$REPO_ROOT" rev-parse origin/main)"
[[ "$LOCAL_HEAD" == "$ORIGIN_HEAD" ]] || die "WORKTREE_NOT_AT_ORIGIN_MAIN local=$LOCAL_HEAD origin=$ORIGIN_HEAD"

EXPECTED_SHA="$(python3 - "$FREEZE" <<'PY'
import json,sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert obj["schema"]=="botmarket.test_executor_installation_freeze.v1.0.5"
print(obj["artifacts"]["main_installer"]["sha256"])
PY
)"
ACTUAL_SHA="$(sha256sum "$INSTALLER" | awk '{print $1}')"
[[ "$ACTUAL_SHA" == "$EXPECTED_SHA" ]] || die "INSTALLER_HASH_MISMATCH expected=$EXPECTED_SHA actual=$ACTUAL_SHA"

bash -n "$INSTALLER" || die "INSTALLER_BASH_SYNTAX"
echo "REDEPLOY_PREFLIGHT_PASS head=$LOCAL_HEAD installer_sha256=$ACTUAL_SHA"

BEFORE_START="$(systemctl show "$SERVICE" -p ExecMainStartTimestampMonotonic --value 2>/dev/null || true)"
BEFORE_ACTIVE=0
systemctl is-active --quiet "$SERVICE" 2>/dev/null && BEFORE_ACTIVE=1 || true

sudo -v
sudo bash "$INSTALLER"

systemctl is-active --quiet "$SERVICE" || die "SERVICE_NOT_ACTIVE_AFTER_INSTALL"
AFTER_START="$(systemctl show "$SERVICE" -p ExecMainStartTimestampMonotonic --value 2>/dev/null || true)"
if [[ "$BEFORE_ACTIVE" -eq 1 && -n "$BEFORE_START" && "$BEFORE_START" != "0" && "$AFTER_START" == "$BEFORE_START" ]]; then
  die "SERVICE_PROCESS_NOT_RESTARTED"
fi

sudo grep -Fq 'PRUNER="/usr/local/sbin/botmarket-test-prune"' /opt/botmarket-test-executor/server.py \
  || die "INSTALLED_SERVER_MISSING_PRUNER_BINDING"
sudo grep -Fq 'RETENTION_PRUNE_FAILED' /opt/botmarket-test-executor/server.py \
  || die "INSTALLED_SERVER_MISSING_RETENTION_PATH"

sudo runuser -u botmarket-testctl -- sudo -n -- /usr/local/sbin/botmarket-test-launch --self-test \
  | grep -qx 'BOTMARKET_TEST_LAUNCHER_SELFTEST_PASS' \
  || die "LAUNCHER_SELFTEST"
sudo runuser -u botmarket-testctl -- sudo -n -- /usr/local/sbin/botmarket-test-cancel --self-test \
  | grep -qx 'BOTMARKET_TEST_CANCEL_SELFTEST_PASS' \
  || die "CANCEL_SELFTEST"
sudo runuser -u botmarket-testctl -- sudo -n -- /usr/local/sbin/botmarket-test-prune --self-test \
  | grep -qx 'BOTMARKET_TEST_PRUNE_SELFTEST_PASS' \
  || die "PRUNER_SELFTEST"

echo "BOTMARKET_TEST_EXECUTOR_REDEPLOY_PASS head=$LOCAL_HEAD service=$SERVICE"
