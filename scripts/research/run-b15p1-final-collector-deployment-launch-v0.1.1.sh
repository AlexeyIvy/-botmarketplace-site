#!/usr/bin/env bash
set -eEuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
STAGE="/home/botmarket/.local/share/botmarket/b15p1-final-launch-v0.1.1-stage"
RUNTIME_ROOT="/home/botmarket/botmarketplace-site"
BACKUP_ROOT="/home/botmarket/.local/share/botmarket/b15p1-final-launch-v0.1.1-backup"
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
RECOVERY_REPORT="$OUT_DIR/final_launch_v0.1_recovery_manifest.json"
LOCK_FILE="/run/lock/botmarket-b15p1-final-launch-v0.1.1.lock"

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
RECOVERY_HOST_RESULT_REL="docs/research/sc001-b15-p1-final-launch-v0.1-failure-recovery-host-result-v0.1.json"
FAILURE_DIAGNOSTIC_REL="docs/research/sc001-b15-p1-final-launch-attempt-v0.1-technical-failure-diagnostic.json"

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
EXPECTED_RECOVERY_HOST_RESULT_SHA="cf5743e65f577e346df21bfcc03cecd9ae428cea3c1ff338e254e09a476f79fe"
EXPECTED_FAILURE_DIAGNOSTIC_SHA="03bead41d3c92851db47259429a1d0ee0b538116c01203ebfe83c581ca18c04a"
EXPECTED_RECOVERY_REPORT_SHA="59d77abb773e482c3fc804878ac17214b516bc72807635f52efa881507741a25"
EXPECTED_HOST_REPORT_SHA="e249f824a4b10f19a81aa6e01f1f5d7beee5088997880b146378f73f676d7aee"
EXPECTED_SNAPSHOT_SHA="14341c153649455459f18998be90d65a3010c009893bf76b359dc0b5b74387fc"
EXPECTED_AUTH_SHA="fd5b9a6c683bd15df2dfc26c4ba6497d8e8e152d9b70ed1dc1edeab5107f13be"

MUTATION_STARTED=0
AUTH_CREATED=0
UNIT_INSTALLED=0
SERVICE_ENABLED=0
SERVICE_STARTED=0
FAIL_HANDLED=0
SUCCESS=0
ROLLBACK_DONE=0
ROLLBACK_INCOMPLETE=0
BACKUP_DIR=""
ROLLBACK_LEDGER=""
UNIT_TMP=""
AUTH_TMP=""
DEPLOY_TEMP_FILES=()

rollback() {
  set +e
  if [[ "$ROLLBACK_DONE" -eq 1 ]]; then
    set -e
    return
  fi
  ROLLBACK_DONE=1
  if [[ "$MUTATION_STARTED" -eq 1 ]]; then
    systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true
    systemctl disable "$SERVICE_NAME" >/dev/null 2>&1 || true

    if [[ "$AUTH_CREATED" -eq 1 && -f "$AUTH_FILE" ]]; then
      auth_sha_now="$(sha256sum "$AUTH_FILE" 2>/dev/null | awk '{print $1}')"
      if [[ "$auth_sha_now" == "$EXPECTED_AUTH_SHA" ]]; then
        rm -f "$AUTH_FILE"
      else
        ROLLBACK_INCOMPLETE=1
      fi
    fi

    if [[ "$UNIT_INSTALLED" -eq 1 && -f "$RUNTIME_UNIT" ]]; then
      unit_sha_now="$(sha256sum "$RUNTIME_UNIT" 2>/dev/null | awk '{print $1}')"
      if [[ "$unit_sha_now" == "$EXPECTED_SERVICE_SHA" ]]; then
        rm -f "$RUNTIME_UNIT"
        systemctl daemon-reload >/dev/null 2>&1 || true
      else
        ROLLBACK_INCOMPLETE=1
      fi
    fi

    if [[ -n "$UNIT_TMP" ]]; then rm -f "$UNIT_TMP" >/dev/null 2>&1 || true; fi
    if [[ -n "$AUTH_TMP" ]]; then rm -f "$AUTH_TMP" >/dev/null 2>&1 || true; fi
    for tmp in "${DEPLOY_TEMP_FILES[@]}"; do
      rm -f "$tmp" >/dev/null 2>&1 || true
    done

    if [[ -n "$ROLLBACK_LEDGER" && -f "$ROLLBACK_LEDGER" ]]; then
      while IFS=$'\t' read -r rel existed expected; do
        [[ -n "$rel" ]] || continue
        dst="$RUNTIME_ROOT/$rel"
        backup="$BACKUP_DIR/files/$rel"
        if [[ "$existed" == "1" ]]; then
          if [[ -f "$backup" && ! -L "$backup" ]]; then
            if [[ -L "$dst" ]]; then
              ROLLBACK_INCOMPLETE=1
              continue
            fi
            install -d -m 0750 -o botmarket -g botmarket "$(dirname "$dst")" >/dev/null 2>&1 || {
              ROLLBACK_INCOMPLETE=1
              continue
            }
            rm -f "$dst" >/dev/null 2>&1 || true
            cp -a "$backup" "$dst" >/dev/null 2>&1 || ROLLBACK_INCOMPLETE=1
          else
            ROLLBACK_INCOMPLETE=1
          fi
        else
          if [[ -e "$dst" ]]; then
            if [[ -f "$dst" && ! -L "$dst" ]]; then
              current_sha="$(sha256sum "$dst" 2>/dev/null | awk '{print $1}')"
              if [[ "$current_sha" == "$expected" ]]; then
                rm -f "$dst" >/dev/null 2>&1 || ROLLBACK_INCOMPLETE=1
              else
                ROLLBACK_INCOMPLETE=1
              fi
            else
              ROLLBACK_INCOMPLETE=1
            fi
          fi
        fi
      done < "$ROLLBACK_LEDGER"
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
  echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_V011_REVIEW"
  echo "reason=$reason"
  echo "rollback_incomplete=$ROLLBACK_INCOMPLETE"
  echo "collector_may_have_failure_evidence=True"
  echo "price_pnl_authorized=False"
  exit 2
}

on_err() {
  local rc="$?"
  local line="$1"
  if [[ "$SUCCESS" -ne 1 && "$FAIL_HANDLED" -ne 1 ]]; then
    FAIL_HANDLED=1
    rollback
    echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_V011_REVIEW"
    echo "reason=unexpected_shell_error:line=$line:rc=$rc"
    echo "rollback_incomplete=$ROLLBACK_INCOMPLETE"
    echo "collector_may_have_failure_evidence=True"
    echo "price_pnl_authorized=False"
  fi
  exit "$rc"
}

on_signal() {
  local signal_name="$1"
  local exit_code="$2"
  if [[ "$SUCCESS" -ne 1 ]]; then
    FAIL_HANDLED=1
    rollback
    echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_V011_REVIEW"
    echo "reason=signal:$signal_name"
    echo "rollback_incomplete=$ROLLBACK_INCOMPLETE"
    echo "price_pnl_authorized=False"
  fi
  exit "$exit_code"
}

on_exit() {
  local rc="$1"
  if [[ "$rc" -ne 0 && "$SUCCESS" -ne 1 && "$FAIL_HANDLED" -ne 1 ]]; then
    rollback
  fi
}

trap 'on_err $LINENO' ERR
trap 'on_signal HUP 129' HUP
trap 'on_signal INT 130' INT
trap 'on_signal TERM 143' TERM
trap 'on_exit $?' EXIT
[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "wrapper_must_run_as_root"

exec 9>"$LOCK_FILE"
flock -n 9 || fail "another_final_launch_or_recovery_in_progress"

for cmd in sha256sum awk stat install sudo python3 find wc systemctl systemd-analyze pgrep date grep tail sleep mkdir rm cp mv seq cat env flock dirname; do
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

[[ -f "$RECOVERY_REPORT" ]] || fail "recovery_report_missing"
[[ ! -L "$RECOVERY_REPORT" ]] || fail "recovery_report_symlink_forbidden"
recovery_report_sha="$(sha256sum "$RECOVERY_REPORT" | awk '{print $1}')"
[[ "$recovery_report_sha" == "$EXPECTED_RECOVERY_REPORT_SHA" ]] || fail "recovery_report_sha_mismatch"

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
  not-found|"") ;;
  *) fail "stable_service_should_be_not_found_after_recovery:$enabled_state" ;;
esac

[[ ! -e "$RUNTIME_UNIT" ]] || fail "runtime_unit_present_after_recovery"

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
  "$RECOVERY_HOST_RESULT_REL"
  "$FAILURE_DIAGNOSTIC_REL"
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
  "$EXPECTED_RECOVERY_HOST_RESULT_SHA"
  "$EXPECTED_FAILURE_DIAGNOSTIC_SHA"
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

python3 - "$RUNTIME_ROOT" "$DATA_ROOT" "${DEPLOY_FILES[@]}" <<'PY'
import shutil
import sys
from pathlib import Path

runtime_root = Path(sys.argv[1])
data_root = Path(sys.argv[2])
deploy_rels = sys.argv[3:]

if runtime_root.is_symlink() or not runtime_root.is_dir():
    raise SystemExit("runtime root invalid")

for rel in deploy_rels:
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise SystemExit(f"unsafe deploy relative path: {rel}")
    current = runtime_root
    for part in rel_path.parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise SystemExit(f"runtime parent symlink forbidden: {current}")

usage = shutil.disk_usage(data_root)
free_percent = 100.0 * usage.free / usage.total
if usage.free < 10 * 1024**3 or free_percent < 15.0:
    raise SystemExit(
        f"storage pressure before launch: free_bytes={usage.free} free_percent={free_percent:.2f}"
    )
print("runtime_path_and_storage_preflight = PASS")
print("free_bytes =", usage.free)
print("free_percent =", round(free_percent, 2))
PY

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

if selftest_stdout="$(
  sudo -u botmarket -H env -i \
    HOME=/home/botmarket \
    PATH=/usr/bin:/bin \
    B15P1_REPO_ROOT="$STAGE" \
    B15P1_SELFTEST_OUTPUT="$STAGED_SELFTEST" \
    /usr/bin/python3 "$STAGED_RUNNER" --mode self-test 2>&1
)"; then
  selftest_rc=0
else
  selftest_rc="$?"
fi
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

# Validate the full prerequisite + failed-attempt recovery chain immediately before mutation.
python3 - \
  "$STAGE/$PRELAUNCH_RESULT_REL" \
  "$STAGE/$POST_REBOOT_RESULT_REL" \
  "$STAGE/$RECOVERY_HOST_RESULT_REL" \
  "$STAGE/$FAILURE_DIAGNOSTIC_REL" \
  "$RECOVERY_REPORT" \
  "$EXPECTED_SNAPSHOT_SHA" \
  "$EXPECTED_HOST_REPORT_SHA" \
  "$EXPECTED_RECOVERY_REPORT_SHA" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

(
    prelaunch_arg,
    post_reboot_arg,
    recovery_host_arg,
    failure_diag_arg,
    recovery_report_arg,
    snapshot_sha,
    host_report_sha,
    recovery_report_sha,
) = sys.argv[1:]

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

pre = load(prelaunch_arg)
post = load(post_reboot_arg)
recovery_host = load(recovery_host_arg)
diag = load(failure_diag_arg)
recovery = load(recovery_report_arg)

assert pre.get("status") == "B15P1_COLLECTOR_PRELAUNCH_READINESS_OFFLINE_PASS"
assert pre.get("live_snapshot_sha256") == snapshot_sha
assert (pre.get("safety") or {}).get("collector_start_performed") is False
assert (pre.get("safety") or {}).get("runtime_authorization_created") is False

assert post.get("status") == "B15P1_COLLECTOR_HOST_DEPLOYMENT_READINESS_POST_REBOOT_PASS"
assert post.get("reboot_hold_cleared") is True
assert (post.get("snapshot") or {}).get("sha256") == snapshot_sha
assert post.get("host_report_sha256") == host_report_sha

assert diag.get("status") == "TECHNICAL_WRAPPER_CONTROL_FLOW_FAILURE"
assert (diag.get("exact_failure") or {}).get("failure_class") == "EXPECTED_NOT_READY_STATE_TRIGGERED_GLOBAL_ERR_TRAP"
assert diag.get("retry_authorized") is False

assert recovery_host.get("status") == "B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_PASS"
assert recovery_host.get("recovery_report_sha256") == recovery_report_sha
assert recovery_host.get("archived_file_count") == 7
host_state = recovery_host.get("host_state") or {}
assert host_state.get("service_active") == "inactive"
assert host_state.get("service_enabled") == "not-found"
assert host_state.get("runtime_unit") == "ABSENT"
assert host_state.get("runtime_authorization") == "ABSENT"
assert host_state.get("active_state") == "ABSENT"
assert host_state.get("active_manifest") == "ABSENT"

assert sha(recovery_report_arg) == recovery_report_sha
assert recovery.get("status") == "B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_PASS"
assert recovery.get("live_snapshot_sha256") == snapshot_sha
assert recovery.get("archived_file_count") == 7
assert recovery.get("archive_dir") == recovery_host.get("archive_dir")
assert recovery.get("runtime_unit_present_after_recovery") is False
assert recovery.get("runtime_authorization_present_after_recovery") is False
assert recovery.get("active_collector_state_present_after_recovery") is False
assert recovery.get("active_collector_manifest_present_after_recovery") is False
assert recovery.get("collector_start_authorized") is False
assert recovery.get("price_pnl_authorized") is False

archive_root = Path(recovery["archive_dir"])
assert archive_root.is_dir() and not archive_root.is_symlink()
archived_files = recovery.get("archived_files") or []
assert len(archived_files) == recovery.get("archived_file_count")
for item in archived_files:
    rel = Path(str(item.get("path") or ""))
    assert not rel.is_absolute() and ".." not in rel.parts
    p = archive_root / rel
    assert p.is_file() and not p.is_symlink()
    assert p.stat().st_size == int(item.get("size_bytes"))
    assert sha(p) == item.get("sha256")

print("final_launch_v011_prerequisites_and_recovery_evidence = PASS")
print("archived_failure_evidence_files =", len(archived_files))
PY

MUTATION_STARTED=1
backup_stamp="$(date -u +%Y%m%dT%H%M%SZ)_$$"
BACKUP_DIR="$BACKUP_ROOT/$backup_stamp"
[[ ! -e "$BACKUP_DIR" ]] || fail "backup_dir_already_exists:$BACKUP_DIR"
install -d -m 0750 -o botmarket -g botmarket "$BACKUP_DIR/files"
ROLLBACK_LEDGER="$BACKUP_DIR/runtime_file_ledger.tsv"
install -m 0640 -o botmarket -g botmarket /dev/null "$ROLLBACK_LEDGER"

for i in "${!DEPLOY_FILES[@]}"; do
  rel="${DEPLOY_FILES[$i]}"
  expected="${DEPLOY_SHAS[$i]}"
  src="$STAGE/$rel"
  dst="$RUNTIME_ROOT/$rel"
  install -d -m 0750 -o botmarket -g botmarket "$(dirname "$dst")"

  existed=0
  if [[ -e "$dst" ]]; then
    [[ -f "$dst" && ! -L "$dst" ]] || fail "runtime_target_not_regular:$rel"
    backup="$BACKUP_DIR/files/$rel"
    install -d -m 0750 -o botmarket -g botmarket "$(dirname "$backup")"
    cp -a "$dst" "$backup"
    existed=1
  fi
  printf '%s\t%s\t%s\n' "$rel" "$existed" "$expected" >> "$ROLLBACK_LEDGER"

  tmp="$dst.b15p1.v011.tmp.$$"
  DEPLOY_TEMP_FILES+=("$tmp")
  rm -f "$tmp"
  install -m 0640 -o botmarket -g botmarket "$src" "$tmp"
  [[ "$(sha256sum "$tmp" | awk '{print $1}')" == "$expected" ]] || fail "runtime_temp_sha_mismatch:$rel"
  mv -f "$tmp" "$dst"
  [[ "$(sha256sum "$dst" | awk '{print $1}')" == "$expected" ]] || fail "runtime_deploy_sha_mismatch:$rel"
done

for i in "${!DEPLOY_FILES[@]}"; do
  rel="${DEPLOY_FILES[$i]}"
  expected="${DEPLOY_SHAS[$i]}"
  dst="$RUNTIME_ROOT/$rel"
  [[ -f "$dst" && ! -L "$dst" ]] || fail "runtime_deployed_file_missing:$rel"
  [[ "$(sha256sum "$dst" | awk '{print $1}')" == "$expected" ]] || fail "runtime_deployed_set_sha_mismatch:$rel"
done

UNIT_TMP="$RUNTIME_UNIT.b15p1.v011.tmp.$$"
rm -f "$UNIT_TMP"
install -m 0644 -o root -g root "$RUNTIME_ROOT/$SERVICE_REL" "$UNIT_TMP"
[[ "$(sha256sum "$UNIT_TMP" | awk '{print $1}')" == "$EXPECTED_SERVICE_SHA" ]] || fail "runtime_unit_temp_sha_mismatch"
UNIT_INSTALLED=1
mv -f "$UNIT_TMP" "$RUNTIME_UNIT"
[[ "$(sha256sum "$RUNTIME_UNIT" | awk '{print $1}')" == "$EXPECTED_SERVICE_SHA" ]] || fail "installed_runtime_unit_sha_mismatch"
systemd-analyze verify "$RUNTIME_UNIT" >/dev/null 2>"$STAGE/runtime_systemd_verify.stderr" || {
  cat "$STAGE/runtime_systemd_verify.stderr" >&2 || true
  fail "runtime_systemd_verify_failed"
}
systemctl daemon-reload

install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"
AUTH_TMP="$AUTH_FILE.b15p1.v011.tmp.$$"
rm -f "$AUTH_TMP"
install -m 0640 -o botmarket -g botmarket "$STAGED_AUTH" "$AUTH_TMP"
[[ "$(sha256sum "$AUTH_TMP" | awk '{print $1}')" == "$EXPECTED_AUTH_SHA" ]] || fail "runtime_launch_authorization_temp_sha_mismatch"
AUTH_CREATED=1
mv -f "$AUTH_TMP" "$AUTH_FILE"
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

# Wait for stable readiness: >=2 completed polls, >=1 fully valid poll, fresh heartbeat.
# NOT_READY is retryable; HARD_FAIL is immediately fail-closed.
ready=0
verify_output=""
for _ in $(seq 1 45); do
  service_now="$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || true)"
  case "$service_now" in
    active) ;;
    activating)
      sleep 1
      continue
      ;;
    *) fail "collector_service_not_active_after_start:$service_now" ;;
  esac

  if [[ -f "$STATE_FILE" && -f "$MANIFEST_FILE" ]]; then
    if verify_output="$(
      python3 - \
        "$STATE_FILE" \
        "$MANIFEST_FILE" \
        "$AUTH_FILE" \
        "$SNAPSHOT" \
        "$OUT_DIR" \
        "$EXPECTED_AUTH_SHA" \
        "$EXPECTED_SNAPSHOT_SHA" \
        "$EXPECTED_RUNNER_SHA" \
        "$EXPECTED_LIBRARY_SHA" \
        "$EXPECTED_FREEZE_SHA" \
        "$EXPECTED_PROTOCOL_SHA" \
        "$EXPECTED_DESIGN_SHA" \
        "$EXPECTED_DESIGN_MANIFEST_SHA" \
        "$EXPECTED_ROUTE_GRAPH_SHA" <<'PY'
import hashlib
import json
import sys
import time
from pathlib import Path

NOT_READY_EXIT = 10
HARD_FAIL_EXIT = 20

(
    state_arg,
    manifest_arg,
    auth_arg,
    snapshot_arg,
    out_dir_arg,
    expected_auth_sha,
    expected_snapshot_sha,
    expected_runner_sha,
    expected_library_sha,
    expected_freeze_sha,
    expected_protocol_sha,
    expected_design_sha,
    expected_design_preflight_sha,
    expected_route_graph_sha,
) = sys.argv[1:]

def hard(reason):
    print("HARD_FAIL =", reason)
    raise SystemExit(HARD_FAIL_EXIT)

def not_ready(reason):
    print("NOT_READY =", reason)
    raise SystemExit(NOT_READY_EXIT)

def require(condition, reason):
    if not condition:
        hard(reason)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        hard(f"json_load_failed:{path}:{type(exc).__name__}:{exc}")

state = load(state_arg)
manifest = load(manifest_arg)
out_dir = Path(out_dir_arg)

require(sha(auth_arg) == expected_auth_sha, "runtime_authorization_sha_mismatch")
require(sha(snapshot_arg) == expected_snapshot_sha, "snapshot_sha_mismatch")

require(state.get("stage") == "SC001-B15P1-NONPRICE-TRANSFERABILITY-COLLECTOR-V0.1.3", "state_stage_mismatch")
require(state.get("version") == "0.1.3", "state_version_mismatch")
require(state.get("price_data_collected") is False, "state_price_firewall_mismatch")
require(state.get("pnl_calculated") is False, "state_pnl_firewall_mismatch")
status = state.get("status")
if status == "INITIALIZED":
    not_ready("state_initialized")
require(status == "B15P1_NONPRICE_COLLECTION_RUNNING", f"state_status_unexpected:{status}")

require(int(state.get("process_epoch") or 0) == 1, "process_epoch_not_one")
require(int(state.get("process_restart_count") or 0) == 0, "process_restart_count_nonzero")

require(manifest.get("stage") == "SC001-B15P1-NONPRICE-TRANSFERABILITY-COLLECTOR-V0.1.3", "manifest_stage_mismatch")
require(manifest.get("version") == "0.1.3", "manifest_version_mismatch")
require(manifest.get("runner_sha256") == expected_runner_sha, "manifest_runner_sha_mismatch")
require(manifest.get("library_sha256") == expected_library_sha, "manifest_library_sha_mismatch")
require(manifest.get("implementation_freeze_sha256") == expected_freeze_sha, "manifest_freeze_sha_mismatch")
require(manifest.get("protocol_sha256") == expected_protocol_sha, "manifest_protocol_sha_mismatch")
require(manifest.get("design_candidate_sha256") == expected_design_sha, "manifest_design_sha_mismatch")
require(manifest.get("design_preflight_manifest_sha256") == expected_design_preflight_sha, "manifest_design_preflight_sha_mismatch")
require(manifest.get("route_graph_sha256") == expected_route_graph_sha, "manifest_route_graph_sha_mismatch")
require(manifest.get("capability_snapshot_sha256") == expected_snapshot_sha, "manifest_capability_snapshot_sha_mismatch")
require(manifest.get("capability_status") == "B15P1_NONPRICE_SOURCE_CAPABILITY_REVALIDATION_PASS", "manifest_capability_status_mismatch")
require(manifest.get("fast_cadence_seconds") == 15, "manifest_fast_cadence_mismatch")
require(manifest.get("request_deadline_seconds") == 12, "manifest_request_deadline_mismatch")
require(manifest.get("fee_refresh_seconds") == 21600, "manifest_fee_refresh_mismatch")
require(manifest.get("fee_stale_after_seconds") == 28800, "manifest_fee_stale_mismatch")
require(manifest.get("price_data_authorized") is False, "manifest_price_firewall_mismatch")
require(manifest.get("pnl_authorized") is False, "manifest_pnl_firewall_mismatch")

poll_count = int(state.get("poll_count") or 0)
invalid_count = int(state.get("invalid_poll_count") or 0)
require(poll_count >= 0, "negative_poll_count")
require(0 <= invalid_count <= poll_count, "invalid_poll_count_out_of_range")

heartbeat = int(state.get("last_heartbeat_ms") or 0)
require(heartbeat > 0, "heartbeat_missing")
heartbeat_age_ms = int(time.time() * 1000) - heartbeat
require(heartbeat_age_ms >= -5000, "heartbeat_in_future")
require(heartbeat_age_ms <= 60000, f"heartbeat_stale:{heartbeat_age_ms}")

if poll_count < 2:
    not_ready(f"poll_count:{poll_count}")
valid_count = poll_count - invalid_count
if valid_count < 1:
    not_ready(f"valid_poll_count:{valid_count}")

chain = str(state.get("last_poll_chain_hash") or "")
require(len(chain) == 64 and chain != "0" * 64, "state_poll_chain_missing")
last_slot = int(state.get("last_scheduled_slot_ms") or 0)
require(last_slot > 0, "last_scheduled_slot_missing")

poll_dir = out_dir / "polls"
require(poll_dir.is_dir() and not poll_dir.is_symlink(), "poll_directory_missing_or_symlink")
scheduled = []
for poll_file in sorted(poll_dir.glob("*.jsonl")):
    require(poll_file.is_file() and not poll_file.is_symlink(), f"poll_file_invalid:{poll_file}")
    with poll_file.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception as exc:
                hard(f"poll_json_invalid:{poll_file}:{line_no}:{exc}")
            if row.get("scheduled_slot_ms") is not None and row.get("poll_chain_hash"):
                scheduled.append(row)

require(len(scheduled) >= poll_count, f"poll_rows_less_than_state:{len(scheduled)}<{poll_count}")
matching = [i for i, row in enumerate(scheduled) if row.get("poll_chain_hash") == chain]
require(bool(matching), "state_poll_chain_not_found_in_poll_log")
state_idx = matching[-1]
state_rows = scheduled[: state_idx + 1]
require(len(state_rows) == poll_count, f"state_poll_count_log_mismatch:{len(state_rows)}!={poll_count}")
require(int(state_rows[-1].get("scheduled_slot_ms")) == last_slot, "last_scheduled_slot_log_mismatch")

slots = [int(row["scheduled_slot_ms"]) for row in state_rows]
require(slots == sorted(set(slots)), "scheduled_slots_not_strictly_increasing")
for a, b in zip(slots, slots[1:]):
    delta = b - a
    require(delta >= 15000 and delta % 15000 == 0, f"scheduled_slot_phase_mismatch:{delta}")

for row in state_rows:
    require(row.get("price_data_collected") is False, "poll_price_firewall_mismatch")

valid_rows = []
for row in state_rows:
    venues = row.get("venues") or {}
    if all((venues.get(v) or {}).get("status") == "OK" for v in ("BYBIT", "OKX")):
        valid_rows.append(row)
require(len(valid_rows) == valid_count, f"valid_poll_state_log_mismatch:{len(valid_rows)}!={valid_count}")
if not valid_rows:
    not_ready("no_fully_valid_poll")

last_valid = valid_rows[-1]
for venue in ("BYBIT", "OKX"):
    venue_row = (last_valid.get("venues") or {}).get(venue) or {}
    raw_sha = str(venue_row.get("raw_body_sha256") or "")
    require(len(raw_sha) == 64, f"{venue}_raw_sha_missing")
    raw_path = out_dir / "raw_objects" / venue.lower() / raw_sha[:2] / f"{raw_sha}.bin"
    require(raw_path.is_file() and not raw_path.is_symlink(), f"{venue}_raw_object_missing")
    require(sha(raw_path) == raw_sha, f"{venue}_raw_object_sha_mismatch")

summary = {
    "poll_count": poll_count,
    "invalid_poll_count": invalid_count,
    "valid_poll_count": valid_count,
    "last_heartbeat_ms": heartbeat,
    "heartbeat_age_ms": heartbeat_age_ms,
    "last_scheduled_slot_ms": last_slot,
    "last_poll_chain_hash": chain,
    "last_valid_poll_slot_ms": int(last_valid["scheduled_slot_ms"]),
}
print("READY =", json.dumps(summary, sort_keys=True))
raise SystemExit(0)
PY
    )"; then
      printf '%s\n' "$verify_output"
      ready=1
      break
    else
      verify_rc="$?"
      printf '%s\n' "$verify_output"
      if [[ "$verify_rc" -eq 10 ]]; then
        sleep 3
        continue
      fi
      fail "collector_initial_verifier_hard_fail:rc=$verify_rc"
    fi
  fi
  sleep 3
done

[[ "$ready" -eq 1 ]] || fail "collector_initial_readiness_timeout"

final_active="$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || true)"
final_enabled="$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || true)"
final_substate="$(systemctl show "$SERVICE_NAME" -p SubState --value 2>/dev/null || true)"
final_main_pid="$(systemctl show "$SERVICE_NAME" -p MainPID --value 2>/dev/null || true)"
final_nrestarts="$(systemctl show "$SERVICE_NAME" -p NRestarts --value 2>/dev/null || true)"

[[ "$final_active" == "active" ]] || fail "final_service_not_active:$final_active"
[[ "$final_enabled" == "enabled" ]] || fail "final_service_not_enabled:$final_enabled"
[[ "$final_substate" == "running" ]] || fail "final_service_substate_not_running:$final_substate"
[[ "$final_main_pid" =~ ^[1-9][0-9]*$ ]] || fail "final_main_pid_invalid:$final_main_pid"
[[ "$final_nrestarts" =~ ^[0-9]+$ ]] || fail "final_nrestarts_invalid:$final_nrestarts"
[[ "$final_nrestarts" -eq 0 ]] || fail "final_nrestarts_nonzero:$final_nrestarts"

python3 - \
  "$STATE_FILE" \
  "$MANIFEST_FILE" \
  "$AUTH_FILE" \
  "$SNAPSHOT" \
  "$RECOVERY_REPORT" \
  "$ROLLBACK_LEDGER" \
  "$LAUNCH_REPORT" \
  "$EXPECTED_AUTH_SHA" \
  "$EXPECTED_SNAPSHOT_SHA" \
  "$EXPECTED_SERVICE_SHA" \
  "$EXPECTED_RECOVERY_REPORT_SHA" \
  "$final_active" \
  "$final_enabled" \
  "$final_substate" \
  "$final_main_pid" \
  "$final_nrestarts" <<'PY'
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

(
    state_arg,
    manifest_arg,
    auth_arg,
    snapshot_arg,
    recovery_report_arg,
    rollback_ledger_arg,
    out_arg,
    expected_auth_sha,
    expected_snapshot_sha,
    service_sha,
    expected_recovery_sha,
    active,
    enabled,
    substate,
    main_pid,
    nrestarts,
) = sys.argv[1:]

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

state = load(state_arg)
manifest = load(manifest_arg)
recovery = load(recovery_report_arg)

assert sha(recovery_report_arg) == expected_recovery_sha
assert recovery.get("status") == "B15P1_FINAL_LAUNCH_V01_FAILURE_RECOVERY_PASS"
assert int(state.get("process_epoch") or 0) == 1
assert int(state.get("process_restart_count") or 0) == 0
assert nrestarts == "0"

report = {
    "schema": "sc001.b15.p1_collector_final_launch_verification.v0.1.1",
    "status": "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_V011_PASS",
    "verified_utc": datetime.now(timezone.utc).isoformat(),
    "technical_retry_of": "final launch v0.1 control-flow failure",
    "recovery_report_sha256": expected_recovery_sha,
    "failed_attempt_archive_dir": recovery.get("archive_dir"),
    "service_active": active,
    "service_enabled": enabled,
    "service_substate": substate,
    "service_main_pid": int(main_pid),
    "service_nrestarts": int(nrestarts),
    "service_file_sha256": service_sha,
    "launch_authorization_sha256": sha(auth_arg),
    "capability_snapshot_sha256": sha(snapshot_arg),
    "rollback_backup_dir": str(Path(rollback_ledger_arg).parent),
    "rollback_ledger_sha256": sha(rollback_ledger_arg),
    "collector_state": {
        "status": state.get("status"),
        "process_epoch": state.get("process_epoch"),
        "process_restart_count": state.get("process_restart_count"),
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
print("process_epoch =", state.get("process_epoch"))
print("process_restart_count =", state.get("process_restart_count"))
print("last_heartbeat_ms =", state.get("last_heartbeat_ms"))
PY

SUCCESS=1
trap - ERR HUP INT TERM EXIT

echo "B15P1_FINAL_COLLECTOR_DEPLOYMENT_LAUNCH_V011_PASS"
echo "service_active=$final_active"
echo "service_enabled=$final_enabled"
echo "live_snapshot_sha256=$EXPECTED_SNAPSHOT_SHA"
echo "launch_authorization_sha256=$EXPECTED_AUTH_SHA"
echo "launch_report=$LAUNCH_REPORT"
echo "price_data_authorized=False"
echo "pnl_authorized=False"
echo "live_execution_authorized=False"
