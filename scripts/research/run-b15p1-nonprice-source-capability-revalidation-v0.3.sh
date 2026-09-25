#!/usr/bin/env bash
set -euo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p1-capability-revalidation-v0.2.2-stage"

PROBE_REL="research/sc001/sc001_b15p1_nonprice_source_capability_revalidation_v0_2_2.py"
FREEZE_REL="docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-freeze-v0.2.2.json"
PROTOCOL_REL="docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-v0.2.md"
SPEC_REL="docs/research/sc001-b15-p1-nonprice-source-capability-revalidation-spec-v0.2.2.json"
RUNNER_REL="research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_4.py"
IMPLEMENTATION_FREEZE_REL="docs/research/sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.4.json"
SERVICE_REL="ops/systemd/sc001-b15p1-transferability-v0.1.4.service"
ROUTE_INDEX_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/directed_route_graph.v0.2.2.shard-index.json"
ADMITTED_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/ADMITTED.v0.2.2.json"
LIBRARY_REL="research/sc001/sc001_b15p1_nonprice_transferability_lib_v0_1_4.py"
PROBE_HARNESS_REL="research/sc001/sc001_b15p1_nonprice_source_capability_selftest_harness_v0_2_2.py"
COLLECTOR_RESULT_REL="docs/research/sc001-b15-p1-nonprice-collector-v0.1.4-offline-selftest-result-v0.1.json"
BINDING_CORRECTION_REL="docs/research/sc001-b15-p1-source-capability-v0.2.2-v014-binding-correction-v0.1.json"
SOURCE_DIAGNOSTIC_REL="docs/research/sc001-b15-p1-final-launch-v0.1.1-host-attempt-v0.1-diagnostic.json"
CREDENTIAL_SECURITY_REL="docs/research/sc001-b15-p1-read-only-credential-security-contract-v0.1.md"

PROBE="$REPO/$PROBE_REL"
FREEZE="$REPO/$FREEZE_REL"
ENV_FILE="/home/botmarket/.config/sc001/b15-p1.env"
OUT_DIR="/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY"
SNAPSHOT="$OUT_DIR/source_capability_snapshot.json"
SAFE_SUMMARY="$OUT_DIR/source_capability_safe_summary.json"
LOG="$OUT_DIR/source_capability_revalidation_v0.2.2_run.log"

EXPECTED_PROBE_SHA="76f6ebd17ed2ad5a1fb8c3fad153c51fdcbaa6eab791cba37dcf3706b5820e12"
EXPECTED_FREEZE_SHA="a783bbf7e7598846f20a04b555e8c40e3c9cc15a3afc949a2f11cddb4a9341b6"
EXPECTED_PROTOCOL_SHA="ee0ea97aa848f6d8acac6b574f9b7a4cb5c2f4ed49bea04d96d7f52b96c49394"
EXPECTED_SPEC_SHA="22920f915837d56ab5c8808badd5b94b3bdea77e018f633395950fd44e4ef062"
EXPECTED_RUNNER_SHA="280253b060f65517548054b3d8c33c315013d724ef2b836e9b8fef14628be213"
EXPECTED_LIBRARY_SHA="eaa925b71a7f33ec59de69f32dd0fb06f85bac67e89101b6f2ad50c1d792fd3f"
EXPECTED_IMPLEMENTATION_FREEZE_SHA="80928b0a11dac333b7844aa15bcdf399fd4db8739a4845e6118ebb576153b38c"
EXPECTED_SERVICE_SHA="7a0f1742481b92f4d2590f09defcc5b287baaf1a9ba50f0da27488f8f5272f9d"
EXPECTED_ROUTE_INDEX_SHA="001c89a7d4e973ed33ab072ec43746f6f7b6c0105912a24ae0483955ac93a50a"
EXPECTED_ROUTE_GRAPH_SHA="06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928"
EXPECTED_ADMITTED_SHA="fa9f97ab1e70b30bdb196fd6f4d49a8cbc7462d13424644ddb7b88cdd9f431b0"
EXPECTED_PROBE_HARNESS_SHA="dfbd0550f2904f4485e250badb3e0c925d9b2cd8f22fef3f85aee7648432dfab"
EXPECTED_COLLECTOR_RESULT_SHA="7cb9aa17fc820fe5bd88507614d273b52e442435de1e191b559053422b8c0c2c"
EXPECTED_BINDING_CORRECTION_SHA="1148da1b917f59992506343b69ab76e64e4fc10344fdbd4184308ef078040268"
EXPECTED_SOURCE_DIAGNOSTIC_SHA="66ed3abc5257eb8c1d378ed448be66f4600175c56efcc3ebbf8d9c880386a27b"
EXPECTED_CREDENTIAL_SECURITY_SHA="a670dab6dedd4dcf65e47f03b4fa2dcd38ca977954e8c5b18242fee31a6e2432"

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
  "$LIBRARY_REL"
  "$IMPLEMENTATION_FREEZE_REL"
  "$SERVICE_REL"
  "$ROUTE_INDEX_REL"
  "$ADMITTED_REL"
  "$PROBE_HARNESS_REL"
  "$COLLECTOR_RESULT_REL"
  "$BINDING_CORRECTION_REL"
  "$SOURCE_DIAGNOSTIC_REL"
  "$CREDENTIAL_SECURITY_REL"
)

EXPECTED_SHAS=(
  "$EXPECTED_PROBE_SHA"
  "$EXPECTED_FREEZE_SHA"
  "$EXPECTED_PROTOCOL_SHA"
  "$EXPECTED_SPEC_SHA"
  "$EXPECTED_RUNNER_SHA"
  "$EXPECTED_LIBRARY_SHA"
  "$EXPECTED_IMPLEMENTATION_FREEZE_SHA"
  "$EXPECTED_SERVICE_SHA"
  "$EXPECTED_ROUTE_INDEX_SHA"
  "$EXPECTED_ADMITTED_SHA"
  "$EXPECTED_PROBE_HARNESS_SHA"
  "$EXPECTED_COLLECTOR_RESULT_SHA"
  "$EXPECTED_BINDING_CORRECTION_SHA"
  "$EXPECTED_SOURCE_DIAGNOSTIC_SHA"
  "$EXPECTED_CREDENTIAL_SECURITY_SHA"
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
STAGED_COLLECTOR_RESULT="$STAGE/$COLLECTOR_RESULT_REL"

# Re-check collector v0.1.4 offline PASS and capability v0.2.2 self-test
# from the exact staged bytes before any exchange call.
python3 - "$STAGED_COLLECTOR_RESULT" "$EXPECTED_RUNNER_SHA" "$EXPECTED_LIBRARY_SHA" "$EXPECTED_IMPLEMENTATION_FREEZE_SHA" <<'PY'
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
expected_runner, expected_library, expected_freeze = sys.argv[2:]
obj = json.loads(p.read_text(encoding="utf-8"))
assert obj.get("status") == "B15P1_NONPRICE_COLLECTOR_V014_COMPILE_AND_SELFTEST_PASS"
assert obj.get("package_integrity_ok") is True
assert obj.get("exit_code") == 0
assert obj.get("mandatory_test_count") == 32
assert obj.get("all_mandatory_tests_passed") is True
assert obj.get("runner_sha256") == expected_runner
assert obj.get("library_sha256") == expected_library
assert obj.get("implementation_freeze_sha256") == expected_freeze
safety = obj.get("safety") or {}
for key in (
    "exchange_calls_performed",
    "collector_launch_authorized",
    "price_data_authorized",
    "pnl_data_authorized",
    "live_execution_authorized",
):
    assert safety.get(key) is False, key
print("collector_v014_offline_prerequisite = PASS")
PY

if probe_selftest_out="$(
  sudo -u botmarket -H env -i     HOME=/home/botmarket     PATH=/usr/bin:/bin     B15P1_REPO_ROOT="$STAGE"     /usr/bin/python3 "$STAGED_PROBE" --mode self-test 2>&1
)"; then
  probe_selftest_rc=0
else
  probe_selftest_rc="$?"
fi
printf '%s
' "$probe_selftest_out"
[[ "$probe_selftest_rc" -eq 0 ]] || die "staged_capability_v022_selftest_failed:$probe_selftest_rc"
printf '%s
' "$probe_selftest_out" | grep -q '^B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_V022_SELF_TEST_PASS$' || die "staged_capability_v022_selftest_pass_token_missing"
echo "staged_capability_v022_selftest = PASS"
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
  "$EXPECTED_LIBRARY_SHA" \
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
    expected_library,
    expected_implementation_freeze,
    expected_service,
    expected_admitted,
    expected_route_graph,
) = sys.argv[1:]

snapshot = Path(snapshot_arg)
summary = Path(summary_arg)
obj = json.loads(snapshot.read_text(encoding="utf-8"))
safe = json.loads(summary.read_text(encoding="utf-8"))

assert obj.get("schema") == "sc001.b15.p1_nonprice_source_capability_snapshot.v0.2.2"
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
    "library_sha256": expected_library,
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

bybit_adapter = obj.get("bybit_adapter") or {}
assert bybit_adapter.get("collector_parser_version") == "0.1.4"
assert bybit_adapter.get("parser_compatible") is True
assert bybit_adapter.get("withdrawMax_minus_one_semantics") == "UNLIMITED"
assert int(bybit_adapter.get("parsed_chain_rows", 0)) > 0
assert int(bybit_adapter.get("raw_withdrawMax_minus_one_rows", -1)) == int(bybit_adapter.get("normalized_unlimited_rows", -2))

adapter = obj.get("okx_adapter") or {}
assert adapter.get("get_currencies_feeCcy_optional") is True
assert adapter.get("trade_fee_primary_schema") == "feeGroup[]"
assert adapter.get("deprecated_top_level_fee_fields_fallback") is True

sha = hashlib.sha256(snapshot.read_bytes()).hexdigest()
assert safe.get("schema") == "sc001.b15.p1_nonprice_source_capability_safe_summary.v0.2.2"
assert safe.get("status") == "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"
assert safe.get("snapshot_sha256") == sha
assert safe.get("source_endpoints_pass") is True
safe_bybit = safe.get("bybit_adapter") or {}
assert safe_bybit.get("collector_parser_version") == "0.1.4"
assert safe_bybit.get("parser_compatible") is True
assert safe.get("collector_launch_authorized") is False
assert safe.get("price_data_used") is False

print("snapshot_sha256 =", sha)
print("qualified_bybit_count =", coverage["qualified_bybit_count"])
print("qualified_okx_count =", coverage["qualified_okx_count"])
print("qualified_both_venues_count =", coverage["both_venues_count"])
print("fee_probe_asset =", fee_probe.get("asset"))
print("bybit_parser_v014_compatible =", bybit_adapter["parser_compatible"])
print("bybit_withdrawMax_minus_one_rows =", bybit_adapter["raw_withdrawMax_minus_one_rows"])
print("bybit_normalized_unlimited_rows =", bybit_adapter["normalized_unlimited_rows"])
print("security_firewall = PASS")
PY

echo "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V022_PASS"
echo "snapshot=$SNAPSHOT"
echo "safe_summary=$SAFE_SUMMARY"
echo "log=$LOG"
echo "staging_root=$STAGE"
echo "collector_launch_authorized=False"
echo "price_data_used=False"
echo "pnl_data_used=False"
echo "live_execution_authorized=False"
