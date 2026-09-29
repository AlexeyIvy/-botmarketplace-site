#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
INBOX_DIR="$REPO/docs/research/runtime-inbox"
OUT_REL="docs/research/runtime-inbox/botmarket-test-executor-namespace-diagnostic-v1.json"
OUT="$REPO/$OUT_REL"

JOB_USER="botmarket-testjob"
JOB_GROUP="botmarket-test-jobs"
RUNNER="/opt/botmarket-test-executor/job_runner.py"

die() {
  echo "BOTMARKET_TEST_EXECUTOR_NAMESPACE_DIAG_REVIEW"
  echo "reason=$1"
  exit 2
}

[[ "${EUID:-$(id -u)}" -eq 0 ]] || die "must_run_as_root"

for c in systemd-run systemctl journalctl python3 install chown chmod date id getent mkdir rm tr; do
  command -v "$c" >/dev/null 2>&1 || die "missing_tool:$c"
done

id "$JOB_USER" >/dev/null 2>&1 || die "job_user_missing"
getent group "$JOB_GROUP" >/dev/null || die "job_group_missing"
[[ -f "$RUNNER" ]] || die "job_runner_missing"

install -d -m0750 -o botmarket-github -g botmarket-github "$INBOX_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BASE="botmarket-test-nsdiag-$STAMP"
WORK="/var/lib/botmarket-test-executor/nsdiag-$STAMP"
PACKAGE="$WORK/package"
OUTPUT="$WORK/output"
MANIFEST="$WORK/job.json"

cleanup() {
  rm -rf "$WORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

install -d -m0755 -o root -g root "$WORK"
install -d -m0755 -o root -g root "$PACKAGE"
install -d -m0777 -o root -g root "$OUTPUT"
printf '%s\n' '{"diagnostic":true}' > "$MANIFEST"
chmod 0444 "$MANIFEST"

# Build the real sandbox cumulatively, one property at a time.
# Every probe executes only /usr/bin/true: no project code and no network calls.
declare -a CURRENT
declare -a STEP_NAMES
declare -a STEP_ARGS

add_step() {
  STEP_NAMES+=("$1")
  STEP_ARGS+=("$2")
}

add_step "baseline" ""
add_step "user" "--property=User=$JOB_USER"
add_step "group" "--property=Group=$JOB_GROUP"
add_step "working_directory" "--property=WorkingDirectory=$PACKAGE"
add_step "umask" "--property=UMask=0027"
add_step "tasks_max" "--property=TasksMax=64"
add_step "memory_max" "--property=MemoryMax=1073741824"
add_step "cpu_quota" "--property=CPUQuota=200%"
add_step "limit_fsize" "--property=LimitFSIZE=67108864"
add_step "no_new_privileges" "--property=NoNewPrivileges=yes"
add_step "private_tmp" "--property=PrivateTmp=yes"
add_step "private_devices" "--property=PrivateDevices=yes"
add_step "protect_system" "--property=ProtectSystem=strict"
add_step "protect_home" "--property=ProtectHome=yes"
add_step "protect_kernel_tunables" "--property=ProtectKernelTunables=yes"
add_step "protect_kernel_modules" "--property=ProtectKernelModules=yes"
add_step "protect_control_groups" "--property=ProtectControlGroups=yes"
add_step "protect_kernel_logs" "--property=ProtectKernelLogs=yes"
add_step "protect_clock" "--property=ProtectClock=yes"
add_step "protect_hostname" "--property=ProtectHostname=yes"
add_step "protect_proc" "--property=ProtectProc=invisible"
add_step "proc_subset" "--property=ProcSubset=pid"
add_step "restrict_suid_sgid" "--property=RestrictSUIDSGID=yes"
add_step "restrict_realtime" "--property=RestrictRealtime=yes"
add_step "restrict_namespaces" "--property=RestrictNamespaces=yes"
add_step "lock_personality" "--property=LockPersonality=yes"
add_step "capability_bounding_set_empty" "--property=CapabilityBoundingSet="
add_step "ambient_capabilities_empty" "--property=AmbientCapabilities="
add_step "readonly_paths" "--property=ReadOnlyPaths=$PACKAGE $MANIFEST $RUNNER"
add_step "readwrite_paths" "--property=ReadWritePaths=$OUTPUT"

for p in   "/etc/botmarket-research"   "/etc/botmarket-github-control"   "/etc/botmarket-test-executor"   "/var/lib/botmarket-github-control"   "/var/lib/botmarket-test-executor/repo"   "/var/lib/botmarket-test-executor/ssh"   "/var/lib/botmarket-runner"   "/var/lib/botmarket-runner-probe"   "/var/lib/botmarket-tunnel"   "/run/systemd"   "/run/dbus"   "/var/run/docker.sock"   "/run/containerd"
do
  if [[ -e "$p" ]]; then
    key="$(printf '%s' "$p" | tr '/.-' '___')"
    add_step "inaccessible_${key}" "--property=InaccessiblePaths=$p"
  fi
done

add_step "private_network" "--property=PrivateNetwork=yes"
add_step "restrict_address_families" "--property=RestrictAddressFamilies=AF_UNIX"

RESULT_TMP="$WORK/result.json"
python3 - "$RESULT_TMP" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({
  "schema":"botmarket.test_executor_namespace_diagnostic.v1",
  "status":"RUNNING",
  "stages":[],
  "network_access_performed":False,
  "project_code_executed":False
},indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY

FIRST_FAIL=""
LAST_PASS=""
FAIL_ARG=""

for i in "${!STEP_NAMES[@]}"; do
  name="${STEP_NAMES[$i]}"
  arg="${STEP_ARGS[$i]}"

  if [[ -n "$arg" ]]; then
    CURRENT+=("$arg")
  fi

  unit="$BASE-$i"

  set +e
  launch_out="$(systemd-run --wait     --unit="$unit"     --description="BotMarketplace Test Executor namespace diagnostic: $name"     --property=Type=exec     --property=RuntimeMaxSec=20     "${CURRENT[@]}"     /usr/bin/true 2>&1)"
  rc=$?
  set -e

  load_state="$(systemctl show "$unit" -p LoadState --value 2>/dev/null || true)"
  active="$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || true)"
  sub="$(systemctl show "$unit" -p SubState --value 2>/dev/null || true)"
  result="$(systemctl show "$unit" -p Result --value 2>/dev/null || true)"
  main_code="$(systemctl show "$unit" -p ExecMainCode --value 2>/dev/null || true)"
  main_status="$(systemctl show "$unit" -p ExecMainStatus --value 2>/dev/null || true)"
  journal="$(journalctl -u "$unit" -n40 --no-pager -o cat 2>/dev/null || true)"

  if [[ $rc -eq 0 ]]; then
    passed="true"
    LAST_PASS="$name"
  else
    passed="false"
    if [[ -z "$FIRST_FAIL" ]]; then
      FIRST_FAIL="$name"
      FAIL_ARG="$arg"
    fi
  fi

  python3 - "$RESULT_TMP" "$name" "$arg" "$rc" "$passed"     "$load_state" "$active" "$sub" "$result" "$main_code" "$main_status"     "$launch_out" "$journal" <<'PY'
import json,sys
from pathlib import Path

p=Path(sys.argv[1])
o=json.loads(p.read_text(encoding="utf-8"))
o["stages"].append({
  "name":sys.argv[2],
  "added_property":sys.argv[3] or None,
  "systemd_run_exit_code":int(sys.argv[4]),
  "pass":sys.argv[5]=="true",
  "load_state":sys.argv[6] or None,
  "active_state":sys.argv[7] or None,
  "sub_state":sys.argv[8] or None,
  "result":sys.argv[9] or None,
  "exec_main_code":sys.argv[10] or None,
  "exec_main_status":sys.argv[11] or None,
  "launch_output":sys.argv[12][-5000:],
  "journal_tail":sys.argv[13][-12000:],
})
p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY

  systemctl stop "$unit" >/dev/null 2>&1 || true
  systemctl reset-failed "$unit" >/dev/null 2>&1 || true

  if [[ "$passed" == "false" ]]; then
    break
  fi
done

ISOLATED_CONFIRMATION="NOT_RUN"
if [[ -n "$FIRST_FAIL" && -n "$FAIL_ARG" ]]; then
  confirm_unit="$BASE-confirm"
  declare -a CONFIRM=(
    "--property=User=$JOB_USER"
    "--property=Group=$JOB_GROUP"
    "--property=WorkingDirectory=$PACKAGE"
    "--property=UMask=0027"
    "--property=TasksMax=64"
    "--property=MemoryMax=1073741824"
    "--property=CPUQuota=200%"
    "--property=LimitFSIZE=67108864"
    "$FAIL_ARG"
  )
  set +e
  confirm_out="$(systemd-run --wait     --unit="$confirm_unit"     --description="BotMarketplace Test Executor namespace diagnostic isolated confirm"     --property=Type=exec     --property=RuntimeMaxSec=20     "${CONFIRM[@]}"     /usr/bin/true 2>&1)"
  confirm_rc=$?
  set -e
  confirm_journal="$(journalctl -u "$confirm_unit" -n40 --no-pager -o cat 2>/dev/null || true)"
  if [[ $confirm_rc -eq 0 ]]; then
    ISOLATED_CONFIRMATION="PASS_PROPERTY_ALONE_INTERACTION_FAILURE"
  else
    ISOLATED_CONFIRMATION="FAIL_PROPERTY_ALONE"
  fi
  python3 - "$RESULT_TMP" "$FIRST_FAIL" "$FAIL_ARG" "$confirm_rc" "$ISOLATED_CONFIRMATION" "$confirm_out" "$confirm_journal" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
o=json.loads(p.read_text(encoding="utf-8"))
o["isolated_confirmation"]={
  "first_failing_stage":sys.argv[2],
  "property":sys.argv[3],
  "systemd_run_exit_code":int(sys.argv[4]),
  "classification":sys.argv[5],
  "launch_output":sys.argv[6][-5000:],
  "journal_tail":sys.argv[7][-12000:],
}
p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
  systemctl stop "$confirm_unit" >/dev/null 2>&1 || true
  systemctl reset-failed "$confirm_unit" >/dev/null 2>&1 || true
fi

python3 - "$RESULT_TMP" "$LAST_PASS" "$FIRST_FAIL" "$ISOLATED_CONFIRMATION" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
o=json.loads(p.read_text(encoding="utf-8"))
last_pass,first_fail,confirm=sys.argv[2:5]
o["last_passing_stage"]=last_pass or None
o["first_failing_stage"]=first_fail or None
o["isolated_confirmation_classification"]=None if confirm=="NOT_RUN" else confirm
o["status"]="PASS_ALL" if not first_fail else "FAIL_LOCALIZED"
p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY

install -m0640 -o botmarket-github -g botmarket-github "$RESULT_TMP" "$OUT"

echo "BOTMARKET_TEST_EXECUTOR_NAMESPACE_DIAGNOSTIC_COMPLETE"
echo "result=$OUT_REL"
python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("status =",o.get("status"))
print("last_passing_stage =",o.get("last_passing_stage"))
print("first_failing_stage =",o.get("first_failing_stage"))
print("isolated_confirmation =",o.get("isolated_confirmation_classification"))
for s in o.get("stages",[]):
    print(
        s["name"],
        "PASS" if s.get("pass") else "FAIL",
        "added="+str(s.get("added_property")),
        "rc="+str(s.get("systemd_run_exit_code")),
        "result="+str(s.get("result")),
        "exec_main_status="+str(s.get("exec_main_status")),
    )
PY
