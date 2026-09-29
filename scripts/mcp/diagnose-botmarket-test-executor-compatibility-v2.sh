#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
INBOX_DIR="$REPO/docs/research/runtime-inbox"
OUT_REL="docs/research/runtime-inbox/botmarket-test-executor-compatibility-v2.json"
OUT="$REPO/$OUT_REL"

JOB_USER="botmarket-testjob"
JOB_GROUP="botmarket-test-jobs"
RUNNER="/opt/botmarket-test-executor/job_runner.py"
PY="/opt/botmarket-research/venv/bin/python"
PUBLIC_RESOLV="/var/lib/botmarket-test-executor/public-resolv.conf"

die(){ echo "BOTMARKET_TEST_COMPAT_V2_REVIEW"; echo "reason=$1"; exit 2; }

[[ "${EUID:-$(id -u)}" -eq 0 ]] || die "must_run_as_root"
for c in systemd-run systemctl journalctl python3 install chown chmod date id getent mkdir rm sha256sum curl; do
  command -v "$c" >/dev/null 2>&1 || die "missing_tool:$c"
done
id "$JOB_USER" >/dev/null 2>&1 || die "job_user_missing"
getent group "$JOB_GROUP" >/dev/null || die "job_group_missing"
[[ -f "$RUNNER" ]] || die "job_runner_missing"
[[ -x "$PY" ]] || die "python_missing"
[[ -f "$PUBLIC_RESOLV" ]] || die "public_resolver_missing"

install -d -m0750 -o botmarket-github -g botmarket-github "$INBOX_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BASE="botmarket-test-compat2-$STAMP"
WORK="/var/lib/botmarket-test-executor/compat2-$STAMP"
JOBS="/var/lib/botmarket-test-executor/jobs"
JOB_ID="job_20260929T000000Z_abcdef12"
JOB_DIR="$JOBS/$JOB_ID"
PACKAGE="$JOB_DIR/package"
OUTPUT="$JOB_DIR/output"
MANIFEST="$JOB_DIR/job.json"

cleanup(){
  rm -rf "$WORK" "$JOB_DIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT

install -d -m0755 -o root -g root "$WORK"
rm -rf "$JOB_DIR"
install -d -m2750 -o botmarket-testctl -g "$JOB_GROUP" "$JOB_DIR"
install -d -m2750 -o botmarket-testctl -g "$JOB_GROUP" "$PACKAGE"
install -d -m2770 -o botmarket-testctl -g "$JOB_GROUP" "$OUTPUT"

cat > "$PACKAGE/test.py" <<'PY'
print("BOTMARKET_COMPAT_V2_JOB_RUNNER_PASS")
PY
chown botmarket-testctl:"$JOB_GROUP" "$PACKAGE/test.py"
chmod 0440 "$PACKAGE/test.py"
EP_SHA="$(sha256sum "$PACKAGE/test.py" | awk '{print $1}')"
cat > "$MANIFEST" <<EOF
{
  "schema": "botmarket.test_job.v1",
  "job_id": "$JOB_ID",
  "created_utc": "2026-09-29T00:00:00+00:00",
  "repo_head": "0000000000000000000000000000000000000000",
  "repo_url": "diagnostic",
  "entrypoint": "test.py",
  "entrypoint_sha256": "$EP_SHA",
  "args": [],
  "network_profile": "offline",
  "timeout_seconds": 20,
  "snapshot_file_count": 1,
  "snapshot_bytes": 1,
  "trading_credentials_available": false
}
EOF
chown botmarket-testctl:"$JOB_GROUP" "$MANIFEST"
chmod 0440 "$MANIFEST"

RESULT_TMP="$WORK/result.json"
python3 - "$RESULT_TMP" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({
  "schema":"botmarket.test_executor_compatibility_v2",
  "status":"RUNNING",
  "checks":[],
  "network_access_performed_only_in_public_smoke":True,
  "project_code_executed":False
},indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY

publish_result(){
  install -m0640 -o botmarket-github -g botmarket-github "$RESULT_TMP" "$OUT"
}

fail_with_result(){
  local stage="$1"
  python3 - "$RESULT_TMP" "$stage" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); o=json.loads(p.read_text(encoding="utf-8"))
o["status"]="REVIEW"
o["failure_stage"]=sys.argv[2]
p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
  publish_result
  echo "BOTMARKET_TEST_COMPAT_V2_REVIEW"
  echo "failure_stage=$stage"
  echo "result=$OUT_REL"
  exit 2
}

declare -a BASE_PROPS=(
  "--property=User=$JOB_USER"
  "--property=Group=$JOB_GROUP"
  "--property=WorkingDirectory=$PACKAGE"
  "--property=UMask=0027"
  "--property=TasksMax=64"
  "--property=MemoryMax=1073741824"
  "--property=CPUQuota=200%"
  "--property=LimitFSIZE=67108864"
  "--property=NoNewPrivileges=yes"
  "--property=PrivateTmp=yes"
  "--property=PrivateDevices=yes"
  "--property=ProtectSystem=strict"
  "--property=ProtectHome=yes"
  "--property=ProtectKernelTunables=yes"
  "--property=ProtectKernelModules=yes"
  "--property=ProtectControlGroups=yes"
  "--property=ProtectKernelLogs=yes"
  "--property=ProtectClock=yes"
  "--property=ProtectHostname=yes"
  "--property=ProtectProc=invisible"
  "--property=ProcSubset=pid"
  "--property=RestrictSUIDSGID=yes"
  "--property=RestrictRealtime=yes"
  "--property=RestrictNamespaces=yes"
  "--property=LockPersonality=yes"
  "--property=CapabilityBoundingSet="
  "--property=AmbientCapabilities="
  "--property=ReadOnlyPaths=$PACKAGE $MANIFEST $RUNNER"
  "--property=ReadWritePaths=$OUTPUT"
)

for p in   "/etc/botmarket-research"   "/etc/botmarket-github-control"   "/etc/botmarket-test-executor"   "/var/lib/botmarket-github-control"   "/var/lib/botmarket-test-executor/repo"   "/var/lib/botmarket-test-executor/ssh"   "/var/lib/botmarket-runner"   "/var/lib/botmarket-runner-probe"   "/var/lib/botmarket-tunnel"
do
  [[ -e "$p" ]] && BASE_PROPS+=("--property=InaccessiblePaths=$p")
done

record(){
  python3 - "$RESULT_TMP" "$@" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); o=json.loads(p.read_text(encoding="utf-8"))
o["checks"].append({
  "name":sys.argv[2],
  "exit_code":int(sys.argv[3]),
  "pass":sys.argv[4]=="true",
  "result":sys.argv[5] or None,
  "exec_main_status":sys.argv[6] or None,
  "output":sys.argv[7][-6000:],
  "journal_tail":sys.argv[8][-12000:]
})
p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
}

run_true_check(){
  local name="$1"; shift
  local unit="$BASE-$name"
  set +e
  local output
  output="$(systemd-run --wait --unit="$unit" --property=Type=exec --property=RuntimeMaxSec=20     "${BASE_PROPS[@]}" "$@" /usr/bin/true 2>&1)"
  local rc=$?
  set -e
  local result status journal passed
  result="$(systemctl show "$unit" -p Result --value 2>/dev/null || true)"
  status="$(systemctl show "$unit" -p ExecMainStatus --value 2>/dev/null || true)"
  journal="$(journalctl -u "$unit" -n50 --no-pager -o cat 2>/dev/null || true)"
  [[ $rc -eq 0 ]] && passed=true || passed=false
  record "$name" "$rc" "$passed" "$result" "$status" "$output" "$journal"
  systemctl stop "$unit" >/dev/null 2>&1 || true
  systemctl reset-failed "$unit" >/dev/null 2>&1 || true
  [[ "$passed" == true ]]
}

# 1. Known-good base without /run/systemd.
run_true_check "base_without_run_systemd" || fail_with_result "base_without_run_systemd"

# 2. Replace broad /run/systemd mask with the narrow control socket only.
if [[ -e /run/systemd/private ]]; then
  run_true_check "mask_systemd_private_socket" "--property=InaccessiblePaths=/run/systemd/private"     || fail_with_result "mask_systemd_private_socket"
  BASE_PROPS+=("--property=InaccessiblePaths=/run/systemd/private")
fi

# 3. Continue remaining host-control masks after the point where v1 stopped.
if [[ -e /run/dbus ]]; then
  run_true_check "mask_run_dbus" "--property=InaccessiblePaths=/run/dbus"     || fail_with_result "mask_run_dbus"
  BASE_PROPS+=("--property=InaccessiblePaths=/run/dbus")
fi
if [[ -e /var/run/docker.sock ]]; then
  run_true_check "mask_docker_socket" "--property=InaccessiblePaths=/var/run/docker.sock"     || fail_with_result "mask_docker_socket"
  BASE_PROPS+=("--property=InaccessiblePaths=/var/run/docker.sock")
fi
if [[ -e /run/containerd ]]; then
  run_true_check "mask_containerd" "--property=InaccessiblePaths=/run/containerd"     || fail_with_result "mask_containerd"
  BASE_PROPS+=("--property=InaccessiblePaths=/run/containerd")
fi

# 4. Full offline namespace.
run_true_check "offline_private_network" "--property=PrivateNetwork=yes"   || fail_with_result "offline_private_network"
run_true_check "offline_af_unix" "--property=PrivateNetwork=yes" "--property=RestrictAddressFamilies=AF_UNIX"   || fail_with_result "offline_af_unix"

# 5. Execute the real job_runner inside the candidate offline sandbox.
rm -f "$OUTPUT/job_result.json" "$OUTPUT/run.log"
unit="$BASE-real-runner"
set +e
runner_out="$(systemd-run --wait --unit="$unit" --property=Type=exec --property=RuntimeMaxSec=50   "${BASE_PROPS[@]}"   "--property=PrivateNetwork=yes"   "--property=RestrictAddressFamilies=AF_UNIX"   "$PY" "$RUNNER" "$JOB_ID" 2>&1)"
runner_rc=$?
set -e
runner_result="$(systemctl show "$unit" -p Result --value 2>/dev/null || true)"
runner_status="$(systemctl show "$unit" -p ExecMainStatus --value 2>/dev/null || true)"
runner_journal="$(journalctl -u "$unit" -n80 --no-pager -o cat 2>/dev/null || true)"
runner_pass=false
if [[ $runner_rc -eq 0 && -f "$OUTPUT/job_result.json" && -f "$OUTPUT/run.log" ]]; then
  if grep -q 'BOTMARKET_COMPAT_V2_JOB_RUNNER_PASS' "$OUTPUT/run.log"; then
    runner_pass=true
  fi
fi
record "real_job_runner_offline" "$runner_rc" "$runner_pass" "$runner_result" "$runner_status" "$runner_out" "$runner_journal"
systemctl stop "$unit" >/dev/null 2>&1 || true
systemctl reset-failed "$unit" >/dev/null 2>&1 || true
[[ "$runner_pass" == true ]] || fail_with_result "real_job_runner_offline"

# 6. Public-research namespace/property compatibility with harmless true.
declare -a PUBLIC_PROPS=(
  "${BASE_PROPS[@]}"
  "--property=PrivateNetwork=no"
  "--property=RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6"
  "--property=BindReadOnlyPaths=$PUBLIC_RESOLV:/etc/resolv.conf"
  "--property=IPAddressDeny=127.0.0.0/8"
  "--property=IPAddressDeny=::1/128"
  "--property=IPAddressDeny=10.0.0.0/8"
  "--property=IPAddressDeny=172.16.0.0/12"
  "--property=IPAddressDeny=192.168.0.0/16"
  "--property=IPAddressDeny=169.254.0.0/16"
  "--property=IPAddressDeny=fc00::/7"
  "--property=IPAddressDeny=fe80::/10"
  "--property=IPAddressDeny=224.0.0.0/4"
  "--property=IPAddressDeny=ff00::/8"
)
unit="$BASE-public-props"
set +e
public_prop_out="$(systemd-run --wait --unit="$unit" --property=Type=exec --property=RuntimeMaxSec=30   "${PUBLIC_PROPS[@]}" /usr/bin/true 2>&1)"
public_prop_rc=$?
set -e
public_prop_result="$(systemctl show "$unit" -p Result --value 2>/dev/null || true)"
public_prop_status="$(systemctl show "$unit" -p ExecMainStatus --value 2>/dev/null || true)"
public_prop_journal="$(journalctl -u "$unit" -n80 --no-pager -o cat 2>/dev/null || true)"
[[ $public_prop_rc -eq 0 ]] && public_prop_pass=true || public_prop_pass=false
record "public_profile_properties" "$public_prop_rc" "$public_prop_pass" "$public_prop_result" "$public_prop_status" "$public_prop_out" "$public_prop_journal"
systemctl stop "$unit" >/dev/null 2>&1 || true
systemctl reset-failed "$unit" >/dev/null 2>&1 || true
[[ "$public_prop_pass" == true ]] || fail_with_result "public_profile_properties"

# 7. Public HTTPS works while loopback MCP remains blocked.
cat > "$PACKAGE/public_probe.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
code="$(curl -4 --http1.1 -sS --max-time 15 -o /dev/null -w '%{http_code}' https://announcements.bybit.com/en-US/)"
[[ "$code" =~ ^[23] ]] || { echo "PUBLIC_HTTP_CODE=$code"; exit 11; }
if curl -sS --max-time 2 http://127.0.0.1:8768/mcp >/dev/null 2>&1; then
  echo "LOOPBACK_MCP_REACHABLE"
  exit 12
fi
echo "PUBLIC_RESEARCH_NETWORK_BOUNDARY_PASS"
SH
chmod 0555 "$PACKAGE/public_probe.sh"
unit="$BASE-public-net"
set +e
public_out="$(systemd-run --wait --unit="$unit" --property=Type=exec --property=RuntimeMaxSec=60   "${PUBLIC_PROPS[@]}" /usr/bin/bash "$PACKAGE/public_probe.sh" 2>&1)"
public_rc=$?
set -e
public_result="$(systemctl show "$unit" -p Result --value 2>/dev/null || true)"
public_status="$(systemctl show "$unit" -p ExecMainStatus --value 2>/dev/null || true)"
public_journal="$(journalctl -u "$unit" -n80 --no-pager -o cat 2>/dev/null || true)"
[[ $public_rc -eq 0 ]] && public_pass=true || public_pass=false
record "public_research_network_smoke" "$public_rc" "$public_pass" "$public_result" "$public_status" "$public_out" "$public_journal"
systemctl stop "$unit" >/dev/null 2>&1 || true
systemctl reset-failed "$unit" >/dev/null 2>&1 || true
[[ "$public_pass" == true ]] || fail_with_result "public_research_network_smoke"

python3 - "$RESULT_TMP" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); o=json.loads(p.read_text(encoding="utf-8"))
o["status"]="PASS" if all(x.get("pass") for x in o["checks"]) else "REVIEW"
o["recommended_systemd_control_mask"]="InaccessiblePaths=/run/systemd/private" if any(
    x["name"]=="mask_systemd_private_socket" for x in o["checks"]
) else "NONE_REQUIRED_PATH_ABSENT"
p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY

publish_result
echo "BOTMARKET_TEST_EXECUTOR_COMPATIBILITY_V2_COMPLETE"
echo "result=$OUT_REL"
python3 - "$OUT" <<'PY'
import json,sys
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("status =",o.get("status"))
print("recommended_systemd_control_mask =",o.get("recommended_systemd_control_mask"))
for x in o.get("checks",[]):
    print(x["name"],"PASS" if x.get("pass") else "FAIL",
          "rc="+str(x.get("exit_code")),
          "result="+str(x.get("result")),
          "exec_main_status="+str(x.get("exec_main_status")))
PY
