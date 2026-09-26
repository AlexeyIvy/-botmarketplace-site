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

EXPECTED_RUNNER_SHA="280253b060f65517548054b3d8c33c315013d724ef2b836e9b8fef14628be213"
EXPECTED_LIBRARY_SHA="eaa925b71a7f33ec59de69f32dd0fb06f85bac67e89101b6f2ad50c1d792fd3f"
EXPECTED_IMPLEMENTATION_FREEZE_SHA="80928b0a11dac333b7844aa15bcdf399fd4db8739a4845e6118ebb576153b38c"
EXPECTED_SERVICE_V014_SHA="7a0f1742481b92f4d2590f09defcc5b287baaf1a9ba50f0da27488f8f5272f9d"
EXPECTED_ROUTE_GRAPH_SHA="06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928"
EXPECTED_ADMITTED_SHA="fa9f97ab1e70b30bdb196fd6f4d49a8cbc7462d13424644ddb7b88cdd9f431b0"
EXPECTED_CAPABILITY_PROBE_SHA="76f6ebd17ed2ad5a1fb8c3fad153c51fdcbaa6eab791cba37dcf3706b5820e12"
EXPECTED_CAPABILITY_FREEZE_SHA="a783bbf7e7598846f20a04b555e8c40e3c9cc15a3afc949a2f11cddb4a9341b6"
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

[[ -f "$SAFE_SUMMARY" && ! -L "$SAFE_SUMMARY" ]] || fail "v022_safe_summary_missing_or_symlink"
[[ -f "$CAP_LOG" && ! -L "$CAP_LOG" ]] || fail "v022_capability_log_missing_or_symlink"
[[ ! -e "$RECOVERY_REPORT" ]] || fail "recovery_report_already_present"

python3 -   "$SNAPSHOT"   "$SAFE_SUMMARY"   "$CAP_LOG"   "$snapshot_before"   "$EXPECTED_RUNNER_SHA"   "$EXPECTED_LIBRARY_SHA"   "$EXPECTED_IMPLEMENTATION_FREEZE_SHA"   "$EXPECTED_SERVICE_V014_SHA"   "$EXPECTED_ROUTE_GRAPH_SHA"   "$EXPECTED_ADMITTED_SHA"   "$EXPECTED_CAPABILITY_PROBE_SHA"   "$EXPECTED_CAPABILITY_FREEZE_SHA" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

(
    snapshot_arg,
    safe_summary_arg,
    cap_log_arg,
    snapshot_sha,
    runner_sha,
    library_sha,
    implementation_freeze_sha,
    service_sha,
    route_graph_sha,
    admitted_sha,
    capability_probe_sha,
    capability_freeze_sha,
) = sys.argv[1:]

def load(path):
    p = Path(path)
    obj = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(obj, dict)
    return obj

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

snapshot = load(snapshot_arg)
safe = load(safe_summary_arg)
cap_log = Path(cap_log_arg).read_text(encoding="utf-8", errors="replace")

assert sha(snapshot_arg) == snapshot_sha
assert snapshot.get("schema") == "sc001.b15.p1_nonprice_source_capability_snapshot.v0.2.2"
assert snapshot.get("status") == "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"

anchors = snapshot.get("anchors") or {}
expected_anchors = {
    "runner_sha256": runner_sha,
    "library_sha256": library_sha,
    "implementation_freeze_sha256": implementation_freeze_sha,
    "service_file_sha256": service_sha,
    "route_graph_sha256": route_graph_sha,
    "admitted_universe_sha256": admitted_sha,
    "capability_probe_sha256": capability_probe_sha,
    "capability_freeze_sha256": capability_freeze_sha,
}
for key, expected in expected_anchors.items():
    assert anchors.get(key) == expected, (key, anchors.get(key), expected)

permissions = snapshot.get("permissions") or {}
assert permissions.get("bybit_readOnly") == 1
assert permissions.get("bybit_withdraw_token_present") is False
assert permissions.get("bybit_ip_bound") is True
assert permissions.get("okx_permission") == "read_only"
assert permissions.get("okx_ip_bound") is True

assert snapshot.get("source_endpoints_pass") is True
bybit = snapshot.get("bybit_adapter") or {}
assert bybit.get("collector_parser_version") == "0.1.4"
assert bybit.get("parser_compatible") is True
assert bybit.get("withdrawMax_minus_one_semantics") == "UNLIMITED"
raw_minus_one = int(bybit.get("raw_withdrawMax_minus_one_rows") or 0)
normalized = int(bybit.get("normalized_unlimited_rows") or 0)
assert raw_minus_one > 0
assert raw_minus_one == normalized

coverage = snapshot.get("pair_coverage") or {}
assert coverage.get("frozen_admitted_assets") == 192
assert coverage.get("qualified_bybit_count") == 192
assert coverage.get("qualified_okx_count") == 192
assert coverage.get("both_venues_count") == 192
assert coverage.get("missing_bybit_assets") == []
assert coverage.get("missing_okx_assets") == []

fee_probe = snapshot.get("fee_endpoint_probe") or {}
assert fee_probe.get("pass") is True

security = snapshot.get("security") or {}
for key in (
    "secret_values_printed",
    "price_endpoints_called",
    "order_endpoints_called",
    "transfer_endpoints_called",
    "withdrawal_endpoints_called",
):
    assert security.get(key) is False, key

assert snapshot.get("price_data_used") is False
assert snapshot.get("pnl_data_used") is False
assert snapshot.get("collector_launch_authorized") is False
assert snapshot.get("live_execution_authorized") is False

assert safe.get("schema") == "sc001.b15.p1_nonprice_source_capability_safe_summary.v0.2.2"
assert safe.get("status") == "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"
assert safe.get("snapshot_sha256") == snapshot_sha
safe_bybit = safe.get("bybit_adapter") or {}
assert safe_bybit.get("collector_parser_version") == "0.1.4"
assert safe_bybit.get("parser_compatible") is True
assert int(safe_bybit.get("raw_withdrawMax_minus_one_rows") or 0) == raw_minus_one
assert int(safe_bybit.get("normalized_unlimited_rows") or 0) == normalized
safe_cov = safe.get("pair_coverage") or {}
assert safe_cov.get("frozen_admitted_assets") == 192
assert safe_cov.get("qualified_bybit_count") == 192
assert safe_cov.get("qualified_okx_count") == 192
assert safe_cov.get("both_venues_count") == 192
assert safe.get("source_endpoints_pass") is True
assert safe.get("collector_launch_authorized") is False
assert safe.get("price_data_used") is False

assert "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS" in cap_log
assert "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_REVIEW" not in cap_log
assert "Bybit parser v0.1.4 compatible = True" in cap_log
assert "price endpoints called = False" in cap_log
assert "order/transfer/withdraw endpoints called = False" in cap_log
assert "collector_launch_authorized = False" in cap_log

print("v022_snapshot_semantic_contract = PASS")
print("v022_snapshot_sha256 =", snapshot_sha)
print("bybit_withdrawMax_minus_one_rows =", raw_minus_one)
print("bybit_normalized_unlimited_rows =", normalized)
PY

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
[[ "$snapshot_after" == "$snapshot_before" ]] || fail "v022_snapshot_changed_during_recovery"
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

python3 -   "$ATTEMPT_DIR"   "$RECOVERY_REPORT"   "$snapshot_before"   "$active_final"   "$enabled_final"   "$runtime_unit_was_present"   "$SAFE_SUMMARY"   "$CAP_LOG" <<'PY'
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
    "schema": "sc001.b15.p1_v011_source_invalid_recovery.v0.1.2",
    "status": "B15P1_V011_SOURCE_INVALID_RECOVERY_V012_PASS",
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

echo "B15P1_V011_SOURCE_INVALID_RECOVERY_V012_PASS"
echo "service_active=$active_final"
echo "service_enabled=$enabled_final"
echo "runtime_unit=ABSENT"
echo "runtime_authorization=ABSENT"
echo "active_state=ABSENT"
echo "active_manifest=ABSENT"
echo "v022_snapshot_sha256=$snapshot_before"
echo "collector_start_authorized=False"
echo "price_pnl_authorized=False"
