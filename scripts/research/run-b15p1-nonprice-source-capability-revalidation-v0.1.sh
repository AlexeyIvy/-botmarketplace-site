#!/usr/bin/env bash
set -euo pipefail

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p1-capability-revalidation-v0.1-stage"
PROBE_REL="research/sc001/sc001_b15p1_nonprice_source_capability_revalidation_v0_1.py"
FREEZE_REL="docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-freeze-v0.1.json"
PROBE="$REPO/$PROBE_REL"
FREEZE="$REPO/$FREEZE_REL"
STAGED_PROBE="$STAGE/$PROBE_REL"
STAGED_FREEZE="$STAGE/$FREEZE_REL"
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

# GitHub Control clone is intentionally private to botmarket-github.
# Never relax /var/lib/botmarket-github-control permissions for this probe.
# Stage only the exact non-secret files required by the frozen capability probe.
STAGE_FILES=(
  "$PROBE_REL"
  "$FREEZE_REL"
  "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-v0.1.md"
  "docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-spec-v0.1.json"
  "research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_2.py"
  "docs/research/sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.2.json"
  "ops/systemd/sc001-b15p1-transferability-v0.1.2.service"
  "docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/directed_route_graph.v0.2.2.shard-index.json"
  "docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/ADMITTED.v0.2.2.json"
  "docs/research/artifacts/b15-p1-collector-implementation-v0.1.2/20260924T120400Z/implementation_self_test_manifest.json"
)

rm -rf "$STAGE"
install -d -m 0750 -o botmarket -g botmarket "$STAGE"

for rel in "${STAGE_FILES[@]}"; do
  src="$REPO/$rel"
  dst="$STAGE/$rel"
  [[ -f "$src" ]] || die "stage_source_missing:$rel"
  install -d -m 0750 -o botmarket -g botmarket "$(dirname "$dst")"
  install -m 0640 -o botmarket -g botmarket "$src" "$dst"
done

[[ -r "$STAGED_PROBE" ]] || die "staged_probe_missing"
[[ -r "$STAGED_FREEZE" ]] || die "staged_freeze_missing"

staged_probe_sha="$(sha256sum "$STAGED_PROBE" | awk '{print $1}')"
staged_freeze_sha="$(sha256sum "$STAGED_FREEZE" | awk '{print $1}')"
[[ "$staged_probe_sha" == "$EXPECTED_PROBE_SHA" ]] || die "staged_probe_sha_mismatch"
[[ "$staged_freeze_sha" == "$EXPECTED_FREEZE_SHA" ]] || die "staged_freeze_sha_mismatch"

# Verify botmarket can traverse/read the staged root before any exchange call.
sudo -u botmarket -H test -r "$STAGED_PROBE" || die "staged_probe_not_readable_by_botmarket"
sudo -u botmarket -H test -r "$STAGED_FREEZE" || die "staged_freeze_not_readable_by_botmarket"

install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"

rm -f "$SNAPSHOT" "$SAFE_SUMMARY"
: > "$LOG"
chown botmarket:botmarket "$LOG"
chmod 0640 "$LOG"

set +e
sudo -u botmarket -H \
  env \
    B15P1_REPO_ROOT="$STAGE" \
    B15P1_CAPABILITY_SNAPSHOT="$SNAPSHOT" \
    /usr/bin/python3 "$STAGED_PROBE" --mode run \
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
echo "staging_root=$STAGE"
echo "collector_launch_authorized=False"
echo "price_data_used=False"
