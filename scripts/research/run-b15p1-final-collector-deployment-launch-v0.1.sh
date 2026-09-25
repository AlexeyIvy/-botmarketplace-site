#!/usr/bin/env bash
set -eEuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p1-final-launch-v0.1-stage"
RUNTIME_ROOT="/home/botmarket/botmarketplace-site"
BACKUP_ROOT="/home/botmarket/.local/share/botmarket/b15p1-final-launch-v0.1-backup"
DATA_ROOT="/home/botmarket/sc001_data"
OUT_DIR="$DATA_ROOT/SC001_B15P1_TRANSFERABILITY"

SERVICE_NAME="sc001-b15p1-transferability.service"
RUNTIME_UNIT="/etc/systemd/system/$SERVICE_NAME"
ENV_FILE="/home/botmarket/.config/sc001/b15-p1.env"
SNAPSHOT="$OUT_DIR/source_capability_snapshot.json"
AUTH_FILE="$OUT_DIR/collector_launch_authorization.json"
STATE_FILE="$OUT_DIR/collector_state.json"
MANIFEST_FILE="$OUT_DIR/collector_manifest.json"
HOST_REPORT="$OUT_DIR/host_deployment_readiness_manifest.json"
SYSTEMD_LOG="$OUT_DIR/systemd.log"
LAUNCH_REPORT="$OUT_DIR/collector_launch_verification_manifest.json"

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
CANDIDATE_REL="docs/research/sc001-b15-p1-collector-launch-authorization-candidate-v0.1.json"
PRELAUNCH_RESULT_REL="docs/research/sc001-b15-p1-collector-prelaunch-readiness-result-v0.1.json"
POST_REBOOT_RESULT_REL="docs/research/sc001-b15-p1-collector-host-deployment-readiness-post-reboot-result-v0.1.json"

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
EXPECTED_CANDIDATE_SHA="70fe8764adcc3aa9f0d2ef8826c2edabe9eaeaf7fa40192782bbea624d5681cd"
EXPECTED_PRELAUNCH_RESULT_SHA="0396aedc678a6094fb73a675ba9a1446c501cb2871f220a03387d0df38d653bd"
EXPECTED_POST_REBOOT_RESULT_SHA="155c98d7fc021ac15eef0b23f0129ecc436bcc2a91a75b817ad2363be6815d73"
EXPECTED_HOST_REPORT_SHA="e249f824a4b10f19a81aa6e01f1f5d7beee5088997880b146378f73f676d7aee"
EXPECTED_SNAPSHOT_SHA="14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc"
EXPECTED_AUTH_SHA="fd5b9a6c683bd15df2dfc26c4ba6497d8e8e152d9b70ed1dc1edeab5107f13be"

MUTATION_STARTED=0
AUTH_CREATED=0
UNIT_INSTALLED=0
SERVICE_ENABLED=0
SERVICE_STARTED=0
UNIT_WAS_PRESENT=0
FAIL_HANDLED=0
SUCCESS=0

rollback() {
  set +e
  if [[ "$MUTATION_STARTED" -eq 1 ]]; then
    # Always attempt stop/disable after mutation starts. This also covers
    # partial side effects if systemctl returns an error before local flags update.
    systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true
    systemctl disable "$SERVICE_NAME" >/dev/null 2>&1 || true
    if [[ "$AUTH_CREATED" -eq 1 && -f "$AUTH_FILE" ]]; then
      auth_sha_now="$(sha256sum "$AUTH_FILE" 2>/dev/null | awk '{print $1}')"
      if [[ "$auth_sha_now" == "$EXPECTED_AUTH_SHA" ]]; then
        rm -f "$AUTH_FILE"
      fi
    fi
    if [[ "$UNIT_INSTALLED" -eq 1 && "$UNIT_WAS_PRESENT" -eq 0 && -f "$RUNTIME_UNIT" ]]; then
      unit_sha_now="$(sha256sum "$RUNTIME_UNIT" 2>/dev/null | awk '{print $1}')"
      if [[ "$unit_sha_now" == "$EXPECTED_SERVICE_SHA" ]]; then
        rm -f "$RUNTIME_UNIT"
        systemctl daemon-reload >/dev/null 2>&1 || true
      fi
    fi
  fi
  set -e
}

fail() {
  local reason="$1"
  FAIL_HANDLED=1
  if [[ "$MUTATION_STARTED" -eq 1 && -f "$SYSTEMD_LOG" ]]; then
    echo "===== B15P1 recent systemd log before rollback =====" >&2
    tail -n 40 "$SYSTEMD_LOG" >&2 || true
  fi
  rollback
  echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_REVIEW"
  echo "reason=$reason"
  echo "collector_may_have_failure_evidence=True"
  echo "price_pnl_authorized=False"
  exit 2
}

on_err() {
  local rc="$?"
  local line="$1"
  if [[ "$SUCCESS" -ne 1 && "$FAIL_HANDLED" -ne 1 ]]; then
    rollback
    echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_REVIEW"
    echo "reason=unexpected_shell_error:line=$line:rc=$rc"
    echo "collector_may_have_failure_evidence=True"
    echo "price_pnl_authorized=False"
  fi
  exit "$rc"
}
trap 'on_err $LINENO' ERR

[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "wrapper_must_run_as_root"

for cmd in sha256sum awk stat install sudo python3 find wc systemctl systemd-analyze pgrep date grep tail sleep mkdir rm cp seq cat env; do
  command -v "$cmd" >/dev/null 2>&1 || fail "required_command_missing:$cmd"
done

[[ -d "$REPO" ]] || fail "github_control_repo_missing"
[[ -d "$RUNTIME_ROOT" ]] || fail "runtime_root_missing"
[[ ! -L "$RUNTIME_ROOT" ]] || fail "runtime_root_symlink_forbidden"
[[ -f "$SNAPSHOT" ]] || fail "live_capability_snapshot_missing"
[[ ! -L "$SNAPSHOT" ]] || fail "live_capability_snapshot_symlink_forbidden"
snapshot_sha="$(sha256sum "$SNAPSHOT" | awk '{print $1}')"
[[ "$snapshot_sha" == "$EXPECTED_SNAPSHOT_SHA" ]] || fail "live_capability_snapshot_sha_mismatch"

[[ -f "$HOST_REPORT" ]] || fail "post_reboot_host_report_missing"
host_report_sha="$(sha256sum "$HOST_REPORT" | awk '{print $1}')"
[[ "$host_report_sha" == "$EXPECTED_HOST_REPORT_SHA" ]] || fail "post_reboot_host_report_sha_mismatch"

[[ -f "$ENV_FILE" ]] || fail "credential_env_missing"
[[ ! -L "$ENV_FILE" ]] || fail "credential_env_symlink_forbidden"
env_mode="$(stat -c '%a' "$ENV_FILE")"
env_owner="$(stat -c '%U:%G' "$ENV_FILE")"
[[ "$env_mode" == "600" ]] || fail "credential_env_mode_not_0600"
[[ "$env_owner" == "botmarket:botmarket" ]] || fail "credential_env_owner_mismatch:$env_owner"
sudo -u botmarket -H test -r "$ENV_FILE" || fail "credential_env_not_readable_by_botmarket"

[[ ! -e "$AUTH_FILE" ]] || fail "runtime_launch_authorization_already_present"
[[ ! -e "$STATE_FILE" ]] || fail "collector_state_already_present"
[[ ! -e "$MANIFEST_FILE" ]] || fail "collector_manifest_already_present"
[[ ! -e "$LAUNCH_REPORT" ]] || fail "collector_launch_report_already_present"

if pgrep -f 'sc001_b15p1_nonprice_transferability_collector_v0_1_3[.]py' >/dev/null 2>&1; then
  fail "collector_process_already_running"
fi

active_state="$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || true)"
enabled_state="$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || true)"
case "$active_state" in
  inactive|unknown|"") ;;
  *) fail "stable_service_not_inactive:$active_state" ;;
esac
case "$enabled_state" in
  disabled|not-found|"") ;;
  *) fail "stable_service_not_disabled:$enabled_state" ;;
esac

if [[ -e "$RUNTIME_UNIT" ]]; then
  UNIT_WAS_PRESENT=1
  [[ -f "$RUNTIME_UNIT" ]] || fail "runtime_unit_not_regular_file"
  [[ ! -L "$RUNTIME_UNIT" ]] || fail "runtime_unit_symlink_forbidden"
  current_unit_sha="$(sha256sum "$RUNTIME_UNIT" | awk '{print $1}')"
  [[ "$current_unit_sha" == "$EXPECTED_SERVICE_SHA" ]] || fail "runtime_unit_sha_mismatch:$current_unit_sha"
else
  UNIT_WAS_PRESENT=0
fi

show_text="$(systemctl show "$SERVICE_NAME" -p LoadState -p FragmentPath -p DropInPaths 2>/dev/null || true)"
if printf '%s\n' "$show_text" | grep -Eq '^DropInPaths=.+$'; then
  fail "stable_service_dropins_present"
fi

SOURCE_FILES=(
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
  "$CANDIDATE_REL"
  "$PRELAUNCH_RESULT_REL"
  "$POST_REBOOT_RESULT_REL"
)

SOURCE_SHAS=(
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
  "$EXPECTED_CANDIDATE_SHA"
  "$EXPECTED_PRELAUNCH_RESULT_SHA"
  "$EXPECTED_POST_REBOOT_RESULT_SHA"
)

DEPLOY_FILES=(
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
)

DEPLOY_SHAS=(
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
)

[[ "${#SOURCE_FILES[@]}" -eq "${#SOURCE_SHAS[@]}" ]] || fail "source_array_mismatch"
[[ "${#DEPLOY_FILES[@]}" -eq "${#DEPLOY_SHAS[@]}" ]] || fail "deploy_array_mismatch"

for i in "${!SOURCE_FILES[@]}"; do
  rel="${SOURCE_FILES[$i]}"
  expected="${SOURCE_SHAS[$i]}"
  src="$REPO/$rel"
  [[ -f "$src" ]] || fail "source_missing:$rel"
  [[ ! -L "$src" ]] || fail "source_symlink_forbidden:$rel"
  actual="$(sha256sum "$src" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || fail "source_sha_mismatch:$rel"
done

rm -rf "$STAGE"
install -d -m 0750 -o botmarket -g botmarket "$STAGE"

for i in "${!SOURCE_FILES[@]}"; do
  rel="${SOURCE_FILES[$i]}"
  expected="${SOURCE_SHAS[$i]}"
  src="$REPO/$rel"
  dst="$STAGE/$rel"
  install -d -m 0750 -o botmarket -g botmarket "$(dirname "$dst")"
  install -m 0640 -o botmarket -g botmarket "$src" "$dst"
  actual="$(sha256sum "$dst" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || fail "staged_sha_mismatch:$rel"
done

[[ -z "$(find "$STAGE" -type l -print -quit)" ]] || fail "staging_symlink_detected"
stage_file_count="$(find "$STAGE" -type f | wc -l | awk '{print $1}')"
[[ "$stage_file_count" == "${#SOURCE_FILES[@]}" ]] || fail "unexpected_staging_file_count:$stage_file_count"

STAGED_RUNNER="$STAGE/$RUNNER_REL"
STAGED_LIBRARY="$STAGE/$LIBRARY_REL"
STAGED_SERVICE="$STAGE/$SERVICE_REL"
STAGED_CANDIDATE="$STAGE/$CANDIDATE_REL"
STAGED_AUTH="$STAGE/runtime/collector_launch_authorization.json"
STAGED_STABLE_UNIT="$STAGE/runtime/$SERVICE_NAME"
STAGED_SELFTEST="$STAGE/output/implementation_self_test_manifest.json"

install -d -m 0750 -o botmarket -g botmarket "$STAGE/runtime" "$STAGE/output"
install -m 0640 -o botmarket -g botmarket "$STAGED_SERVICE" "$STAGED_STABLE_UNIT"
[[ "$(sha256sum "$STAGED_STABLE_UNIT" | awk '{print $1}')" == "$EXPECTED_SERVICE_SHA" ]] || fail "staged_stable_unit_sha_mismatch"

systemd-analyze verify "$STAGED_STABLE_UNIT" >/dev/null 2>"$STAGE/systemd_verify.stderr" || {
  cat "$STAGE/systemd_verify.stderr" >&2 || true
  fail "staged_systemd_verify_failed"
}

sudo -u botmarket -H env -i \
  HOME=/home/botmarket \
  PATH=/usr/bin:/bin \
  B15P1_REPO_ROOT="$STAGE" \
  B15P1_SELFTEST_OUTPUT="$STAGED_SELFTEST" \
  /usr/bin/python3 -m py_compile "$STAGED_RUNNER" "$STAGED_LIBRARY" || fail "staged_python_compile_failed"

set +e
selftest_stdout="$(
  sudo -u botmarket -H env -i \
    HOME=/home/botmarket \
    PATH=/usr/bin:/bin \
    B15P1_REPO_ROOT="$STAGE" \
    B15P1_SELFTEST_OUTPUT="$STAGED_SELFTEST" \
    /usr/bin/python3 "$STAGED_RUNNER" --mode self-test 2>&1
)"
selftest_rc="$?"
set -e
printf '%s\n' "$selftest_stdout"
[[ "$selftest_rc" -eq 0 ]] || fail "staged_collector_selftest_failed:$selftest_rc"
printf '%s\n' "$selftest_stdout" | grep -q '^B15P1_NONPRICE_COLLECTOR_V013_SELF_TEST_PASS$' || fail "staged_selftest_pass_token_missing"

sudo -u botmarket -H env -i \
  HOME=/home/botmarket \
  PATH=/usr/bin:/bin \
  B15P1_REPO_ROOT="$STAGE" \
  B15P1_CAPABILITY_SNAPSHOT="$SNAPSHOT" \
  SC001_DATA_ROOT="$DATA_ROOT" \
  /usr/bin/python3 - \
    "$STAGED_CANDIDATE" \
    "$STAGED_AUTH" \
    "$EXPECTED_AUTH_SHA" \
    "$EXPECTED_RUNNER_SHA" \
    "$EXPECTED_FREEZE_SHA" \
    "$EXPECTED_SNAPSHOT_SHA" \
    "$EXPECTED_SERVICE_SHA" <<'PY'
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

candidate_path, auth_path, expected_auth_sha, runner_sha, freeze_sha, snapshot_sha, service_sha = sys.argv[1:]
candidate = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
assert candidate.get("status") == "CANDIDATE_NOT_ACTIVE"
assert candidate.get("runtime_install_authorized") is False
assert candidate.get("collector_start_authorized") is False
payload = candidate.get("proposed_runtime_payload")
assert isinstance(payload, dict)
raw = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
assert hashlib.sha256(raw).hexdigest() == expected_auth_sha
out = Path(auth_path)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(raw)

collector_path = Path(os.environ["B15P1_REPO_ROOT"]) / "research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_3.py"
sys.path.insert(0, str(collector_path.parent))
spec = importlib.util.spec_from_file_location("b15p1_final_prestart", collector_path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fr = module.require_freeze()
cap, _ = module.load_capability(fr)
module.validate_launch_authorization(
    payload,
    runner_sha256=runner_sha,
    freeze_sha256=freeze_sha,
    capability_sha256=snapshot_sha,
    service_sha256=service_sha,
)
assert cap is not None
print("staged_launch_authorization_validator = PASS")
PY

[[ "$(sha256sum "$STAGED_AUTH" | awk '{print $1}')" == "$EXPECTED_AUTH_SHA" ]] || fail "staged_launch_authorization_sha_mismatch"

# Validate prior frozen prerequisite documents immediately before mutation.
python3 - \
  "$STAGE/$PRELAUNCH_RESULT_REL" \
  "$STAGE/$POST_REBOOT_RESULT_REL" \
  "$EXPECTED_SNAPSHOT_SHA" \
  "$EXPECTED_HOST_REPORT_SHA" <<'PY'
import json, sys
from pathlib import Path

pre = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
post = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
snapshot_sha = sys.argv[3]
host_report_sha = sys.argv[4]

assert pre.get("status") == "B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE_PASS"
assert pre.get("live_snapshot_sha256") == snapshot_sha
assert (pre.get("safety") or {}).get("collector_start_performed") is False
assert (pre.get("safety") or {}).get("runtime_authorization_created") is False

assert post.get("status") == "B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_POST_REBOOT_PASS"
assert post.get("reboot_hold_cleared") is True
assert (post.get("snapshot") or {}).get("sha256") == snapshot_sha
assert post.get("host_report_sha256") == host_report_sha
assert (post.get("host_state") or {}).get("stable_service_active") == "inactive"
assert (post.get("host_state") or {}).get("stable_service_enabled") == "not-found"
assert (post.get("host_state") or {}).get("runtime_unit_sha256_or_absent") == "ABSENT"
assert (post.get("host_state") or {}).get("runtime_launch_authorization_present") is False
print("final_launch_prerequisites = PASS")
PY

MUTATION_STARTED=1
backup_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="$BACKUP_ROOT/$backup_stamp"
install -d -m 0750 -o botmarket -g botmarket "$BACKUP_DIR"

# Deploy only the exact B15-P1 frozen runtime files; do not touch unrelated project files.
for i in "${!DEPLOY_FILES[@]}"; do
  rel="${DEPLOY_FILES[$i]}"
  expected="${DEPLOY_SHAS[$i]}"
  src="$STAGE/$rel"
  dst="$RUNTIME_ROOT/$rel"
  install -d -m 0750 -o botmarket -g botmarket "$(dirname "$dst")"
  if [[ -e "$dst" ]]; then
    [[ -f "$dst" && ! -L "$dst" ]] || fail "runtime_target_not_regular:$rel"
    old_sha="$(sha256sum "$dst" | awk '{print $1}')"
    if [[ "$old_sha" != "$expected" ]]; then
      backup="$BACKUP_DIR/$rel"
      install -d -m 0750 -o botmarket -g botmarket "$(dirname "$backup")"
      cp -a "$dst" "$backup"
    fi
  fi
  install -m 0640 -o botmarket -g botmarket "$src" "$dst"
  actual="$(sha256sum "$dst" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || fail "runtime_deploy_sha_mismatch:$rel"
done

# Install the exact frozen v0.1.3 service candidate under the stable runtime name.
install -m 0644 -o root -g root "$RUNTIME_ROOT/$SERVICE_REL" "$RUNTIME_UNIT"
UNIT_INSTALLED=1
[[ "$(sha256sum "$RUNTIME_UNIT" | awk '{print $1}')" == "$EXPECTED_SERVICE_SHA" ]] || fail "installed_runtime_unit_sha_mismatch"
systemd-analyze verify "$RUNTIME_UNIT" >/dev/null 2>"$STAGE/runtime_systemd_verify.stderr" || {
  cat "$STAGE/runtime_systemd_verify.stderr" >&2 || true
  fail "runtime_systemd_verify_failed"
}
systemctl daemon-reload

install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"
install -m 0640 -o botmarket -g botmarket "$STAGED_AUTH" "$AUTH_FILE"
AUTH_CREATED=1
[[ "$(sha256sum "$AUTH_FILE" | awk '{print $1}')" == "$EXPECTED_AUTH_SHA" ]] || fail "runtime_launch_authorization_sha_mismatch"

# Validate the exact runtime freeze, live snapshot and authorization without loading credentials or starting network.
sudo -u botmarket -H env -i \
  HOME=/home/botmarket \
  PATH=/usr/bin:/bin \
  SC001_DATA_ROOT="$DATA_ROOT" \
  B15P1_REPO_ROOT="$RUNTIME_ROOT" \
  B15P1_CAPABILITY_SNAPSHOT="$SNAPSHOT" \
  B15P1_LAUNCH_AUTHORIZATION="$AUTH_FILE" \
  /usr/bin/python3 - <<'PY'
import importlib.util
import os
import sys
from pathlib import Path

root = Path(os.environ["B15P1_REPO_ROOT"])
collector = root / "research/sc001/sc001_b15p1_nonprice_transferability_collector_v0_1_3.py"
sys.path.insert(0, str(collector.parent))
spec = importlib.util.spec_from_file_location("b15p1_runtime_prestart", collector)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fr = module.require_freeze()
mapping = module.load_mapping()
module.ensure_mapping_invariants(mapping)
module.load_capability(fr)
module.require_launch_authorization()
print("runtime_prestart_freeze_capability_authorization = PASS")
PY

systemctl enable "$SERVICE_NAME"
SERVICE_ENABLED=1
systemctl start "$SERVICE_NAME"
SERVICE_STARTED=1

# Wait for at least two completed polls and one fully valid poll; max ~90 seconds.
ready=0
for _ in $(seq 1 30); do
  service_now="$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || true)"
  if [[ "$service_now" != "active" ]]; then
    fail "collector_service_not_active_after_start:$service_now"
  fi
  if [[ -f "$STATE_FILE" && -f "$MANIFEST_FILE" ]]; then
    set +e
    python3 - "$STATE_FILE" "$MANIFEST_FILE" "$AUTH_FILE" "$SNAPSHOT" "$EXPECTED_AUTH_SHA" "$EXPECTED_SNAPSHOT_SHA" "$EXPECTED_RUNNER_SHA" "$EXPECTED_LIBRARY_SHA" "$EXPECTED_FREEZE_SHA" "$EXPECTED_PROTOCOL_SHA" "$EXPECTED_DESIGN_SHA" "$EXPECTED_DESIGN_MANIFEST_SHA" "$EXPECTED_ROUTE_GRAPH_SHA" <<'PY'
import hashlib
import json
import sys
import time
from pathlib import Path

(
    state_arg, manifest_arg, auth_arg, snapshot_arg,
    expected_auth_sha, expected_snapshot_sha, expected_runner_sha,
    expected_library_sha, expected_freeze_sha, expected_protocol_sha,
    expected_design_sha, expected_design_preflight_sha, expected_route_graph_sha,
) = sys.argv[1:]

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

state = load(state_arg)
manifest = load(manifest_arg)

assert sha(auth_arg) == expected_auth_sha
assert sha(snapshot_arg) == expected_snapshot_sha

assert state.get("stage") == "SC001-B15P1-NONPRICE-TRANSFERABILITY-COLLECTOR-V0.1.3"
assert state.get("version") == "0.1.3"
assert state.get("status") == "B15P1_NONPRICE_COLLECTION_RUNNING"
poll_count = int(state.get("poll_count") or 0)
invalid = int(state.get("invalid_poll_count") or 0)
assert poll_count >= 2
assert poll_count - invalid >= 1
assert state.get("price_data_collected") is False
assert state.get("pnl_calculated") is False
heartbeat = int(state.get("last_heartbeat_ms") or 0)
assert heartbeat > 0
assert int(time.time() * 1000) - heartbeat <= 60000
chain = str(state.get("last_poll_chain_hash") or "")
assert len(chain) == 64 and chain != "0" * 64

assert manifest.get("stage") == "SC001-B15P1-NONPRICE-TRANSFERABILITY-COLLECTOR-V0.1.3"
assert manifest.get("version") == "0.1.3"
assert manifest.get("runner_sha256") == expected_runner_sha
assert manifest.get("library_sha256") == expected_library_sha
assert manifest.get("implementation_freeze_sha256") == expected_freeze_sha
assert manifest.get("protocol_sha256") == expected_protocol_sha
assert manifest.get("design_candidate_sha256") == expected_design_sha
assert manifest.get("design_preflight_manifest_sha256") == expected_design_preflight_sha
assert manifest.get("route_graph_sha256") == expected_route_graph_sha
assert manifest.get("capability_snapshot_sha256") == expected_snapshot_sha
assert manifest.get("capability_status") == "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS"
assert manifest.get("fast_cadence_seconds") == 15
assert manifest.get("request_deadline_seconds") == 12
assert manifest.get("fee_refresh_seconds") == 21600
assert manifest.get("fee_stale_after_seconds") == 28800
assert manifest.get("price_data_authorized") is False
assert manifest.get("pnl_authorized") is False

print(poll_count)
print(invalid)
PY
    verify_rc="$?"
    set -e
    if [[ "$verify_rc" -eq 0 ]]; then
      ready=1
      break
    fi
  fi
  sleep 3
done

[[ "$ready" -eq 1 ]] || fail "collector_initial_poll_verification_timeout"

final_active="$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || true)"
final_enabled="$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || true)"
[[ "$final_active" == "active" ]] || fail "final_service_not_active:$final_active"
[[ "$final_enabled" == "enabled" ]] || fail "final_service_not_enabled:$final_enabled"

python3 - \
  "$STATE_FILE" \
  "$MANIFEST_FILE" \
  "$AUTH_FILE" \
  "$SNAPSHOT" \
  "$LAUNCH_REPORT" \
  "$EXPECTED_AUTH_SHA" \
  "$EXPECTED_SNAPSHOT_SHA" \
  "$EXPECTED_SERVICE_SHA" \
  "$final_active" \
  "$final_enabled" <<'PY'
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

state_arg, manifest_arg, auth_arg, snapshot_arg, out_arg, expected_auth_sha, expected_snapshot_sha, service_sha, active, enabled = sys.argv[1:]

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

state = load(state_arg)
manifest = load(manifest_arg)
report = {
    "schema": "sc001.b15.p1_collector_final_launch_verification.v0.1",
    "status": "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_PASS",
    "verified_utc": datetime.now(timezone.utc).isoformat(),
    "service_active": active,
    "service_enabled": enabled,
    "service_file_sha256": service_sha,
    "launch_authorization_sha256": sha(auth_arg),
    "capability_snapshot_sha256": sha(snapshot_arg),
    "collector_state": {
        "status": state.get("status"),
        "process_epoch": state.get("process_epoch"),
        "poll_count": state.get("poll_count"),
        "invalid_poll_count": state.get("invalid_poll_count"),
        "missed_poll_slots": state.get("missed_poll_slots"),
        "source_gap_count": state.get("source_gap_count"),
        "last_heartbeat_ms": state.get("last_heartbeat_ms"),
        "last_scheduled_slot_ms": state.get("last_scheduled_slot_ms"),
        "last_poll_chain_hash": state.get("last_poll_chain_hash"),
        "price_data_collected": state.get("price_data_collected"),
        "pnl_calculated": state.get("pnl_calculated"),
    },
    "collector_manifest_sha256": sha(manifest_arg),
    "runtime_authorization_created": True,
    "collector_start_performed": True,
    "price_data_authorized": False,
    "pnl_authorized": False,
    "live_execution_authorized": False,
    "first_operational_review_after_complete_utc_days": 7,
}
assert report["launch_authorization_sha256"] == expected_auth_sha
assert report["capability_snapshot_sha256"] == expected_snapshot_sha
assert report["collector_state"]["price_data_collected"] is False
assert report["collector_state"]["pnl_calculated"] is False
out = Path(out_arg)
tmp = out.with_name(out.name + ".tmp")
tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
os.chmod(tmp, 0o640)
os.replace(tmp, out)
print("launch_report_sha256 =", sha(out))
print("poll_count =", state.get("poll_count"))
print("invalid_poll_count =", state.get("invalid_poll_count"))
print("last_heartbeat_ms =", state.get("last_heartbeat_ms"))
PY

SUCCESS=1
trap - ERR

echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_PASS"
echo "service_active=$final_active"
echo "service_enabled=$final_enabled"
echo "live_snapshot_sha256=$EXPECTED_SNAPSHOT_SHA"
echo "launch_authorization_sha256=$EXPECTED_AUTH_SHA"
echo "launch_report=$LAUNCH_REPORT"
echo "price_data_authorized=False"
echo "pnl_authorized=False"
echo "live_execution_authorized=False"
