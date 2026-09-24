#!/usr/bin/env bash
set -euo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p1-capability-revalidation-v0.2.1-stage"

PROBE_REL="research/sc001/sc001_b15p1_nonprice_source_capability_revalidation_v0_2_1.py"
FREEZE_REL="docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-freeze-v0.2.1.json"
PROTOCOL_REL="docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-v0.2.md"
SPEC_REL="docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-spec-v0.2.1.json"
RUNNER_REL="research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_3.py"
IMPLEMENTATION_FREEZE_REL="docs/research/sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.3.json"
SERVICE_REL="ops/systemd/sc001-b15p1-transferability-v0.1.3.service"
ROUTE_INDEX_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/directed_route_graph.v0.2.2.shard-index.json"
ADMITTED_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/ADMITTED.v0.2.2.json"
OFFLINE_RESULT_REL="docs/research/sc001-b15-p1-adapter-combined-offline-validation-result-v0.1.1.json"

PROBE="$REPO/$PROBE_REL"
FREEZE="$REPO/$FREEZE_REL"
ENV_FILE="/home/botmarket/.config/sc001/b15-p1.env"
OUT_DIR="/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY"
SNAPSHOT="$OUT_DIR/source_capability_snapshot.json"
SAFE_SUMMARY="$OUT_DIR/source_capability_safe_summary.json"
LOG="$OUT_DIR/source_capability_revalidation_v0.2.1_run.log"

EXPECTED_PROBE_SHA="dacaacd8563ec80d7f9f3006cc846795aa7e5e017518a817c962ee1dc7c1f1fe"
EXPECTED_FREEZE_SHA="943a10a5da9ca4334366c2266df26e672bbc76eb30ebcf976e6fa8b1a8b6d73c"
EXPECTED_PROTOCOL_SHA="ee0ea97aa848f6d8acac6b574f9b7a4cb5c2f4ed49bea04d96d7f52b96c49394"
EXPECTED_SPEC_SHA="9811fe0c10b9b4178376b7ce244936e9d00027ab4d6d234b9c8581cca75a00ef"
EXPECTED_RUNNER_SHA="f8181c4f25d6fc842d13c1faf8e259756883fcbb0bbcf08c23b3e60c9ed7bce0"
EXPECTED_IMPLEMENTATION_FREEZE_SHA="cdc6654ce5bbf265ce5cc5af2e448806ba306292d29fb986c7eb78bb1379df96"
EXPECTED_SERVICE_SHA="b59d61f25b4e643f6c9f27389d9829f7e4ea91cfbbb8dffeb48a91b55d755bf8"
EXPECTED_ROUTE_INDEX_SHA="001c89a7d4e973ed33ab072ec43746f6f7b6c0105912a24ae0483955ac93a50a"
EXPECTED_ROUTE_GRAPH_SHA="06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928"
EXPECTED_ADMITTED_SHA="fa9f97ab1e70b30bdb196fd6f4d49a8cbc7462d13424644ddb7b88cdd9f431b0"
EXPECTED_OFFLINE_RESULT_SHA="c9b2a2dfa193a596939627284a7221541452434cbab363b92dece4477c3d913a"

die() {
  echo "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_REVIEW"
  echo "reason=$1"
  echo "collector_launch_authorized=False"
  echo "price_data_used=False"
  echo "live_execution_authorized=False"
  exit 2
}

[[ "${EUID:-$(id -u)}" -eq 0 ]] || die "wrapper_must_run_as_root"

for cmd in sha256sum awk stat install sudo tee python3 find wc chown chmod; do
  command -v "$cmd" >/dev/null 2>&1 || die "required_command_missing:$cmd"
done

[[ -d "$REPO" ]] || die "repo_missing"
[[ -f "$ENV_FILE" ]] || die "credential_env_missing"
[[ ! -L "$ENV_FILE" ]] || die "credential_env_symlink_forbidden"

env_mode="$(stat -c '%a' "$ENV_FILE")"
[[ "$env_mode" == "600" ]] || die "credential_env_mode_not_0600"
sudo -u botmarket -H test -r "$ENV_FILE" || die "credential_env_not_readable_by_botmarket"

STAGE_FILES=(
  "$PROBE_REL"
  "$FREEZE_REL"
  "$PROTOCOL_REL"
  "$SPEC_REL"
  "$RUNNER_REL"
  "$IMPLEMENTATION_FREEZE_REL"
  "$SERVICE_REL"
  "$ROUTE_INDEX_REL"
  "$ADMITTED_REL"
  "$OFFLINE_RESULT_REL"
)

EXPECTED_SHAS=(
  "$EXPECTED_PROBE_SHA"
  "$EXPECTED_FREEZE_SHA"
  "$EXPECTED_PROTOCOL_SHA"
  "$EXPECTED_SPEC_SHA"
  "$EXPECTED_RUNNER_SHA"
  "$EXPECTED_IMPLEMENTATION_FREEZE_SHA"
  "$EXPECTED_SERVICE_SHA"
  "$EXPECTED_ROUTE_INDEX_SHA"
  "$EXPECTED_ADMITTED_SHA"
  "$EXPECTED_OFFLINE_RESULT_SHA"
)

[[ "${#STAGE_FILES[@]}" -eq "${#EXPECTED_SHAS[@]}" ]] || die "internal_stage_array_mismatch"

# Validate exact source bytes before staging. Keep GitHub Control clone isolation unchanged.
for i in "${!STAGE_FILES[@]}"; do
  rel="${STAGE_FILES[$i]}"
  expected="${EXPECTED_SHAS[$i]}"
  src="$REPO/$rel"
  [[ -f "$src" ]] || die "stage_source_missing:$rel"
  [[ ! -L "$src" ]] || die "stage_source_symlink_forbidden:$rel"
  actual="$(sha256sum "$src" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || die "source_sha_mismatch:$rel"
done

rm -rf "$STAGE"
install -d -m 0750 -o botmarket -g botmarket "$STAGE"

for i in "${!STAGE_FILES[@]}"; do
  rel="${STAGE_FILES[$i]}"
  expected="${EXPECTED_SHAS[$i]}"
  src="$REPO/$rel"
  dst="$STAGE/$rel"
  install -d -m 0750 -o botmarket -g botmarket "$(dirname "$dst")"
  install -m 0640 -o botmarket -g botmarket "$src" "$dst"
  actual="$(sha256sum "$dst" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || die "staged_sha_mismatch:$rel"
  sudo -u botmarket -H test -r "$dst" || die "staged_file_not_readable_by_botmarket:$rel"
done

[[ -z "$(find "$STAGE" -type l -print -quit)" ]] || die "staging_symlink_detected"
stage_file_count="$(find "$STAGE" -type f | wc -l | awk '{print $1}')"
[[ "$stage_file_count" == "${#STAGE_FILES[@]}" ]] || die "unexpected_staging_file_count:$stage_file_count"

STAGED_PROBE="$STAGE/$PROBE_REL"
STAGED_OFFLINE_RESULT="$STAGE/$OFFLINE_RESULT_REL"

# Re-check combined offline PASS before any exchange call.
python3 - "$STAGED_OFFLINE_RESULT" <<'PY'
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
obj = json.loads(p.read_text(encoding="utf-8"))
assert obj.get("status") == "B15P1_ADAPTER_COMBINED_OFFLINE_VALIDATION_PASS"
assert obj.get("bundle_id") == "bundle_20260924T163807Z_a5599568"
assert obj.get("job_id") == "job_20260924T170906Z_810905df"
assert obj.get("package_integrity_ok") is True
assert obj.get("exit_code") == 0
safety = obj.get("safety") or {}
for key in (
    "credentials_used",
    "exchange_calls_performed",
    "capability_snapshot_written",
    "collector_launch_authorized",
    "price_data_used",
    "pnl_data_used",
    "live_execution_authorized",
):
    assert safety.get(key) is False, key
print("offline_combined_prerequisite = PASS")
PY

install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"
rm -f "$SNAPSHOT" "$SAFE_SUMMARY"
: > "$LOG"
chown botmarket:botmarket "$LOG"
chmod 0640 "$LOG"

# This is the only live call boundary: the frozen probe runs as botmarket,
# with the protected 0600 credential file and only read-only/non-price endpoints.
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
  echo "price_data_used=False"
  echo "live_execution_authorized=False"
  exit "$rc"
fi

[[ -f "$SNAPSHOT" ]] || die "snapshot_missing_after_pass"
[[ ! -L "$SNAPSHOT" ]] || die "snapshot_symlink_forbidden"
[[ -f "$SAFE_SUMMARY" ]] || die "safe_summary_missing_after_pass"
[[ ! -L "$SAFE_SUMMARY" ]] || die "safe_summary_symlink_forbidden"

python3 - \
  "$SNAPSHOT" \
  "$SAFE_SUMMARY" \
  "$EXPECTED_PROBE_SHA" \
  "$EXPECTED_FREEZE_SHA" \
  "$EXPECTED_RUNNER_SHA" \
  "$EXPECTED_IMPLEMENTATION_FREEZE_SHA" \
  "$EXPECTED_SERVICE_SHA" \
  "$EXPECTED_ADMITTED_SHA" \
  "$EXPECTED_ROUTE_GRAPH_SHA" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

(
    snapshot_arg,
    summary_arg,
    expected_probe,
    expected_freeze,
    expected_runner,
    expected_implementation_freeze,
    expected_service,
    expected_admitted,
    expected_route_graph,
) = sys.argv[1:]

snapshot = Path(snapshot_arg)
summary = Path(summary_arg)
obj = json.loads(snapshot.read_text(encoding="utf-8"))
safe = json.loads(summary.read_text(encoding="utf-8"))

assert obj.get("schema") == "sc001.b15.p1_nonprice_source_capability_snapshot.v0.2.1"
assert obj.get("status") == "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"
assert obj.get("source_endpoints_pass") is True
assert obj.get("collector_launch_authorized") is False
assert obj.get("price_data_used") is False
assert obj.get("pnl_data_used") is False
assert obj.get("live_execution_authorized") is False

permissions = obj.get("permissions") or {}
assert permissions.get("bybit_readOnly") == 1
assert permissions.get("bybit_withdraw_token_present") is False
assert permissions.get("bybit_ip_bound") is True
assert permissions.get("okx_permission") == "read_only"
assert permissions.get("okx_ip_bound") is True

security = obj.get("security") or {}
for key in (
    "secret_values_printed",
    "price_endpoints_called",
    "order_endpoints_called",
    "transfer_endpoints_called",
    "withdrawal_endpoints_called",
):
    assert security.get(key) is False, key

anchors = obj.get("anchors") or {}
expected_anchors = {
    "capability_probe_sha256": expected_probe,
    "capability_freeze_sha256": expected_freeze,
    "runner_sha256": expected_runner,
    "implementation_freeze_sha256": expected_implementation_freeze,
    "service_file_sha256": expected_service,
    "admitted_universe_sha256": expected_admitted,
    "route_graph_sha256": expected_route_graph,
}
for key, expected in expected_anchors.items():
    assert anchors.get(key) == expected, (key, anchors.get(key), expected)

coverage = obj.get("pair_coverage") or {}
assert coverage.get("frozen_admitted_assets") == 192
assert int(coverage.get("qualified_bybit_count", 0)) > 0
assert int(coverage.get("qualified_okx_count", 0)) > 0
assert int(coverage.get("both_venues_count", 0)) > 0

fee_probe = obj.get("fee_endpoint_probe") or {}
assert fee_probe.get("pass") is True

adapter = obj.get("okx_adapter") or {}
assert adapter.get("get_currencies_feeCcy_optional") is True
assert adapter.get("trade_fee_primary_schema") == "feeGroup[]"
assert adapter.get("deprecated_top_level_fee_fields_fallback") is True

sha = hashlib.sha256(snapshot.read_bytes()).hexdigest()
assert safe.get("schema") == "sc001.b15.p1_nonprice_source_capability_safe_summary.v0.2.1"
assert safe.get("status") == "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"
assert safe.get("snapshot_sha256") == sha
assert safe.get("source_endpoints_pass") is True
assert safe.get("collector_launch_authorized") is False
assert safe.get("price_data_used") is False

print("snapshot_sha256 =", sha)
print("qualified_bybit_count =", coverage["qualified_bybit_count"])
print("qualified_okx_count =", coverage["qualified_okx_count"])
print("qualified_both_venues_count =", coverage["both_venues_count"])
print("fee_probe_asset =", fee_probe.get("asset"))
print("security_firewall = PASS")
PY

echo "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V021_PASS"
echo "snapshot=$SNAPSHOT"
echo "safe_summary=$SAFE_SUMMARY"
echo "log=$LOG"
echo "staging_root=$STAGE"
echo "collector_launch_authorized=False"
echo "price_data_used=False"
echo "pnl_data_used=False"
echo "live_execution_authorized=False"
