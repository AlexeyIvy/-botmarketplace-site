#!/usr/bin/env bash
set -eEuo pipefail
umask 027

OUT_DIR="/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY"
ATTEMPT_ROOT="$OUT_DIR/launch_attempts"
SERVICE_NAME="sc001-b15p1-transferability.service"
RUNTIME_UNIT="/etc/systemd/system/$SERVICE_NAME"
AUTH_FILE="$OUT_DIR/collector_launch_authorization.json"
STATE_FILE="$OUT_DIR/collector_state.json"
MANIFEST_FILE="$OUT_DIR/collector_manifest.json"
SYSTEMD_LOG="$OUT_DIR/systemd.log"
LAUNCH_REPORT="$OUT_DIR/collector_launch_verification_manifest.json"

SNAPSHOT="$OUT_DIR/source_capability_snapshot.json"
SAFE_SUMMARY="$OUT_DIR/source_capability_safe_summary.json"
CAP_LOG="$OUT_DIR/source_capability_revalidation_v0.2.2_run.log"
DIAG_REPORT="$OUT_DIR/diagnostics/final_launch_v011_source_invalid_diagnostic.json"
RECOVERY_REPORT="$OUT_DIR/final_launch_v0.1.1_source_invalid_recovery_manifest.json"
LOCK_FILE="/run/lock/botmarket-b15p1-v011-source-invalid-recovery.lock"

EXPECTED_SNAPSHOT_SHA="fc1b4537290451241596e67342a9ab8fa6acd827afd4aeb70b70cee1e24e8e47"
EXPECTED_OLD_SERVICE_SHA="b59d61f25b4e643f6c9f27389d9829f7e4ea91cfbbb8dffeb48a91b55d755bf8"
EXPECTED_OLD_AUTH_SHA="fd5b9a6c683bd15df2dfc26c4ba6497d8e8e152d9b70ed1dc1edeab5107f13be"

fail() {
  echo "B15P1_V011_SOURCE_INVALID_RECOVERY_REVIEW"
  echo "reason=$1"
  echo "collector_start_authorized=False"
  echo "price_pnl_authorized=False"
  exit 2
}

[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "wrapper_must_run_as_root"

for cmd in sha256sum awk install python3 systemctl pgrep date mv cp rm find wc seq sleep basename flock; do
  command -v "$cmd" >/dev/null 2>&1 || fail "required_command_missing:$cmd"
done

exec 9>"$LOCK_FILE"
flock -n 9 || fail "another_recovery_in_progress"

[[ -f "$SNAPSHOT" && ! -L "$SNAPSHOT" ]] || fail "v022_snapshot_missing_or_symlink"
snapshot_before="$(sha256sum "$SNAPSHOT" | awk '{print $1}')"
[[ "$snapshot_before" == "$EXPECTED_SNAPSHOT_SHA" ]] || fail "v022_snapshot_sha_mismatch"

[[ -f "$SAFE_SUMMARY" && ! -L "$SAFE_SUMMARY" ]] || fail "v022_safe_summary_missing_or_symlink"
[[ -f "$CAP_LOG" && ! -L "$CAP_LOG" ]] || fail "v022_capability_log_missing_or_symlink"
[[ ! -e "$RECOVERY_REPORT" ]] || fail "recovery_report_already_present"

systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true
systemctl disable "$SERVICE_NAME" >/dev/null 2>&1 || true

for _ in $(seq 1 10); do
  active_now="$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || true)"
  if [[ "$active_now" != "active" && "$active_now" != "activating" ]]; then
    break
  fi
  sleep 1
done

active_now="$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || true)"
enabled_now="$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || true)"
case "$active_now" in
  inactive|failed|unknown|"") ;;
  *) fail "service_still_running_after_stop:$active_now" ;;
esac
case "$enabled_now" in
  disabled|not-found|"") ;;
  *) fail "service_still_enabled_after_disable:$enabled_now" ;;
esac

if pgrep -f 'sc001_b15p1_nonprice_transferability_collector_v0_1_3[.]py' >/dev/null 2>&1; then
  fail "collector_v013_process_still_running"
fi
if pgrep -f 'sc001_b15p1_nonprice_transferability_collector_v0_1_4[.]py' >/dev/null 2>&1; then
  fail "collector_v014_process_unexpectedly_running"
fi

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
ATTEMPT_DIR="$ATTEMPT_ROOT/${stamp}_final_launch_v0.1.1_source_invalid_failed"
install -d -m 0750 -o botmarket -g botmarket "$ATTEMPT_DIR"

if [[ -e "$AUTH_FILE" ]]; then
  [[ -f "$AUTH_FILE" && ! -L "$AUTH_FILE" ]] || fail "runtime_authorization_not_regular"
  auth_sha="$(sha256sum "$AUTH_FILE" | awk '{print $1}')"
  [[ "$auth_sha" == "$EXPECTED_OLD_AUTH_SHA" ]] || fail "runtime_authorization_unexpected_sha:$auth_sha"
  mv "$AUTH_FILE" "$ATTEMPT_DIR/collector_launch_authorization.json"
fi

runtime_unit_was_present=false
if [[ -e "$RUNTIME_UNIT" ]]; then
  runtime_unit_was_present=true
  [[ -f "$RUNTIME_UNIT" && ! -L "$RUNTIME_UNIT" ]] || fail "runtime_unit_not_regular"
  unit_sha="$(sha256sum "$RUNTIME_UNIT" | awk '{print $1}')"
  [[ "$unit_sha" == "$EXPECTED_OLD_SERVICE_SHA" ]] || fail "runtime_unit_unexpected_sha:$unit_sha"
  cp -a "$RUNTIME_UNIT" "$ATTEMPT_DIR/runtime_unit.service"
  rm -f "$RUNTIME_UNIT"
  systemctl daemon-reload
fi

EVIDENCE_PATHS=(
  "$STATE_FILE"
  "$MANIFEST_FILE"
  "$SYSTEMD_LOG"
  "$LAUNCH_REPORT"
  "$OUT_DIR/raw_objects"
  "$OUT_DIR/polls"
  "$OUT_DIR/normalized"
  "$OUT_DIR/events"
  "$OUT_DIR/gaps"
  "$OUT_DIR/fees"
  "$OUT_DIR/invalid"
  "$OUT_DIR/daily_manifests"
)

archived_names=()
for src in "${EVIDENCE_PATHS[@]}"; do
  [[ -e "$src" ]] || continue
  [[ ! -L "$src" ]] || fail "evidence_symlink_forbidden:$src"
  name="$(basename "$src")"
  [[ ! -e "$ATTEMPT_DIR/$name" ]] || fail "archive_name_collision:$name"
  mv "$src" "$ATTEMPT_DIR/$name"
  archived_names+=("$name")
done

# Preserve the read-only diagnostic report as a copy, without removing it
# from the active diagnostics directory.
if [[ -f "$DIAG_REPORT" && ! -L "$DIAG_REPORT" ]]; then
  cp -a "$DIAG_REPORT" "$ATTEMPT_DIR/source_invalid_diagnostic.json"
fi

[[ ! -e "$AUTH_FILE" ]] || fail "runtime_authorization_still_present"
[[ ! -e "$STATE_FILE" ]] || fail "active_state_still_present"
[[ ! -e "$MANIFEST_FILE" ]] || fail "active_manifest_still_present"
[[ ! -e "$LAUNCH_REPORT" ]] || fail "active_launch_report_still_present"
[[ ! -e "$RUNTIME_UNIT" ]] || fail "runtime_unit_still_present"

snapshot_after="$(sha256sum "$SNAPSHOT" | awk '{print $1}')"
[[ "$snapshot_after" == "$EXPECTED_SNAPSHOT_SHA" ]] || fail "v022_snapshot_changed_during_recovery"
[[ -f "$SAFE_SUMMARY" && ! -L "$SAFE_SUMMARY" ]] || fail "v022_safe_summary_changed_or_missing"
[[ -f "$CAP_LOG" && ! -L "$CAP_LOG" ]] || fail "v022_capability_log_changed_or_missing"

active_final="$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || true)"
enabled_final="$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || true)"
case "$active_final" in
  inactive|failed|unknown|"") ;;
  *) fail "final_service_active_state_unexpected:$active_final" ;;
esac
case "$enabled_final" in
  disabled|not-found|"") ;;
  *) fail "final_service_enabled_state_unexpected:$enabled_final" ;;
esac

python3 -   "$ATTEMPT_DIR"   "$RECOVERY_REPORT"   "$EXPECTED_SNAPSHOT_SHA"   "$active_final"   "$enabled_final"   "$runtime_unit_was_present"   "$SAFE_SUMMARY"   "$CAP_LOG" <<'PY'
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

(
    attempt_dir,
    report_path,
    snapshot_sha,
    active,
    enabled,
    unit_was_present,
    safe_summary_path,
    cap_log_path,
) = sys.argv[1:]

root = Path(attempt_dir)

files = []
for p in sorted(root.rglob("*")):
    if p.is_file():
        files.append({
            "path": str(p.relative_to(root)),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "size_bytes": p.stat().st_size,
        })

protected = {}
for name, raw in (
    ("source_capability_safe_summary", safe_summary_path),
    ("source_capability_v022_run_log", cap_log_path),
):
    p = Path(raw)
    protected[name] = {
        "path": str(p),
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "size_bytes": p.stat().st_size,
    }

report = {
    "schema": "sc001.b15.p1_v011_source_invalid_recovery.v0.1",
    "status": "B15P1_V011_SOURCE_INVALID_RECOVERY_PASS",
    "recovered_utc": datetime.now(timezone.utc).isoformat(),
    "v022_snapshot_sha256": snapshot_sha,
    "archive_dir": str(root),
    "archived_file_count": len(files),
    "archived_files": files,
    "protected_live_capability_files": protected,
    "runtime_unit_was_present_before_recovery": unit_was_present.lower() == "true",
    "service_active_after_recovery": active,
    "service_enabled_after_recovery": enabled,
    "runtime_unit_present_after_recovery": False,
    "runtime_authorization_present_after_recovery": False,
    "active_collector_state_present_after_recovery": False,
    "active_collector_manifest_present_after_recovery": False,
    "collector_start_authorized": False,
    "price_pnl_authorized": False,
    "next_state": "PREPARE_V014_CONTROLLED_LAUNCH_GATE",
}

out = Path(report_path)
tmp = out.with_name(out.name + ".tmp")
tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
os.chmod(tmp, 0o640)
os.replace(tmp, out)

print("recovery_report_sha256 =", hashlib.sha256(out.read_bytes()).hexdigest())
print("archived_file_count =", len(files))
print("archive_dir =", root)
PY

echo "B15P1_V011_SOURCE_INVALID_RECOVERY_PASS"
echo "service_active=$active_final"
echo "service_enabled=$enabled_final"
echo "runtime_unit=ABSENT"
echo "runtime_authorization=ABSENT"
echo "active_state=ABSENT"
echo "active_manifest=ABSENT"
echo "v022_snapshot_sha256=$EXPECTED_SNAPSHOT_SHA"
echo "collector_start_authorized=False"
echo "price_pnl_authorized=False"
