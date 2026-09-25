#!/usr/bin/env bash
set -euo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p1-collector-host-readiness-v0.1-stage"
OUT_DIR="/home/botmarket/sc001_data/SC001_B15P1_TRANSFERABILITY"
HOST_REPORT="$OUT_DIR/host_deployment_readiness_manifest.json"

SERVICE_NAME="sc001-b15p1-transferability.service"
RUNTIME_UNIT="/etc/systemd/system/$SERVICE_NAME"
ENV_FILE="/home/botmarket/.config/sc001/b15-p1.env"
SNAPSHOT="$OUT_DIR/source_capability_snapshot.json"
AUTH_FILE="$OUT_DIR/collector_launch_authorization.json"
STATE_FILE="$OUT_DIR/collector_state.json"
COLLECTOR_MANIFEST="$OUT_DIR/collector_manifest.json"

RUNNER_REL="research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_3.py"
LIBRARY_REL="research/sc001/sc001_b15p1_nonprice_transferability_lib_v0_1_3.py"
FREEZE_REL="docs/research/sc001-b15-p1-nonprice-collector-implementation-freeze-v0.1.3.json"
CONTRACT_REL="docs/research/sc001-b15-p1-nonprice-collector-implementation-contract-v0.1.3.json"
PROTOCOL_REL="docs/research/sc001-b15-p1-15-second-nonprice-collector-protocol-v0.1.md"
DESIGN_REL="docs/research/sc001-b15-p1-15-second-nonprice-collector-design-candidate-v0.1.json"
DESIGN_SPEC_REL="docs/research/sc001-b15-p1-15-second-nonprice-collector-design-preflight-spec-v0.1.json"
RATE_EVIDENCE_REL="docs/research/sc001-b15-p1-nonprice-collector-rate-limit-evidence-v0.1.json"
DESIGN_MANIFEST_REL="docs/research/artifacts/b15-p1-collector-design/20260924T103023Z/collector_design_preflight_manifest.json"
SEMANTICS_REL="docs/research/sc001-b15-p1-nonprice-collector-implementation-semantics-v0.2.md"
RAW_STORAGE_REL="docs/research/sc001-b15-p1-collector-raw-storage-amendment-v0.1.md"
BASE_ADMITTED_REL="docs/research/artifacts/b15-p1-canonical-freeze/20260920T210446Z/ADMITTED.json"
FINAL_RESOLVED_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/replay/integrated_replay_resolved_rows_v0.2.2.json"
FINAL_DISPOSITIONS_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/replay/integrated_replay_asset_dispositions_v0.2.2.json"
FINAL_QUOTE_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-preflight/identity_route_v0.2.2_final_quote_classification.json"
FREEZE_SUPPLEMENT_REL="docs/research/sc001-b15-p1-v0.2.2-final-freeze-artifact-supplement-v1.json"
ROUTE_INDEX_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/directed_route_graph.v0.2.2.shard-index.json"
SERVICE_REL="ops/systemd/sc001-b15p1-transferability-v0.1.3.service"
STATUS_HELPER_REL="ops/systemd/sc001_b15p1_transferability_status.sh"
PRELAUNCH_RESULT_REL="docs/research/sc001-b15-p1-collector-prelaunch-readiness-result-v0.1.json"
LIVE_RESULT_REL="docs/research/sc001-b15-p1-live-source-capability-revalidation-v0.2.1-result-v0.1.json"

EXPECTED_RUNNER_SHA="f8181c4f25d6fc842d13c1faf8e259756883fcbb0bbcf08c23b3e60c9ed7bce0"
EXPECTED_LIBRARY_SHA="f4e27edff5acb38fb1c9ee840490179d1c3ebe13fd258d8875de768acc4078b5"
EXPECTED_FREEZE_SHA="cdc6654ce5bbf265ce5cc5af2e448806ba306292d29fb986c7eb78bb1379df96"
EXPECTED_CONTRACT_SHA="e584f07e024aa972cb9fe49881b016931b2e0e51acaa56fece3440cef869357f"
EXPECTED_PROTOCOL_SHA="2d4f65c1ddd13ee0fbafb76734ce266fb933404ad24394ac707b246613613563"
EXPECTED_DESIGN_SHA="ea42cbd5a2f14061d3bd66aafbda7ccf79f6afa85a5c90c3defe8c2ba952889e"
EXPECTED_DESIGN_SPEC_SHA="cb56417ab12fe1e46b5202eca550fee505755b6df759ffd9349ffaef6d4cc0bc"
EXPECTED_RATE_EVIDENCE_SHA="80ff38757742b8ffded028533d190be6a7f84de82fa7fcf9fb335007965a8613"
EXPECTED_DESIGN_MANIFEST_SHA="5066d1e91e6b8e122ef1289a35b1747f18a2e68cc3692d8e4c999692db8a03a9"
EXPECTED_SEMANTICS_SHA="b260ce101624edacad74badc2d9a4158dc4c074550e8603b06b88ff676af5b70"
EXPECTED_RAW_STORAGE_SHA="24a650478914c13e8c6afdd3780cac2ec3da5965a4b48a9ea7f2546299593f4d"
EXPECTED_BASE_ADMITTED_SHA="4125dd9577a3493b0242b9f79db5da1db780d45bd9dd90acad5dffa78bc90bc5"
EXPECTED_FINAL_RESOLVED_SHA="58fed2f8a317b72bad2680c70e51c83a6c1a70f93064930cd7857cb014979d6c"
EXPECTED_FINAL_DISPOSITIONS_SHA="b8bdb5df6ce388b67d8f2f48a8ef430d205c0cec88fb28b1b25a287d2bb99dc2"
EXPECTED_FINAL_QUOTE_SHA="ad8434a8b1f2c00b4eae3f690427ac05431cc9aab04631d9438b4a238d483520"
EXPECTED_FREEZE_SUPPLEMENT_SHA="6241a66f93dfcbd74d2ea8c3ac164c746f87236d653895b8cbf01ce348913997"
EXPECTED_ROUTE_INDEX_SHA="001c89a7d4e973ed33ab072ec43746f6f7b6c0105912a24ae0483955ac93a50a"
EXPECTED_ROUTE_GRAPH_SHA="06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928"
EXPECTED_SERVICE_SHA="b59d61f25b4e643f6c9f27389d9829f7e4ea91cfbbb8dffeb48a91b55d755bf8"
EXPECTED_STATUS_HELPER_SHA="e26c6707ac38ae2d4bd61e2e31b9197d492f6d43e01d0436e301a284279b1702"
EXPECTED_PRELAUNCH_RESULT_SHA="0396aedc678a6094fb73a675ba9a1446c501cb2871f220a03387d0df38d653bd"
EXPECTED_LIVE_RESULT_SHA="61fb470c4d0c795adf31a36fff8da34157caa86824efeb8521373a5bf1584ff1"
EXPECTED_SNAPSHOT_SHA="14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc"

die() {
  echo "B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_REVIEW"
  echo "reason=$1"
  echo "collector_start_performed=False"
  echo "systemd_mutation_performed=False"
  echo "runtime_authorization_created=False"
  exit 2
}

[[ "${EUID:-$(id -u)}" -eq 0 ]] || die "wrapper_must_run_as_root"

for cmd in sha256sum awk stat install sudo python3 find wc systemctl systemd-analyze pgrep; do
  command -v "$cmd" >/dev/null 2>&1 || die "required_command_missing:$cmd"
done

[[ -d "$REPO" ]] || die "github_control_repo_missing"
[[ -f "$SNAPSHOT" ]] || die "live_capability_snapshot_missing"
[[ ! -L "$SNAPSHOT" ]] || die "live_capability_snapshot_symlink_forbidden"
snapshot_sha="$(sha256sum "$SNAPSHOT" | awk '{print $1}')"
[[ "$snapshot_sha" == "$EXPECTED_SNAPSHOT_SHA" ]] || die "live_capability_snapshot_sha_mismatch"

[[ -f "$ENV_FILE" ]] || die "credential_env_missing"
[[ ! -L "$ENV_FILE" ]] || die "credential_env_symlink_forbidden"
env_mode="$(stat -c '%a' "$ENV_FILE")"
env_owner="$(stat -c '%U:%G' "$ENV_FILE")"
[[ "$env_mode" == "600" ]] || die "credential_env_mode_not_0600"
[[ "$env_owner" == "botmarket:botmarket" ]] || die "credential_env_owner_mismatch:$env_owner"
sudo -u botmarket -H test -r "$ENV_FILE" || die "credential_env_not_readable_by_botmarket"

[[ ! -e "$AUTH_FILE" ]] || die "active_runtime_launch_authorization_already_present"
[[ ! -e "$STATE_FILE" ]] || die "collector_state_already_present"
[[ ! -e "$COLLECTOR_MANIFEST" ]] || die "collector_manifest_already_present"

if pgrep -f 'sc001_b15p1_nonprice_transferability_collector_v0_1_3[.]py' >/dev/null 2>&1; then
  die "collector_process_already_running"
fi

active_state="$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || true)"
enabled_state="$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || true)"
case "$active_state" in
  inactive|unknown|"") ;;
  *) die "stable_service_not_inactive:$active_state" ;;
esac
case "$enabled_state" in
  disabled|not-found|"") ;;
  *) die "stable_service_not_disabled:$enabled_state" ;;
esac

if [[ -e "$RUNTIME_UNIT" ]]; then
  [[ -f "$RUNTIME_UNIT" ]] || die "runtime_unit_not_regular_file"
  [[ ! -L "$RUNTIME_UNIT" ]] || die "runtime_unit_symlink_forbidden"
  runtime_unit_sha="$(sha256sum "$RUNTIME_UNIT" | awk '{print $1}')"
  [[ "$runtime_unit_sha" == "$EXPECTED_SERVICE_SHA" ]] || die "runtime_unit_sha_mismatch:$runtime_unit_sha"
else
  runtime_unit_sha="ABSENT"
fi

show_text="$(systemctl show "$SERVICE_NAME" -p LoadState -p FragmentPath -p DropInPaths 2>/dev/null || true)"
if printf '%s\n' "$show_text" | grep -Eq '^DropInPaths=.+$'; then
  die "stable_service_dropins_present"
fi

STAGE_FILES=(
  "$RUNNER_REL"
  "$LIBRARY_REL"
  "$FREEZE_REL"
  "$CONTRACT_REL"
  "$PROTOCOL_REL"
  "$DESIGN_REL"
  "$DESIGN_SPEC_REL"
  "$RATE_EVIDENCE_REL"
  "$DESIGN_MANIFEST_REL"
  "$SEMANTICS_REL"
  "$RAW_STORAGE_REL"
  "$BASE_ADMITTED_REL"
  "$FINAL_RESOLVED_REL"
  "$FINAL_DISPOSITIONS_REL"
  "$FINAL_QUOTE_REL"
  "$FREEZE_SUPPLEMENT_REL"
  "$ROUTE_INDEX_REL"
  "$SERVICE_REL"
  "$STATUS_HELPER_REL"
  "$PRELAUNCH_RESULT_REL"
  "$LIVE_RESULT_REL"
)

EXPECTED_SHAS=(
  "$EXPECTED_RUNNER_SHA"
  "$EXPECTED_LIBRARY_SHA"
  "$EXPECTED_FREEZE_SHA"
  "$EXPECTED_CONTRACT_SHA"
  "$EXPECTED_PROTOCOL_SHA"
  "$EXPECTED_DESIGN_SHA"
  "$EXPECTED_DESIGN_SPEC_SHA"
  "$EXPECTED_RATE_EVIDENCE_SHA"
  "$EXPECTED_DESIGN_MANIFEST_SHA"
  "$EXPECTED_SEMANTICS_SHA"
  "$EXPECTED_RAW_STORAGE_SHA"
  "$EXPECTED_BASE_ADMITTED_SHA"
  "$EXPECTED_FINAL_RESOLVED_SHA"
  "$EXPECTED_FINAL_DISPOSITIONS_SHA"
  "$EXPECTED_FINAL_QUOTE_SHA"
  "$EXPECTED_FREEZE_SUPPLEMENT_SHA"
  "$EXPECTED_ROUTE_INDEX_SHA"
  "$EXPECTED_SERVICE_SHA"
  "$EXPECTED_STATUS_HELPER_SHA"
  "$EXPECTED_PRELAUNCH_RESULT_SHA"
  "$EXPECTED_LIVE_RESULT_SHA"
)

[[ "${#STAGE_FILES[@]}" -eq "${#EXPECTED_SHAS[@]}" ]] || die "internal_stage_array_mismatch"

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

STAGED_RUNNER="$STAGE/$RUNNER_REL"
STAGED_LIBRARY="$STAGE/$LIBRARY_REL"
STAGED_SERVICE="$STAGE/$SERVICE_REL"
STAGED_SELFTEST_OUTPUT="$STAGE/output/implementation_self_test_manifest.json"
STAGED_STABLE_UNIT="$STAGE/runtime/$SERVICE_NAME"

install -d -m 0750 -o botmarket -g botmarket "$(dirname "$STAGED_STABLE_UNIT")" "$STAGE/output"
install -m 0640 -o botmarket -g botmarket "$STAGED_SERVICE" "$STAGED_STABLE_UNIT"
stable_stage_sha="$(sha256sum "$STAGED_STABLE_UNIT" | awk '{print $1}')"
[[ "$stable_stage_sha" == "$EXPECTED_SERVICE_SHA" ]] || die "staged_stable_unit_sha_mismatch"

systemd-analyze verify "$STAGED_STABLE_UNIT" >/dev/null 2>"$STAGE/systemd_verify.stderr" || {
  cat "$STAGE/systemd_verify.stderr" >&2 || true
  die "systemd_analyze_verify_failed"
}

sudo -u botmarket -H env -i \
  HOME=/home/botmarket \
  PATH=/usr/bin:/bin \
  B15P1_REPO_ROOT="$STAGE" \
  B15P1_SELFTEST_OUTPUT="$STAGED_SELFTEST_OUTPUT" \
  /usr/bin/python3 -m py_compile "$STAGED_RUNNER" "$STAGED_LIBRARY" || die "staged_python_compile_failed"

set +e
selftest_stdout="$(
  sudo -u botmarket -H env -i \
    HOME=/home/botmarket \
    PATH=/usr/bin:/bin \
    B15P1_REPO_ROOT="$STAGE" \
    B15P1_SELFTEST_OUTPUT="$STAGED_SELFTEST_OUTPUT" \
    /usr/bin/python3 "$STAGED_RUNNER" --mode self-test 2>&1
)"
selftest_rc="$?"
set -e
printf '%s\n' "$selftest_stdout"
[[ "$selftest_rc" -eq 0 ]] || die "staged_collector_selftest_failed:$selftest_rc"
printf '%s\n' "$selftest_stdout" | grep -q '^B15P1_NONPRICE_COLLECTOR_V013_SELF_TEST_PASS$' || die "staged_collector_selftest_pass_token_missing"

python3 - \
  "$SNAPSHOT" \
  "$STAGED_SELFTEST_OUTPUT" \
  "$STAGE/$PRELAUNCH_RESULT_REL" \
  "$STAGE/$LIVE_RESULT_REL" \
  "$EXPECTED_SNAPSHOT_SHA" \
  "$EXPECTED_RUNNER_SHA" \
  "$EXPECTED_LIBRARY_SHA" \
  "$EXPECTED_FREEZE_SHA" \
  "$EXPECTED_SERVICE_SHA" \
  "$EXPECTED_ROUTE_GRAPH_SHA" \
  "$HOST_REPORT" \
  "$active_state" \
  "$enabled_state" \
  "$runtime_unit_sha" <<'PY'
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

(
    snapshot_arg,
    selftest_arg,
    prelaunch_arg,
    live_result_arg,
    expected_snapshot_sha,
    expected_runner_sha,
    expected_library_sha,
    expected_freeze_sha,
    expected_service_sha,
    expected_route_graph_sha,
    host_report_arg,
    active_state,
    enabled_state,
    runtime_unit_sha,
) = sys.argv[1:]

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

snapshot = load(snapshot_arg)
selftest = load(selftest_arg)
prelaunch = load(prelaunch_arg)
live_result = load(live_result_arg)

assert sha(snapshot_arg) == expected_snapshot_sha
assert snapshot.get("schema") == "sc001.b15.p1_nonprice_source_capability_snapshot.v0.2.1"
assert snapshot.get("status") == "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"
assert snapshot.get("source_endpoints_pass") is True
assert snapshot.get("collector_launch_authorized") is False
assert snapshot.get("price_data_used") is False
assert snapshot.get("pnl_data_used") is False
assert snapshot.get("live_execution_authorized") is False

anchors = snapshot.get("anchors") or {}
assert anchors.get("runner_sha256") == expected_runner_sha
assert anchors.get("implementation_freeze_sha256") == expected_freeze_sha
assert anchors.get("service_file_sha256") == expected_service_sha
assert anchors.get("route_graph_sha256") == expected_route_graph_sha

permissions = snapshot.get("permissions") or {}
assert permissions.get("bybit_readOnly") == 1
assert permissions.get("bybit_withdraw_token_present") is False
assert permissions.get("bybit_ip_bound") is True
assert permissions.get("okx_permission") == "read_only"
assert permissions.get("okx_ip_bound") is True

security = snapshot.get("security") or {}
for key in (
    "secret_values_printed",
    "price_endpoints_called",
    "order_endpoints_called",
    "transfer_endpoints_called",
    "withdrawal_endpoints_called",
):
    assert security.get(key) is False, key

coverage = snapshot.get("pair_coverage") or {}
assert coverage.get("frozen_admitted_assets") == 192
assert coverage.get("qualified_bybit_count") == 192
assert coverage.get("qualified_okx_count") == 192
assert coverage.get("both_venues_count") == 192

assert selftest.get("status") == "B15P1_NONPRICE_COLLECTOR_V013_SELF_TEST_PASS"
assert selftest.get("runner_sha256") == expected_runner_sha
assert selftest.get("library_sha256") == expected_library_sha
assert selftest.get("implementation_freeze_sha256") == expected_freeze_sha
assert selftest.get("exchange_calls_performed") is False
assert selftest.get("collector_launch_authorized") is False
assert selftest.get("price_data_authorized") is False
assert selftest.get("pnl_data_authorized") is False
mandatory = selftest.get("mandatory_tests") or []
results = selftest.get("test_results") or {}
assert len(mandatory) == 28
assert all(results.get(name) is True for name in mandatory)

assert prelaunch.get("status") == "B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE_PASS"
assert prelaunch.get("live_snapshot_sha256") == expected_snapshot_sha
assert prelaunch.get("safety", {}).get("collector_start_performed") is False
assert prelaunch.get("safety", {}).get("runtime_authorization_created") is False

assert live_result.get("status") == "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_COMMAND_V021_PASS"
assert (live_result.get("snapshot") or {}).get("sha256") == expected_snapshot_sha

report = {
    "schema": "sc001.b15.p1_collector_host_deployment_readiness.v0.1",
    "status": "B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_PASS",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "live_snapshot_sha256": expected_snapshot_sha,
    "collector_runner_sha256": expected_runner_sha,
    "collector_library_sha256": expected_library_sha,
    "implementation_freeze_sha256": expected_freeze_sha,
    "service_candidate_sha256": expected_service_sha,
    "runtime_service_active_state": active_state,
    "runtime_service_enabled_state": enabled_state,
    "runtime_unit_sha256_or_absent": runtime_unit_sha,
    "credential_env_mode": "0600",
    "credential_env_owner": "botmarket:botmarket",
    "active_runtime_launch_authorization_present": False,
    "collector_state_present": False,
    "collector_manifest_present": False,
    "staged_selftest_status": selftest.get("status"),
    "staged_mandatory_test_count": len(mandatory),
    "systemd_analyze_verify": "PASS",
    "collector_start_performed": False,
    "systemd_start_enable_performed": False,
    "runtime_authorization_created": False,
    "exchange_calls_performed_by_readiness_wrapper": False,
    "price_data_used": False,
    "pnl_data_used": False,
    "live_execution_performed": False,
    "next_state": "AWAIT_EXPLICIT_APPROVAL_FOR_FINAL_COLLECTOR_DEPLOYMENT_AUTHORIZATION_AND_START",
}
out = Path(host_report_arg)
out.parent.mkdir(parents=True, exist_ok=True)
tmp = out.with_name(out.name + ".tmp")
tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
os.chmod(tmp, 0o640)
os.replace(tmp, out)

print("snapshot_contract = PASS")
print("staged_collector_selftest = PASS")
print("host_report_sha256 =", sha(out))
PY

echo "B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_PASS"
echo "live_snapshot_sha256=$snapshot_sha"
echo "stable_service_active=$active_state"
echo "stable_service_enabled=$enabled_state"
echo "runtime_unit_sha256_or_absent=$runtime_unit_sha"
echo "staging_root=$STAGE"
echo "host_report=$HOST_REPORT"
echo "collector_start_performed=False"
echo "systemd_start_enable_performed=False"
echo "runtime_authorization_created=False"
