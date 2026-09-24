#!/usr/bin/env bash
set -euo pipefail

REPO="/var/lib/botmarket-github-control/repo"
PROBE="$REPO/research/sc001/sc001_b15p1_nonprice_source_capability_revalidation_v0_1.py"
FREEZE="$REPO/docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-freeze-v0.1.json"
ENV_FILE="/home/botmarket/.config/sc001/b15-p1.env"
OUT_DIR="/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY"
SNAPSHOT="$OUT_DIR/source_capability_snapshot.json"
SAFE_SUMMARY="$OUT_DIR/source_capability_safe_summary.json"
LOG="$OUT_DIR/source_capability_revalidation_run.log"

EXPECTED_PROBE_SHA="489e769665abcefd56bba9937d4179e932083e4545b3d1cac85638adf2b4bf1a"
EXPECTED_FREEZE_SHA="d0332d69208de8cdb4f8fdf9e521ff31b9db02717edbb1b2fae688931af4b4c3"

die() {
  echo "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_REVIEW"
  echo "reason=$1"
  exit 2
}

[[ -f "$PROBE" ]] || die "probe_missing"
[[ -f "$FREEZE" ]] || die "freeze_missing"
[[ -f "$ENV_FILE" ]] || die "credential_env_missing"

probe_sha="$(sha256sum "$PROBE" | awk '{print $1}')"
freeze_sha="$(sha256sum "$FREEZE" | awk '{print $1}')"
[[ "$probe_sha" == "$EXPECTED_PROBE_SHA" ]] || die "probe_sha_mismatch"
[[ "$freeze_sha" == "$EXPECTED_FREEZE_SHA" ]] || die "freeze_sha_mismatch"

env_mode="$(stat -c '%a' "$ENV_FILE")"
[[ "$env_mode" == "600" ]] || die "credential_env_mode_not_0600"

install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"

rm -f "$SNAPSHOT" "$SAFE_SUMMARY"
: > "$LOG"
chown botmarket:botmarket "$LOG"
chmod 0640 "$LOG"

set +e
sudo -u botmarket -H \
  env \
    B15P1_REPO_ROOT="$REPO" \
    B15P1_CAPABILITY_SNAPSHOT="$SNAPSHOT" \
    /usr/bin/python3 "$PROBE" --mode run \
  2>&1 | tee "$LOG"
rc="${PIPESTATUS[0]}"
set -e

if [[ "$rc" -ne 0 ]]; then
  echo "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_REVIEW"
  echo "probe_exit_code=$rc"
  echo "collector_launch_authorized=False"
  exit "$rc"
fi

[[ -f "$SNAPSHOT" ]] || die "snapshot_missing_after_pass"
[[ -f "$SAFE_SUMMARY" ]] || die "safe_summary_missing_after_pass"

python3 - "$SNAPSHOT" "$SAFE_SUMMARY" <<'PY'
import hashlib, json, sys
from pathlib import Path

snapshot=Path(sys.argv[1])
summary=Path(sys.argv[2])

obj=json.loads(snapshot.read_text())
safe=json.loads(summary.read_text())

assert obj.get("status")=="B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"
assert obj.get("collector_launch_authorized") is False
assert obj.get("price_data_used") is False
assert obj.get("pnl_data_used") is False
assert obj.get("live_execution_authorized") is False
assert obj.get("source_endpoints_pass") is True
assert obj.get("permissions",{}).get("bybit_readOnly")==1
assert obj.get("permissions",{}).get("bybit_withdraw_token_present") is False
assert obj.get("permissions",{}).get("okx_permission")=="read_only"

sha=hashlib.sha256(snapshot.read_bytes()).hexdigest()
assert safe.get("snapshot_sha256")==sha

print("snapshot_sha256 =",sha)
print("qualified_bybit_count =",safe["pair_coverage"]["qualified_bybit_count"])
print("qualified_okx_count =",safe["pair_coverage"]["qualified_okx_count"])
print("qualified_both_venues_count =",safe["pair_coverage"]["both_venues_count"])
PY

echo "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_PASS"
echo "snapshot=$SNAPSHOT"
echo "safe_summary=$SAFE_SUMMARY"
echo "log=$LOG"
echo "collector_launch_authorized=False"
echo "price_data_used=False"
