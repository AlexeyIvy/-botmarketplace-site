#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO_NAME="${BM_TEST_REPO:-AlexeyIvy/-botmarketplace-site}"
REPO_URL="git@github.com:${REPO_NAME}.git"
BRANCH="${BM_TEST_BRANCH:-main}"

CTL_USER="botmarket-testctl"
CTL_GROUP="botmarket-testctl"
JOB_USER="botmarket-testjob"
JOB_GROUP="botmarket-test-jobs"

STATE="/var/lib/botmarket-test-executor"
REPODIR="$STATE/repo"
SSHDIR="$STATE/ssh"
JOBS="$STATE/jobs"
KEY="$SSHDIR/id_ed25519"
KH="$SSHDIR/known_hosts"

APP="/opt/botmarket-test-executor"
CONF="/etc/botmarket-test-executor"
ENVF="$CONF/env"
POLICY="$CONF/policy.json"
UNIT="/etc/systemd/system/botmarket-test-executor.service"
SUDOERS="/etc/sudoers.d/botmarket-test-executor"

LAUNCHER="/usr/local/sbin/botmarket-test-launch"
CANCELER="/usr/local/sbin/botmarket-test-cancel"
PRUNER="/usr/local/sbin/botmarket-test-prune"

PY="${BM_TEST_PYTHON:-/opt/botmarket-research/venv/bin/python}"
HOST="127.0.0.1"
PORT="${BM_TEST_PORT:-8769}"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/botmarket-test-executor-backups/$TS"

log(){ printf '\n[%s] %s\n' "$1" "$2"; }
die(){ echo "[FAIL] $*" >&2; exit 1; }

as_testctl_root() {
  runuser -u "$CTL_USER" -- sudo -n -- "$@"
}

retry_cmd() {
  local max_attempts="$1"; shift
  local attempt=1 rc=0
  while true; do
    if "$@"; then
      return 0
    else
      rc=$?
    fi
    if (( attempt >= max_attempts )); then
      return "$rc"
    fi
    echo "[RETRY] command failed rc=$rc attempt=$attempt/$max_attempts; retrying in $((attempt*2))s" >&2
    sleep "$((attempt*2))"
    attempt=$((attempt+1))
  done
}

explicit_readonly_denial() {
  local msg="$1"
  grep -Fqi 'The key you are authenticating with has been marked as read only.' <<<"$msg" \
    || grep -Eqi 'write access.*not granted|permission to .* denied|deploy key.*read.?only|permission denied.*write' <<<"$msg"
}

SERVICE_WAS_ACTIVE=0
systemctl is-active --quiet botmarket-test-executor.service 2>/dev/null && SERVICE_WAS_ACTIVE=1 || true

[[ "${EUID:-$(id -u)}" -eq 0 ]] || die "Run as root"

log STEP "Preflight"
for c in git ssh ssh-keygen ssh-keyscan systemctl journalctl runuser curl ss sudo visudo sha256sum awk install getent useradd groupadd usermod id grep sort chmod chown mv rm cp mktemp seq; do
  command -v "$c" >/dev/null || die "$c missing"
done
[[ -x "$PY" ]] || die "Python missing: $PY"

READONLY_SAMPLE= | awk '{print $4}' | grep -Eq "(^|:)${PORT}$"   && ! systemctl is-active --quiet botmarket-test-executor.service 2>/dev/null; then
  die "Port $PORT is occupied"
fi

"$PY" - <<'PY'
try:
    from mcp.server.mcpserver import MCPServer
except Exception:
    from mcp.server.fastmcp import FastMCP as MCPServer
print("MCP_SDK_IMPORT=PASS")
PY

log STEP "Create isolated users and directories"
getent group "$CTL_GROUP" >/dev/null || groupadd --system "$CTL_GROUP"
getent group "$JOB_GROUP" >/dev/null || groupadd --system "$JOB_GROUP"

id "$CTL_USER" >/dev/null 2>&1 ||   useradd --system --gid "$CTL_GROUP" --home-dir "$STATE" --create-home --shell /usr/sbin/nologin "$CTL_USER"
id "$JOB_USER" >/dev/null 2>&1 ||   useradd --system --gid "$JOB_GROUP" --home-dir /nonexistent --shell /usr/sbin/nologin "$JOB_USER"

usermod -a -G "$JOB_GROUP" "$CTL_USER"

install -d -m0755 -o root -g root "$APP" "$CONF"
install -d -m0750 -o "$CTL_USER" -g "$JOB_GROUP" "$STATE"
install -d -m0700 -o "$CTL_USER" -g "$CTL_GROUP" "$SSHDIR"
install -d -m2770 -o "$CTL_USER" -g "$JOB_GROUP" "$JOBS"
install -d -m0700 -o root -g root "$BACKUP"

for f in "$APP/server.py" "$APP/job_runner.py" "$LAUNCHER" "$CANCELER" "$PRUNER" "$ENVF" "$POLICY" "$UNIT" "$SUDOERS"; do
  [[ -f "$f" ]] && cp -a "$f" "$BACKUP/$(basename "$f").bak"
done

log STEP "Create/read-only GitHub deploy key"
: > "$KH"
for f in /var/lib/botmarket-github-control/ssh/known_hosts /home/botmarket/.ssh/known_hosts /root/.ssh/known_hosts; do
  [[ -r "$f" ]] && grep -E 'github\.com' "$f" >> "$KH" 2>/dev/null || true
done
[[ -s "$KH" ]] || ssh-keyscan -T10 -H github.com >> "$KH" 2>/dev/null || true
[[ -s "$KH" ]] || die "Cannot obtain GitHub host key"
sort -u "$KH" -o "$KH"
chown "$CTL_USER:$CTL_GROUP" "$KH"
chmod 0644 "$KH"

[[ -f "$KEY" ]] ||   ssh-keygen -q -t ed25519 -N '' -C "botmarket-test-executor@$(hostname)" -f "$KEY"
chown "$CTL_USER:$CTL_GROUP" "$KEY" "$KEY.pub"
chmod 0600 "$KEY"
chmod 0644 "$KEY.pub"

SSH="ssh -i $KEY -o IdentitiesOnly=yes -o UserKnownHostsFile=$KH -o StrictHostKeyChecking=yes -o BatchMode=yes"

READ=""
RC=1
for attempt in 1 2 3 4; do
  set +e
  READ="$(runuser -u "$CTL_USER" -- env GIT_SSH_COMMAND="$SSH" git ls-remote "$REPO_URL" "refs/heads/$BRANCH" 2>&1)"
  RC=$?
  set -e
  [[ $RC -eq 0 ]] && break
  if (( attempt < 4 )); then
    echo "[RETRY] GitHub read probe failed rc=$RC attempt=$attempt/4; retrying in $((attempt*2))s" >&2
    sleep "$((attempt*2))"
  fi
done
if [[ $RC -ne 0 ]]; then
  if grep -Eqi 'Permission denied \(publickey\)|Repository not found|repository access denied' <<<"$READ"; then
    echo
    echo "TEST_EXECUTOR_DEPLOY_KEY_NOT_AUTHORIZED_YET"
    echo "Repository: $REPO_NAME"
    echo "GitHub -> Settings -> Deploy keys -> Add deploy key"
    echo "Title: BotMarketplace Test Executor READ ONLY"
    echo "IMPORTANT: DO NOT enable 'Allow write access'"
    echo
    cat "$KEY.pub"
    echo
    echo "After authorizing this READ-ONLY key, rerun this same installer."
    exit 3
  fi
  die "GITHUB_READ_TRANSPORT_FAILURE after 4 attempts: ${READ:0:1200}"
fi

REMOTE_SHA="$(awk 'NF>=2{print $1;exit}' <<<"$READ")"
[[ "$REMOTE_SHA" =~ ^[0-9a-f]{40,64}$ ]] || die "Cannot parse remote branch SHA"
echo "GITHUB_READ=PASS"

log STEP "Create/refresh dedicated read-only clone"
if [[ -d "$REPODIR/.git" ]]; then
  ORIGIN="$(runuser -u "$CTL_USER" -- git -C "$REPODIR" remote get-url origin)"
  [[ "$ORIGIN" == "$REPO_URL" ]] || die "Unexpected origin: $ORIGIN"
  [[ -z "$(runuser -u "$CTL_USER" -- git -C "$REPODIR" status --porcelain=v1)" ]] || die "Test Executor clone is dirty"
  retry_cmd 4 runuser -u "$CTL_USER" -- env GIT_SSH_COMMAND="$SSH" git -C "$REPODIR" fetch --prune origin "$BRANCH" \
    || die "Git fetch failed after retries"
  runuser -u "$CTL_USER" -- git -C "$REPODIR" checkout "$BRANCH"
  runuser -u "$CTL_USER" -- git -C "$REPODIR" merge --ff-only "origin/$BRANCH"
else
  CLONE_OK=0
  for attempt in 1 2 3 4; do
    rm -rf "$REPODIR"
    if runuser -u "$CTL_USER" -- env GIT_SSH_COMMAND="$SSH" git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$REPODIR"; then
      CLONE_OK=1
      break
    fi
    if (( attempt < 4 )); then
      echo "[RETRY] Git clone failed attempt=$attempt/4; retrying in $((attempt*2))s" >&2
      sleep "$((attempt*2))"
    fi
  done
  [[ "$CLONE_OK" -eq 1 ]] || die "Git clone failed after retries"
fi
chmod 0700 "$REPODIR"
LOCAL_HEAD="$(runuser -u "$CTL_USER" -- git -C "$REPODIR" rev-parse HEAD)"
[[ "$LOCAL_HEAD" == "$REMOTE_SHA" ]] || die "Clone HEAD != origin/$BRANCH"
echo "TEST_EXECUTOR_REPO_HEAD=$LOCAL_HEAD"

log STEP "Verify deploy key is truly read-only"
WRITE_PROBE=""
WRITE_RC=1
for attempt in 1 2 3; do
  set +e
  WRITE_PROBE="$(runuser -u "$CTL_USER" -- env GIT_SSH_COMMAND="$SSH" git -C "$REPODIR" push --dry-run origin "HEAD:refs/heads/__botmarket_test_executor_write_probe__" 2>&1)"
  WRITE_RC=$?
  set -e
  if [[ $WRITE_RC -eq 0 ]]; then
    die "Deploy key appears write-enabled. Disable 'Allow write access' before continuing."
  fi
  if explicit_readonly_denial "$WRITE_PROBE"; then
    break
  fi
  if (( attempt < 3 )); then
    echo "[RETRY] GitHub write-denial probe was transport-indeterminate attempt=$attempt/3; retrying in $((attempt*2))s" >&2
    sleep "$((attempt*2))"
  fi
done
if ! explicit_readonly_denial "$WRITE_PROBE"; then
  die "GITHUB_WRITE_DENIAL_INDETERMINATE: ${WRITE_PROBE:0:1200}"
fi
echo "GITHUB_WRITE=DENIED_AS_REQUIRED"

log STEP "Prepare isolated public-research DNS"
PUBLIC_RESOLV="$STATE/public-resolv.conf"
"$PY" - "$PUBLIC_RESOLV.tmp" <<'PY'
import ipaddress,sys
from pathlib import Path

out=Path(sys.argv[1])
seen=[]
for src in (Path("/run/systemd/resolve/resolv.conf"),Path("/etc/resolv.conf")):
    try:
        lines=src.read_text(encoding="utf-8",errors="ignore").splitlines()
    except Exception:
        continue
    for line in lines:
        parts=line.split()
        if len(parts)<2 or parts[0]!="nameserver":
            continue
        try:
            ip=ipaddress.ip_address(parts[1].split("%",1)[0])
        except ValueError:
            continue
        if ip.is_global and str(ip) not in seen:
            seen.append(str(ip))
if not seen:
    seen=["1.1.1.1","8.8.8.8"]
out.write_text("".join(f"nameserver {ip}\n" for ip in seen[:3]),encoding="utf-8")
PY
mv "$PUBLIC_RESOLV.tmp" "$PUBLIC_RESOLV"
chown root:"$JOB_GROUP" "$PUBLIC_RESOLV"
chmod 0440 "$PUBLIC_RESOLV"

log STEP "Install policy"
cat > "$POLICY" <<'JSON'
{
  "schema": "botmarket.test_executor_policy.v1",
  "allowed_entrypoint_prefixes": [
    "research/",
    "scripts/research/",
    "tests/"
  ],
  "allowed_entrypoint_suffixes": [
    ".py",
    ".sh"
  ],
  "network_profiles": [
    "offline",
    "public_research"
  ],
  "max_timeout_seconds": 900,
  "default_timeout_seconds": 180,
  "max_runs_per_rolling_hour": 6,
  "max_runs_per_utc_day": 30,
  "max_concurrent_jobs": 1,
  "max_args": 24,
  "max_arg_bytes": 512,
  "max_repo_archive_bytes": 134217728,
  "max_repo_files": 6000,
  "max_output_file_bytes": 67108864,
  "completed_job_retention_days": 7,
  "max_retained_jobs": 100,
  "memory_max_bytes": 1073741824,
  "tasks_max": 64,
  "cpu_quota_percent": 200,
  "public_research_blocks_loopback_private_and_link_local": true,
  "public_research_resolver_file": "/var/lib/botmarket-test-executor/public-resolv.conf",
  "trading_credentials_available_to_jobs": false,
  "arbitrary_shell_tool": false,
  "repo_write": false,
  "sudo_inside_job": false
}
JSON
chown root:"$CTL_GROUP" "$POLICY"
chmod 0640 "$POLICY"

cat > "$ENVF" <<EOF
BM_TEST_STATE=$STATE
BM_TEST_REPO_DIR=$REPODIR
BM_TEST_REPO_URL=$REPO_URL
BM_TEST_BRANCH=$BRANCH
BM_TEST_SSH_KEY=$KEY
BM_TEST_KNOWN_HOSTS=$KH
BM_TEST_POLICY=$POLICY
BM_TEST_HOST=$HOST
BM_TEST_PORT=$PORT
BM_TEST_PYTHON=$PY
BM_TEST_JOB_GROUP=$JOB_GROUP
BM_TEST_MAX_TEXT_BYTES=262144
EOF
chown root:"$CTL_GROUP" "$ENVF"
chmod 0640 "$ENVF"

log STEP "Install sandboxed job runner"
cat > "$APP/job_runner.py" <<PY
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE=Path("$JOBS").resolve()
TARGET_PY=Path("$PY")
BASH=Path("/usr/bin/bash")

def utc_now()->str:
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def atomic_json(path:Path,obj:dict)->None:
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def fail(msg:str,rc:int=125)->int:
    print(msg,file=sys.stderr,flush=True)
    return rc

def main()->int:
    if len(sys.argv)!=2:
        return fail("JOB_ID_REQUIRED")
    job_id=sys.argv[1]
    if not job_id.startswith("job_"):
        return fail("BAD_JOB_ID")

    job=(BASE/job_id).resolve()
    try:
        job.relative_to(BASE)
    except ValueError:
        return fail("JOB_ESCAPE")

    manifest_path=job/"job.json"
    package=(job/"package").resolve()
    output=(job/"output").resolve()
    result_path=output/"job_result.json"
    log_path=output/"run.log"

    started=utc_now()
    rc=125
    timed_out=False
    error=None
    command=[]

    try:
        m=json.loads(manifest_path.read_text(encoding="utf-8"))
        if m.get("schema")!="botmarket.test_job.v1" or m.get("job_id")!=job_id:
            raise RuntimeError("MANIFEST_SCHEMA_OR_ID")
        if m.get("trading_credentials_available") is not False:
            raise RuntimeError("TRADING_CREDENTIAL_BOUNDARY")
        entry_rel=m.get("entrypoint")
        if not isinstance(entry_rel,str):
            raise RuntimeError("ENTRYPOINT")
        entry=(package/entry_rel).resolve()
        entry.relative_to(package)
        if not entry.is_file() or entry.is_symlink():
            raise RuntimeError("ENTRYPOINT_NOT_FILE")
        if sha256_file(entry)!=m.get("entrypoint_sha256"):
            raise RuntimeError("ENTRYPOINT_SHA")

        args=m.get("args") or []
        if (
            not isinstance(args,list)
            or len(args)>24
            or not all(isinstance(x,str) and "\x00" not in x and len(x.encode())<=512 for x in args)
        ):
            raise RuntimeError("ARGS")
        timeout=int(m.get("timeout_seconds") or 0)
        if timeout<1 or timeout>900:
            raise RuntimeError("TIMEOUT")

        suffix=entry.suffix.lower()
        if suffix==".py":
            command=[str(TARGET_PY),str(entry),*args]
        elif suffix==".sh":
            command=[str(BASH),str(entry),*args]
        else:
            raise RuntimeError("ENTRYPOINT_SUFFIX")

        env={
            "PATH":"/usr/bin:/bin",
            "HOME":str(output/"home"),
            "LANG":"C.UTF-8",
            "LC_ALL":"C.UTF-8",
            "PYTHONUNBUFFERED":"1",
            "PYTHONDONTWRITEBYTECODE":"1",
            "BM_TEST_EXECUTOR":"1",
            "BM_TEST_NETWORK_PROFILE":str(m.get("network_profile") or "offline"),
            "BM_TEST_OUTPUT_DIR":str(output),
            "B15P2_REPO_ROOT":str(package),
            "SC001_DATA_ROOT":str(output/"data"),
        }
        (output/"home").mkdir(parents=True,exist_ok=True)
        (output/"data").mkdir(parents=True,exist_ok=True)

        with log_path.open("ab",buffering=0) as log:
            p=subprocess.Popen(
                command,
                cwd=str(package),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
            try:
                rc=p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out=True
                error="TIMEOUT"
                try:
                    os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
                rc=p.wait(timeout=10) if p.poll() is None else p.returncode
                if rc==0:
                    rc=124
    except Exception as exc:
        error=f"{type(exc).__name__}:{exc}"
        rc=125

    result={
        "schema":"botmarket.test_job_result.v1",
        "job_id":job_id,
        "started_utc":started,
        "finished_utc":utc_now(),
        "exit_code":int(rc),
        "timed_out":bool(timed_out),
        "error":error,
        "command_kind":"python" if command and command[0]==str(TARGET_PY) else ("bash" if command else None),
        "log_sha256":sha256_file(log_path) if log_path.is_file() else None,
        "network_profile":json.loads(manifest_path.read_text(encoding="utf-8")).get("network_profile") if manifest_path.is_file() else None,
    }
    atomic_json(result_path,result)
    return int(rc)

if __name__=="__main__":
    raise SystemExit(main())
PY
chmod 0755 "$APP/job_runner.py"
chown root:root "$APP/job_runner.py"
"$PY" -m py_compile "$APP/job_runner.py"

log STEP "Install root-only sandbox launcher"
cat > "$LAUNCHER" <<PY
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import pwd
import re
import subprocess
import sys
from pathlib import Path

BASE=Path("$JOBS").resolve()
RUNNER=Path("$APP/job_runner.py").resolve()
JOB_USER="$JOB_USER"
JOB_GROUP="$JOB_GROUP"
JOB_RE=re.compile(r"^job_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
ALLOWED_PREFIXES=("research/","scripts/research/","tests/")
ALLOWED_SUFFIXES={".py",".sh"}
PUBLIC_RESOLV=Path("$STATE/public-resolv.conf").resolve()

def die(msg:str)->None:
    print(f"TEST_LAUNCH_REVIEW:{msg}",file=sys.stderr)
    raise SystemExit(2)

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

if os.geteuid()!=0:
    die("ROOT_REQUIRED")

if len(sys.argv)==2 and sys.argv[1]=="--self-test":
    print("BOTMARKET_TEST_LAUNCHER_SELFTEST_PASS")
    raise SystemExit(0)

if len(sys.argv)!=2 or not JOB_RE.fullmatch(sys.argv[1]):
    die("BAD_JOB_ID")
job_id=sys.argv[1]
job=(BASE/job_id).resolve()
try:
    job.relative_to(BASE)
except ValueError:
    die("JOB_ESCAPE")

manifest_path=job/"job.json"
package=job/"package"
output=job/"output"
for p in (manifest_path,package,output):
    if not p.exists() or p.is_symlink():
        die(f"PATH_INVALID:{p.name}")

try:
    m=json.loads(manifest_path.read_text(encoding="utf-8"))
except Exception as exc:
    die(f"MANIFEST_PARSE:{type(exc).__name__}")

if m.get("schema")!="botmarket.test_job.v1" or m.get("job_id")!=job_id:
    die("MANIFEST_SCHEMA_OR_ID")
if m.get("trading_credentials_available") is not False:
    die("TRADING_CREDENTIAL_BOUNDARY")
repo_head=m.get("repo_head")
if not isinstance(repo_head,str) or not re.fullmatch(r"[0-9a-f]{40,64}",repo_head):
    die("REPO_HEAD")
args=m.get("args")
if not isinstance(args,list) or len(args)>24:
    die("ARGS")
for arg in args:
    if not isinstance(arg,str) or "\x00" in arg or len(arg.encode())>512:
        die("ARG_INVALID")

entry_rel=m.get("entrypoint")
if not isinstance(entry_rel,str):
    die("ENTRYPOINT")
installer_selftest=m.get("installer_selftest") is True
if installer_selftest:
    allowed_install_tests={
        "_deadbeef":"test.py",
        "_cafebabe":"public_test.sh",
    }
    matched=[suffix for suffix,name in allowed_install_tests.items() if job_id.endswith(suffix) and entry_rel==name]
    if len(matched)!=1:
        die("INSTALLER_SELFTEST_BOUNDARY")
else:
    norm=Path(entry_rel).as_posix().lstrip("./")
    if Path(norm).is_absolute() or ".." in Path(norm).parts or ".git" in Path(norm).parts:
        die("ENTRYPOINT_PATH")
    if not any(norm.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        die("ENTRYPOINT_PREFIX")
    if Path(norm).suffix.lower() not in ALLOWED_SUFFIXES:
        die("ENTRYPOINT_SUFFIX")
entry=(package/entry_rel).resolve()
try:
    entry.relative_to(package.resolve())
except ValueError:
    die("ENTRYPOINT_ESCAPE")
if not entry.is_file() or entry.is_symlink():
    die("ENTRYPOINT_NOT_FILE")
if sha256_file(entry)!=m.get("entrypoint_sha256"):
    die("ENTRYPOINT_SHA")

network=m.get("network_profile")
if network not in {"offline","public_research"}:
    die("NETWORK_PROFILE")
timeout=int(m.get("timeout_seconds") or 0)
if timeout<1 or timeout>900:
    die("TIMEOUT")

for root,dirs,files in os.walk(package,followlinks=False):
    rp=Path(root)
    if rp.is_symlink():
        die("PACKAGE_SYMLINK_DIR")
    for name in [*dirs,*files]:
        p=rp/name
        if p.is_symlink():
            die("PACKAGE_SYMLINK")
for root,dirs,files in os.walk(output,followlinks=False):
    rp=Path(root)
    if rp.is_symlink():
        die("OUTPUT_SYMLINK_DIR")
    for name in [*dirs,*files]:
        if (rp/name).is_symlink():
            die("OUTPUT_SYMLINK")

unit=f"botmarket-test-job-{job_id}.service"
show=subprocess.run(
    ["systemctl","show",unit,"-p","LoadState","--value"],
    text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL
)
if show.returncode==0 and show.stdout.strip() not in {"","not-found"}:
    die("UNIT_ALREADY_EXISTS")

common=[
    "systemd-run","--no-block",
    f"--unit={unit}",
    "--description=BotMarketplace isolated Test Executor job",
    "--property=Type=exec",
    f"--property=User={JOB_USER}",
    f"--property=Group={JOB_GROUP}",
    f"--property=WorkingDirectory={package}",
    "--property=UMask=0027",
    "--property=NoNewPrivileges=yes",
    "--property=PrivateTmp=yes",
    "--property=PrivateDevices=yes",
    "--property=ProtectSystem=strict",
    "--property=ProtectHome=yes",
    "--property=ProtectKernelTunables=yes",
    "--property=ProtectKernelModules=yes",
    "--property=ProtectControlGroups=yes",
    "--property=ProtectKernelLogs=yes",
    "--property=ProtectClock=yes",
    "--property=ProtectHostname=yes",
    "--property=ProtectProc=invisible",
    "--property=ProcSubset=pid",
    "--property=RestrictSUIDSGID=yes",
    "--property=RestrictRealtime=yes",
    "--property=RestrictNamespaces=yes",
    "--property=LockPersonality=yes",
    "--property=CapabilityBoundingSet=",
    "--property=AmbientCapabilities=",
    "--property=TasksMax=64",
    "--property=MemoryMax=1073741824",
    "--property=CPUQuota=200%",
    "--property=LimitFSIZE=67108864",
    f"--property=RuntimeMaxSec={timeout+30}",
    f"--property=ReadOnlyPaths={package} {manifest_path} {RUNNER}",
    f"--property=ReadWritePaths={output}",
]

for p in (
    "/etc/botmarket-research",
    "/etc/botmarket-github-control",
    "/etc/botmarket-test-executor",
    "/var/lib/botmarket-github-control",
    "$STATE/repo",
    "$STATE/ssh",
    "/var/lib/botmarket-runner",
    "/var/lib/botmarket-runner-probe",
    "/var/lib/botmarket-tunnel",
    "/run/systemd/private",
    "/run/dbus",
    "/var/run/docker.sock",
    "/run/containerd",
):
    if Path(p).exists():
        common.append(f"--property=InaccessiblePaths={p}")

if network=="offline":
    common += [
        "--property=PrivateNetwork=yes",
        "--property=RestrictAddressFamilies=AF_UNIX",
    ]
else:
    if not PUBLIC_RESOLV.is_file() or PUBLIC_RESOLV.is_symlink():
        die("PUBLIC_RESOLV")
    common += [
        "--property=PrivateNetwork=no",
        "--property=RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
        f"--property=BindReadOnlyPaths={PUBLIC_RESOLV}:/etc/resolv.conf",
        "--property=IPAddressDeny=127.0.0.0/8",
        "--property=IPAddressDeny=::1/128",
        "--property=IPAddressDeny=10.0.0.0/8",
        "--property=IPAddressDeny=172.16.0.0/12",
        "--property=IPAddressDeny=192.168.0.0/16",
        "--property=IPAddressDeny=169.254.0.0/16",
        "--property=IPAddressDeny=fc00::/7",
        "--property=IPAddressDeny=fe80::/10",
        "--property=IPAddressDeny=224.0.0.0/4",
        "--property=IPAddressDeny=ff00::/8",
    ]

cmd=[*common,"$PY",str(RUNNER),job_id]
p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if p.returncode:
    die(f"SYSTEMD_RUN:{p.stderr.strip()[:1200]}")
print(json.dumps({"job_id":job_id,"unit":unit,"network_profile":network,"timeout_seconds":timeout},sort_keys=True))
PY
chmod 0755 "$LAUNCHER"
chown root:root "$LAUNCHER"
"$PY" -m py_compile "$LAUNCHER"

log STEP "Install root-only cancel helper"
cat > "$CANCELER" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, subprocess, sys

JOB_RE=re.compile(r"^job_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")

def die(msg:str)->None:
    print(f"TEST_CANCEL_REVIEW:{msg}",file=sys.stderr)
    raise SystemExit(2)

if os.geteuid()!=0:
    die("ROOT_REQUIRED")
if len(sys.argv)==2 and sys.argv[1]=="--self-test":
    print("BOTMARKET_TEST_CANCEL_SELFTEST_PASS")
    raise SystemExit(0)
if len(sys.argv)!=2 or not JOB_RE.fullmatch(sys.argv[1]):
    die("BAD_JOB_ID")

job_id=sys.argv[1]
unit=f"botmarket-test-job-{job_id}.service"
p=subprocess.run(["systemctl","stop",unit],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if p.returncode:
    die(f"SYSTEMCTL_STOP:{p.stderr.strip()[:800]}")
print(json.dumps({"job_id":job_id,"unit":unit,"stopped":True},sort_keys=True))
PY
chmod 0755 "$CANCELER"
chown root:root "$CANCELER"
"$PY" -m py_compile "$CANCELER"

log STEP "Install root-only retention prune helper"
cat > "$PRUNER" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

JOBS=Path("/var/lib/botmarket-test-executor/jobs").resolve()
POLICY=Path("/etc/botmarket-test-executor/policy.json")
JOB_RE=re.compile(r"^job_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")

def die(msg:str)->None:
    print(f"TEST_PRUNE_REVIEW:{msg}",file=sys.stderr)
    raise SystemExit(2)

def job_created(job_id:str)->datetime:
    try:
        return datetime.strptime(job_id[4:20],"%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        die("JOB_ID_TIMESTAMP")
        raise AssertionError

if os.geteuid()!=0:
    die("ROOT_REQUIRED")
if len(sys.argv)==2 and sys.argv[1]=="--self-test":
    print("BOTMARKET_TEST_PRUNE_SELFTEST_PASS")
    raise SystemExit(0)
if len(sys.argv)!=2 or not JOB_RE.fullmatch(sys.argv[1]):
    die("BAD_JOB_ID")

job_id=sys.argv[1]
raw_job=JOBS/job_id
if raw_job.is_symlink():
    die("JOB_SYMLINK")
job=raw_job.resolve()
try:
    job.relative_to(JOBS)
except ValueError:
    die("PATH_ESCAPE")
if not job.is_dir():
    die("JOB_NOT_FOUND")

manifest=job/"job.json"
result=job/"output/job_result.json"
if not manifest.is_file() or manifest.is_symlink():
    die("MANIFEST_REQUIRED")
if not result.is_file() or result.is_symlink():
    die("COMPLETED_RESULT_REQUIRED")

try:
    obj=json.loads(manifest.read_text(encoding="utf-8"))
    policy=json.loads(POLICY.read_text(encoding="utf-8"))
except Exception:
    die("JSON_INVALID")
if obj.get("job_id")!=job_id:
    die("MANIFEST_JOB_ID_MISMATCH")
if policy.get("schema")!="botmarket.test_executor_policy.v1":
    die("POLICY_SCHEMA")

retention_days=int(policy["completed_job_retention_days"])
max_retained=int(policy["max_retained_jobs"])
if retention_days<1 or max_retained<1:
    die("POLICY_RETENTION")

completed:list[tuple[datetime,str]]=[]
for d in JOBS.iterdir():
    if d.is_symlink() or not d.is_dir() or not JOB_RE.fullmatch(d.name):
        continue
    if not (d/"job.json").is_file() or not (d/"output/job_result.json").is_file():
        continue
    completed.append((job_created(d.name),d.name))
completed.sort(key=lambda item:(item[0],item[1]),reverse=True)

rank=next((idx for idx,(_,jid) in enumerate(completed) if jid==job_id),None)
if rank is None:
    die("COMPLETED_JOB_NOT_INDEXED")
cutoff=datetime.now(timezone.utc)-timedelta(days=retention_days)
if not (job_created(job_id)<cutoff or rank>=max_retained):
    die("NOT_RETENTION_ELIGIBLE")

unit=f"botmarket-test-job-{job_id}.service"
state=subprocess.run(
    ["systemctl","is-active",unit],
    text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
)
active_state=state.stdout.strip()
if active_state in {"active","activating","reloading","deactivating"}:
    die("JOB_ACTIVE")

shutil.rmtree(job)
if job.exists():
    die("DELETE_INCOMPLETE")
print(json.dumps({"job_id":job_id,"pruned":True},sort_keys=True))
PY
chmod 0755 "$PRUNER"
chown root:root "$PRUNER"
"$PY" -m py_compile "$PRUNER"

log STEP "Install restricted sudo policy"
cat > "$SUDOERS" <<EOF
$CTL_USER ALL=(root) NOPASSWD: $LAUNCHER
$CTL_USER ALL=(root) NOPASSWD: $CANCELER
$CTL_USER ALL=(root) NOPASSWD: $PRUNER
EOF
chmod 0440 "$SUDOERS"
visudo -cf "$SUDOERS" >/dev/null

as_testctl_root "$LAUNCHER" --self-test | grep -qx 'BOTMARKET_TEST_LAUNCHER_SELFTEST_PASS' || die "Launcher sudo escalation self-test failed"
as_testctl_root "$CANCELER" --self-test | grep -qx 'BOTMARKET_TEST_CANCEL_SELFTEST_PASS' || die "Cancel sudo escalation self-test failed"
as_testctl_root "$PRUNER" --self-test | grep -qx 'BOTMARKET_TEST_PRUNE_SELFTEST_PASS' || die "Prune sudo escalation self-test failed"

PRUNE_SMOKE_ID="job_20000101T000000Z_feedface"
PRUNE_SMOKE_DIR="$JOBS/$PRUNE_SMOKE_ID"
rm -rf "$PRUNE_SMOKE_DIR"
install -d -m0750 -o "$CTL_USER" -g "$JOB_GROUP" "$PRUNE_SMOKE_DIR"
install -d -m0770 -o "$CTL_USER" -g "$JOB_GROUP" "$PRUNE_SMOKE_DIR/output"
cat > "$PRUNE_SMOKE_DIR/job.json" <<EOF
{"schema":"botmarket.test_job.v1","job_id":"$PRUNE_SMOKE_ID","created_utc":"2000-01-01T00:00:00+00:00"}
EOF
cat > "$PRUNE_SMOKE_DIR/output/job_result.json" <<EOF
{"schema":"botmarket.test_job_result.v1","job_id":"$PRUNE_SMOKE_ID","exit_code":0}
EOF
install -d -m0700 -o "$JOB_USER" -g "$JOB_GROUP" "$PRUNE_SMOKE_DIR/output/nested"
echo "protected worker output" > "$PRUNE_SMOKE_DIR/output/nested/worker-owned.txt"
chown "$JOB_USER:$JOB_GROUP" "$PRUNE_SMOKE_DIR/output/nested/worker-owned.txt"
chmod 0600 "$PRUNE_SMOKE_DIR/output/nested/worker-owned.txt"
chown "$CTL_USER:$JOB_GROUP" "$PRUNE_SMOKE_DIR/job.json" "$PRUNE_SMOKE_DIR/output/job_result.json"
chmod 0440 "$PRUNE_SMOKE_DIR/job.json" "$PRUNE_SMOKE_DIR/output/job_result.json"
as_testctl_root "$PRUNER" "$PRUNE_SMOKE_ID" >/dev/null
[[ ! -e "$PRUNE_SMOKE_DIR" ]] || die "Retention prune helper failed synthetic ownership smoke"
echo "RETENTION_PRUNE_OWNERSHIP_SELFTEST=PASS"

set +e
ARBITRARY_ROOT_PROBE="$(runuser -u "$CTL_USER" -- sudo -n -- /usr/bin/id -u 2>&1)"
ARBITRARY_ROOT_RC=$?
set -e
if [[ $ARBITRARY_ROOT_RC -eq 0 ]]; then
  echo "$ARBITRARY_ROOT_PROBE"
  die "Test Executor control user unexpectedly has arbitrary sudo"
fi
echo "ARBITRARY_ROOT_SUDO=DENIED_AS_REQUIRED"

log STEP "Install MCP server"
cat > "$APP/server.py" <<'PY'
from __future__ import annotations

import grp
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from mcp.server.mcpserver import MCPServer
except Exception:
    from mcp.server.fastmcp import FastMCP as MCPServer

NAME="BotMarketplace Test Executor"
STATE=Path(os.environ["BM_TEST_STATE"]).resolve()
REPO=Path(os.environ["BM_TEST_REPO_DIR"]).resolve()
JOBS=(STATE/"jobs").resolve()
URL=os.environ["BM_TEST_REPO_URL"]
BRANCH=os.getenv("BM_TEST_BRANCH","main")
KEY=Path(os.environ["BM_TEST_SSH_KEY"])
KH=Path(os.environ["BM_TEST_KNOWN_HOSTS"])
POLICY_PATH=Path(os.environ["BM_TEST_POLICY"])
HOST=os.getenv("BM_TEST_HOST","127.0.0.1")
PORT=int(os.getenv("BM_TEST_PORT","8769"))
TARGET_PY=os.environ["BM_TEST_PYTHON"]
JOB_GROUP_NAME=os.environ["BM_TEST_JOB_GROUP"]
JOB_GID=grp.getgrnam(JOB_GROUP_NAME).gr_gid
MAX_TEXT=int(os.getenv("BM_TEST_MAX_TEXT_BYTES","262144"))

LAUNCHER="/usr/local/sbin/botmarket-test-launch"
CANCELER="/usr/local/sbin/botmarket-test-cancel"
PRUNER="/usr/local/sbin/botmarket-test-prune"
JOB_RE=re.compile(r"^job_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")

mcp=MCPServer(NAME)

def utc_now()->datetime:
    return datetime.now(timezone.utc)

def iso(dt:datetime)->str:
    return dt.isoformat()

def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def policy()->dict[str,Any]:
    obj=json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if obj.get("schema")!="botmarket.test_executor_policy.v1":
        raise ValueError("POLICY_SCHEMA")
    return obj

def sshcmd()->str:
    return f"ssh -i {KEY} -o IdentitiesOnly=yes -o UserKnownHostsFile={KH} -o StrictHostKeyChecking=yes -o BatchMode=yes"

def git(args:list[str],check:bool=True)->subprocess.CompletedProcess[str]:
    env=os.environ.copy()
    env["GIT_SSH_COMMAND"]=sshcmd()
    p=subprocess.run(
        ["git","-C",str(REPO),*args],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        env=env,timeout=120,
    )
    if check and p.returncode:
        raise ValueError(f"GIT_FAILED rc={p.returncode} stderr={p.stderr.strip()[:1600]}")
    return p

def repo_head()->str:
    return git(["rev-parse","HEAD"]).stdout.strip()

def repo_branch()->str:
    return git(["branch","--show-current"]).stdout.strip()

def repo_status()->str:
    return git(["status","--porcelain=v1","--untracked-files=all"]).stdout

def resolve_job(job_id:str)->Path:
    if not isinstance(job_id,str) or not JOB_RE.fullmatch(job_id):
        raise ValueError("BAD_JOB_ID")
    p=(JOBS/job_id).resolve()
    p.relative_to(JOBS)
    return p

def read_json(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def atomic_json(path:Path,obj:dict[str,Any])->None:
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def set_job_group(path:Path)->None:
    # Control user owns the path and is a supplementary member of JOB_GROUP.
    # This avoids setgid chmod operations, which are intentionally blocked by
    # RestrictSUIDSGID=true on the MCP control service.
    os.chown(path,-1,JOB_GID)

def validate_entrypoint(path:str)->str:
    if not isinstance(path,str) or not path or "\x00" in path or Path(path).is_absolute():
        raise ValueError("ENTRYPOINT_PATH")
    norm=Path(path).as_posix().lstrip("./")
    parts=Path(norm).parts
    if ".." in parts or ".git" in parts:
        raise ValueError("ENTRYPOINT_PATH")
    p=policy()
    if not any(norm.startswith(prefix) for prefix in p["allowed_entrypoint_prefixes"]):
        raise ValueError("ENTRYPOINT_PREFIX_FORBIDDEN")
    if Path(norm).suffix.lower() not in set(p["allowed_entrypoint_suffixes"]):
        raise ValueError("ENTRYPOINT_SUFFIX_FORBIDDEN")
    return norm

def validate_args(args:list[str]|None)->list[str]:
    p=policy()
    args=[] if args is None else args
    if not isinstance(args,list) or len(args)>int(p["max_args"]):
        raise ValueError("ARGS")
    out=[]
    for x in args:
        if not isinstance(x,str) or "\x00" in x or len(x.encode())>int(p["max_arg_bytes"]):
            raise ValueError("ARG_INVALID")
        out.append(x)
    return out

def unit_state(job_id:str)->dict[str,Any]:
    unit=f"botmarket-test-job-{job_id}.service"
    p=subprocess.run(
        ["systemctl","show",unit,
         "-p","LoadState","-p","ActiveState","-p","SubState",
         "-p","Result","-p","ExecMainCode","-p","ExecMainStatus","--no-pager"],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,
    )
    data={"unit":unit}
    if p.returncode:
        data.update({"load_state":"not-found","active_state":"unknown","sub_state":"unknown"})
        return data
    for line in p.stdout.splitlines():
        if "=" in line:
            k,v=line.split("=",1)
            data[k.lower()]=v
    return data

def recent_manifests()->list[dict[str,Any]]:
    out=[]
    if not JOBS.exists():
        return out
    for d in JOBS.iterdir():
        if not d.is_dir() or not JOB_RE.fullmatch(d.name):
            continue
        mp=d/"job.json"
        if not mp.is_file():
            continue
        try:
            out.append(read_json(mp))
        except Exception:
            continue
    return out

def prune_completed_jobs()->dict[str,int]:
    p=policy()
    now=utc_now()
    cutoff=now-timedelta(days=int(p["completed_job_retention_days"]))
    jobs=[]
    for m in recent_manifests():
        try:
            job_id=m["job_id"]
            created=datetime.strptime(job_id[4:20],"%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            job=resolve_job(job_id)
        except Exception:
            continue
        result=(job/"output/job_result.json").is_file()
        if result:
            jobs.append((created,job_id,job))
    jobs.sort(key=lambda x:(x[0],x[1]),reverse=True)
    removed=0
    for idx,(created,job_id,job) in enumerate(jobs):
        if created<cutoff or idx>=int(p["max_retained_jobs"]):
            if not job.exists():
                continue
            prune=subprocess.run(
                ["sudo","-n",PRUNER,job_id],
                text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,
            )
            if prune.returncode:
                raise ValueError(
                    f"RETENTION_PRUNE_FAILED job_id={job_id} stderr={prune.stderr.strip()[:800]}"
                )
            if job.exists():
                raise ValueError(f"RETENTION_PRUNE_INCOMPLETE job_id={job_id}")
            removed+=1
    return {"removed":removed}

def prune_orphan_jobs()->dict[str,int]:
    now=utc_now().timestamp()
    removed=0
    if not JOBS.exists():
        return {"removed":0}
    for d in JOBS.iterdir():
        if not d.is_dir() or not JOB_RE.fullmatch(d.name):
            continue
        if (d/"job.json").exists():
            continue
        try:
            age=max(0.0,now-d.stat().st_mtime)
        except FileNotFoundError:
            continue
        if age>=3600:
            shutil.rmtree(d,ignore_errors=True)
            removed+=1
    return {"removed":removed}

def rate_limit_check()->dict[str,int]:
    p=policy()
    now=utc_now()
    hour_cut=now-timedelta(hours=1)
    day=now.date()
    hour_count=0
    day_count=0
    running=0
    for m in recent_manifests():
        try:
            created=datetime.fromisoformat(m["created_utc"])
        except Exception:
            continue
        if created>=hour_cut:
            hour_count+=1
        if created.date()==day:
            day_count+=1
        s=unit_state(str(m.get("job_id") or ""))
        if s.get("activestate") in {"active","activating","reloading"}:
            running+=1
    if hour_count>=int(p["max_runs_per_rolling_hour"]):
        raise ValueError("RUN_RATE_LIMIT_HOURLY")
    if day_count>=int(p["max_runs_per_utc_day"]):
        raise ValueError("RUN_RATE_LIMIT_DAILY")
    if running>=int(p["max_concurrent_jobs"]):
        raise ValueError("RUN_CONCURRENCY_LIMIT")
    return {"rolling_hour":hour_count,"utc_day":day_count,"running":running}

def secret_like_path(name:str)->bool:
    p=Path(name)
    base=p.name.lower()
    if base in {".env","id_rsa","id_ed25519","authorized_keys",".npmrc",".pypirc"}:
        return True
    if base.startswith(".env.") and base not in {".env.example",".env.sample"}:
        return True
    if p.suffix.lower() in {".pem",".p12",".pfx"}:
        return True
    if p.suffix.lower()==".key" and base not in {"package-lock.key"}:
        return True
    return False

def snapshot_repo(head:str,package:Path)->dict[str,int]:
    p=policy()

    def ensure_package_dir(path:Path)->None:
        path=path.resolve()
        path.relative_to(package.resolve())
        rel=path.relative_to(package.resolve())
        cur=package.resolve()
        set_job_group(cur)
        cur.chmod(0o750)
        for part in rel.parts:
            cur=cur/part
            if not cur.exists():
                cur.mkdir(mode=0o750)
            if not cur.is_dir() or cur.is_symlink():
                raise ValueError(f"REPO_DIR_INVALID:{cur}")
            set_job_group(cur)
            cur.chmod(0o750)
    raw=subprocess.run(
        ["git","-C",str(REPO),"archive","--format=tar",head],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120,
    )
    if raw.returncode:
        raise ValueError(f"GIT_ARCHIVE_FAILED:{raw.stderr.decode(errors='replace')[:800]}")
    if len(raw.stdout)>int(p["max_repo_archive_bytes"]):
        raise ValueError("REPO_ARCHIVE_TOO_LARGE")
    total=0
    count=0
    with tarfile.open(fileobj=io.BytesIO(raw.stdout),mode="r:") as tf:
        members=tf.getmembers()
        if len(members)>int(p["max_repo_files"]):
            raise ValueError("REPO_FILE_COUNT")
        for m in members:
            name=Path(m.name).as_posix()
            if m.issym() or m.islnk() or m.isdev():
                raise ValueError(f"REPO_SPECIAL_FILE:{name}")
            if Path(name).is_absolute() or ".." in Path(name).parts or ".git" in Path(name).parts:
                raise ValueError(f"REPO_PATH:{name}")
            if secret_like_path(name):
                raise ValueError(f"REPO_SECRET_LIKE_PATH:{name}")
            target=(package/name).resolve()
            target.relative_to(package.resolve())
            if m.isdir():
                ensure_package_dir(target)
                continue
            if not m.isfile():
                raise ValueError(f"REPO_MEMBER_TYPE:{name}")
            f=tf.extractfile(m)
            if f is None:
                raise ValueError(f"REPO_EXTRACT:{name}")
            data=f.read()
            total+=len(data)
            if total>int(p["max_repo_archive_bytes"]):
                raise ValueError("REPO_EXTRACTED_TOO_LARGE")
            ensure_package_dir(target.parent)
            target.write_bytes(data)
            set_job_group(target)
            # Preserve only the executable semantic from Git; never preserve
            # owner/group/world write bits from the repository archive.
            target.chmod(0o550 if (m.mode & 0o111) else 0o440)
            count+=1
    return {"file_count":count,"bytes":total}

def read_text_file(path:Path,offset:int,max_bytes:int)->dict[str,Any]:
    n=max(1,min(int(max_bytes),MAX_TEXT))
    off=max(0,int(offset))
    if not path.is_file() or path.is_symlink():
        raise ValueError("FILE_NOT_FOUND")
    data=path.read_bytes()
    chunk=data[off:off+n]
    while chunk:
        try:
            text=chunk.decode("utf-8")
            break
        except UnicodeDecodeError as exc:
            if exc.start>=len(chunk)-4:
                chunk=chunk[:-1]
                continue
            raise ValueError("NOT_UTF8_TEXT") from exc
    else:
        text=""
    nxt=off+len(chunk)
    return {
        "size_bytes":len(data),
        "sha256":sha256_bytes(data),
        "offset_bytes":off,
        "text":text,
        "next_offset_bytes":None if nxt>=len(data) else nxt,
    }

def filesystem_boundary_selftest()->dict[str,Any]:
    probe=(JOBS/f".service-fs-selftest-{os.getpid()}").resolve()
    try:
        probe.relative_to(JOBS)
        package=probe/"package"
        output=probe/"output"
        manifest=probe/"job.json"
        probe.mkdir(mode=0o750,exist_ok=False)
        package.mkdir(mode=0o750)
        output.mkdir(mode=0o770)
        for pth,mode in ((probe,0o750),(package,0o750),(output,0o770)):
            set_job_group(pth)
            pth.chmod(mode)
        sample=package/"sample.py"
        sample.write_text("print('ok')\n",encoding="utf-8")
        set_job_group(sample)
        sample.chmod(0o440)
        atomic_json(manifest,{"schema":"botmarket.service_fs_selftest.v1"})
        set_job_group(manifest)
        manifest.chmod(0o440)
        checks={
            "probe_gid":probe.stat().st_gid,
            "package_gid":package.stat().st_gid,
            "output_gid":output.stat().st_gid,
            "sample_gid":sample.stat().st_gid,
            "manifest_gid":manifest.stat().st_gid,
            "output_group_writable":bool(output.stat().st_mode & 0o020),
        }
        ok=all(checks[k]==JOB_GID for k in ("probe_gid","package_gid","output_gid","sample_gid","manifest_gid")) and checks["output_group_writable"]
        return {"ok":ok,**checks}
    except Exception as exc:
        return {"ok":False,"error":f"{type(exc).__name__}:{exc}"}
    finally:
        shutil.rmtree(probe,ignore_errors=True)

def privilege_bridge_selftest()->dict[str,Any]:
    specs=(
        ("launcher",LAUNCHER,"BOTMARKET_TEST_LAUNCHER_SELFTEST_PASS"),
        ("canceler",CANCELER,"BOTMARKET_TEST_CANCEL_SELFTEST_PASS"),
        ("pruner",PRUNER,"BOTMARKET_TEST_PRUNE_SELFTEST_PASS"),
    )
    checks={}
    for name,path,token in specs:
        p=subprocess.run(
            ["sudo","-n",path,"--self-test"],
            text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,
        )
        checks[name]={
            "ok":p.returncode==0 and p.stdout.strip()==token,
            "returncode":p.returncode,
            "stdout":p.stdout.strip()[:500],
            "stderr":p.stderr.strip()[:500],
        }
    return {"ok":all(x["ok"] for x in checks.values()),"helpers":checks}

@mcp.tool()
def get_test_executor_info()->dict[str,Any]:
    p=policy()
    h=repo_head()
    counts={"rolling_hour":0,"utc_day":0,"running":0}
    try:
        counts=rate_limit_check()
    except ValueError as exc:
        # expose counters even when a limit is reached
        now=utc_now()
        manifests=recent_manifests()
        counts={
            "rolling_hour":sum(
                1 for m in manifests
                if datetime.fromisoformat(m["created_utc"])>=now-timedelta(hours=1)
            ),
            "utc_day":sum(
                1 for m in manifests
                if datetime.fromisoformat(m["created_utc"]).date()==now.date()
            ),
            "running":sum(
                1 for m in manifests
                if unit_state(m["job_id"]).get("activestate") in {"active","activating","reloading"}
            ),
        }
    return {
        "name":NAME,
        "repo_url":URL,
        "branch":repo_branch(),
        "head":h,
        "worktree_clean":not bool(repo_status()),
        "repo_write":False,
        "arbitrary_shell_tool":False,
        "trading_credentials_available_to_jobs":False,
        "network_profiles":p["network_profiles"],
        "limits":{
            "max_timeout_seconds":p["max_timeout_seconds"],
            "max_runs_per_rolling_hour":p["max_runs_per_rolling_hour"],
            "max_runs_per_utc_day":p["max_runs_per_utc_day"],
            "max_concurrent_jobs":p["max_concurrent_jobs"],
            "completed_job_retention_days":p["completed_job_retention_days"],
            "max_retained_jobs":p["max_retained_jobs"],
        },
        "current_counts":counts,
        "privilege_bridge":privilege_bridge_selftest(),
        "filesystem_boundary":filesystem_boundary_selftest(),
    }

@mcp.tool()
def refresh_repo(expected_head:str|None=None)->dict[str,Any]:
    if repo_status():
        raise ValueError("WORKTREE_DIRTY")
    if repo_branch()!=BRANCH:
        raise ValueError("UNEXPECTED_BRANCH")
    before=repo_head()
    git(["fetch","--prune","origin",BRANCH])
    origin=git(["rev-parse",f"origin/{BRANCH}"]).stdout.strip()
    if expected_head is not None and origin!=expected_head:
        raise ValueError(f"REMOTE_HEAD_MISMATCH origin={origin}")
    git(["merge","--ff-only",f"origin/{BRANCH}"])
    after=repo_head()
    if after!=origin:
        raise ValueError("REFRESH_NOT_AT_ORIGIN")
    return {"before":before,"after":after,"origin":origin,"worktree_clean":not bool(repo_status())}

@mcp.tool()
def run_repo_test(
    repo_head_sha:str,
    entrypoint:str,
    args:list[str]|None=None,
    network_profile:str="offline",
    timeout_seconds:int|None=None,
)->dict[str,Any]:
    p=policy()
    if repo_status():
        raise ValueError("WORKTREE_DIRTY")
    if repo_branch()!=BRANCH:
        raise ValueError("UNEXPECTED_BRANCH")
    local=repo_head()
    git(["fetch","--prune","origin",BRANCH])
    origin=git(["rev-parse",f"origin/{BRANCH}"]).stdout.strip()
    if local!=origin:
        raise ValueError(f"REPO_NOT_REFRESHED local={local} origin={origin}")
    if repo_head_sha!=local:
        raise ValueError(f"HEAD_MISMATCH actual={local}")

    entry=validate_entrypoint(entrypoint)
    argv=validate_args(args)
    if network_profile not in set(p["network_profiles"]):
        raise ValueError("NETWORK_PROFILE")
    timeout=int(timeout_seconds or p["default_timeout_seconds"])
    if timeout<1 or timeout>int(p["max_timeout_seconds"]):
        raise ValueError("TIMEOUT")

    prune_orphan_jobs()
    prune_completed_jobs()
    counts=rate_limit_check()

    job_id=utc_now().strftime("job_%Y%m%dT%H%M%SZ_")+secrets.token_hex(4)
    job=resolve_job(job_id)
    package=job/"package"
    output=job/"output"
    job.mkdir(mode=0o750,parents=False,exist_ok=False)
    package.mkdir(mode=0o750)
    output.mkdir(mode=0o770)
    for pth,mode in ((job,0o750),(package,0o750),(output,0o770)):
        set_job_group(pth)
        pth.chmod(mode)

    try:
        snap=snapshot_repo(local,package)
        ep=(package/entry).resolve()
        ep.relative_to(package.resolve())
        if not ep.is_file() or ep.is_symlink():
            raise ValueError("ENTRYPOINT_NOT_IN_SNAPSHOT")
        manifest={
            "schema":"botmarket.test_job.v1",
            "job_id":job_id,
            "created_utc":iso(utc_now()),
            "repo_head":local,
            "repo_url":URL,
            "entrypoint":entry,
            "entrypoint_sha256":sha256_file(ep),
            "args":argv,
            "network_profile":network_profile,
            "timeout_seconds":timeout,
            "snapshot_file_count":snap["file_count"],
            "snapshot_bytes":snap["bytes"],
            "trading_credentials_available":False,
        }
        atomic_json(job/"job.json",manifest)
        set_job_group(job/"job.json")
        os.chmod(job/"job.json",0o440)

        launch=subprocess.run(
            ["sudo","-n",LAUNCHER,job_id],
            text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,
        )
        if launch.returncode:
            atomic_json(output/"launch_error.json",{
                "schema":"botmarket.test_launch_error.v1",
                "job_id":job_id,
                "returncode":launch.returncode,
                "stderr":launch.stderr.strip()[:4000],
            })
            raise ValueError(f"LAUNCH_FAILED:{launch.stderr.strip()[:1200]}")

        return {
            "job_id":job_id,
            "repo_head":local,
            "entrypoint":entry,
            "entrypoint_sha256":manifest["entrypoint_sha256"],
            "network_profile":network_profile,
            "timeout_seconds":timeout,
            "unit_state":unit_state(job_id),
            "rate_counts_before_launch":counts,
        }
    except Exception:
        raise

@mcp.tool()
def get_job_status(job_id:str)->dict[str,Any]:
    job=resolve_job(job_id)
    manifest=read_json(job/"job.json")
    result=None
    rp=job/"output/job_result.json"
    if rp.is_file():
        result=read_json(rp)
    return {
        "job_id":job_id,
        "manifest":manifest,
        "unit_state":unit_state(job_id),
        "result":result,
        "log_present":(job/"output/run.log").is_file(),
    }

@mcp.tool()
def list_recent_jobs(limit:int=20)->dict[str,Any]:
    n=max(1,min(int(limit),100))
    items=[]
    for m in recent_manifests():
        try:
            items.append({
                "job_id":m["job_id"],
                "created_utc":m["created_utc"],
                "repo_head":m["repo_head"],
                "entrypoint":m["entrypoint"],
                "network_profile":m["network_profile"],
                "unit_state":unit_state(m["job_id"]),
                "result":read_json(resolve_job(m["job_id"])/"output/job_result.json")
                    if (resolve_job(m["job_id"])/"output/job_result.json").is_file() else None,
            })
        except Exception:
            continue
    items.sort(key=lambda x:x["created_utc"],reverse=True)
    return {"jobs":items[:n]}

@mcp.tool()
def read_job_log(job_id:str,offset_bytes:int=0,max_bytes:int=65536)->dict[str,Any]:
    job=resolve_job(job_id)
    out=read_text_file(job/"output/run.log",offset_bytes,max_bytes)
    out["job_id"]=job_id
    out["path"]="output/run.log"
    return out

@mcp.tool()
def list_job_files(job_id:str,recursive:bool=False,limit:int=200)->dict[str,Any]:
    job=resolve_job(job_id)
    root=(job/"output").resolve()
    n=max(1,min(int(limit),1000))
    it=root.rglob("*") if recursive else root.iterdir()
    entries=[]
    for x in it:
        if x.is_symlink():
            continue
        rel=x.resolve().relative_to(root).as_posix()
        entries.append({
            "path":rel,
            "kind":"dir" if x.is_dir() else "file",
            "size_bytes":None if x.is_dir() else x.stat().st_size,
        })
        if len(entries)>=n:
            break
    return {"job_id":job_id,"entries":sorted(entries,key=lambda x:x["path"]),"truncated":len(entries)>=n}

@mcp.tool()
def read_job_text(job_id:str,path:str,offset_bytes:int=0,max_bytes:int=65536)->dict[str,Any]:
    if not isinstance(path,str) or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError("PATH")
    job=resolve_job(job_id)
    root=(job/"output").resolve()
    target=(root/path).resolve()
    target.relative_to(root)
    out=read_text_file(target,offset_bytes,max_bytes)
    out["job_id"]=job_id
    out["path"]=Path(path).as_posix()
    return out

@mcp.tool()
def cancel_job(job_id:str)->dict[str,Any]:
    resolve_job(job_id)
    p=subprocess.run(
        ["sudo","-n",CANCELER,job_id],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,
    )
    if p.returncode:
        raise ValueError(f"CANCEL_FAILED:{p.stderr.strip()[:1200]}")
    return {"job_id":job_id,"cancelled":True,"unit_state":unit_state(job_id)}

if __name__=="__main__":
    fscheck=filesystem_boundary_selftest()
    if not fscheck["ok"]:
        raise SystemExit("FILESYSTEM_BOUNDARY_SELFTEST_FAILED:"+json.dumps(fscheck,sort_keys=True))
    bridge=privilege_bridge_selftest()
    if not bridge["ok"]:
        raise SystemExit("PRIVILEGE_BRIDGE_SELFTEST_FAILED:"+json.dumps(bridge,sort_keys=True))
    try:
        mcp.run(
            transport="streamable-http",
            host=HOST,
            port=PORT,
            streamable_http_path="/mcp",
            stateless_http=True,
            json_response=True,
        )
    except TypeError:
        mcp.run(
            transport="streamable-http",
            host=HOST,
            port=PORT,
            streamable_http_path="/mcp",
        )
PY

chmod 0755 "$APP/server.py"
chown root:root "$APP/server.py"
"$PY" -m py_compile "$APP/server.py"
echo "SERVER_PY_COMPILE=PASS"

log STEP "Install MCP service"
cat > "$UNIT" <<EOF
[Unit]
Description=BotMarketplace Test Executor MCP
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$CTL_USER
Group=$CTL_GROUP
SupplementaryGroups=$JOB_GROUP
WorkingDirectory=$STATE
Environment=HOME=$STATE
EnvironmentFile=$ENVF
ExecStart=$PY $APP/server.py
Restart=on-failure
RestartSec=3
TimeoutStopSec=20
UMask=0027
# Deliberately NOT using NoNewPrivileges/empty CapabilityBoundingSet here:
# this control service must traverse the exact sudoers bridge to the three
# root-owned helpers (launch/cancel/retention-prune). The helpers themselves
# remain narrowly scoped; jobs stay tightly sandboxed.
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectKernelLogs=true
RestrictSUIDSGID=true
LockPersonality=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
ReadWritePaths=$REPODIR $JOBS
ReadOnlyPaths=$ENVF $POLICY $APP $SSHDIR $STATE/public-resolv.conf

[Install]
WantedBy=multi-user.target
EOF
chmod 0644 "$UNIT"

systemctl daemon-reload
systemctl enable botmarket-test-executor.service >/dev/null

if ! systemctl restart botmarket-test-executor.service; then
  echo "[WARN] New Test Executor failed to restart; attempting bounded runtime rollback" >&2
  if [[ "$SERVICE_WAS_ACTIVE" -eq 1 && -f "$BACKUP/server.py.bak" && -f "$BACKUP/botmarket-test-executor.service.bak" ]]; then
    cp -a "$BACKUP/server.py.bak" "$APP/server.py"
    cp -a "$BACKUP/botmarket-test-executor.service.bak" "$UNIT"
    [[ -f "$BACKUP/env.bak" ]] && cp -a "$BACKUP/env.bak" "$ENVF"
    [[ -f "$BACKUP/policy.json.bak" ]] && cp -a "$BACKUP/policy.json.bak" "$POLICY"
    [[ -f "$BACKUP/botmarket-test-executor.bak" ]] && cp -a "$BACKUP/botmarket-test-executor.bak" "$SUDOERS"
    systemctl daemon-reload
    systemctl restart botmarket-test-executor.service || true
  fi
  systemctl --no-pager --full status botmarket-test-executor.service || true
  journalctl -u botmarket-test-executor.service -n100 --no-pager || true
  die "Test Executor restart failed; bounded rollback attempted"
fi
sleep 2

systemctl is-active --quiet botmarket-test-executor.service || {
  systemctl --no-pager --full status botmarket-test-executor.service || true
  journalctl -u botmarket-test-executor.service -n100 --no-pager || true
  die "Test Executor service is not active after explicit restart"
}

ss -ltnH | awk '{print $4}' | grep -Eq "127\.0\.0\.1:${PORT}$|\[::1\]:${PORT}$"   || die "Port $PORT not listening"

log STEP "Run isolated offline install self-test"
SELF_ID="job_$(date -u +%Y%m%dT%H%M%SZ)_deadbeef"
SELF_DIR="$JOBS/$SELF_ID"
rm -rf "$SELF_DIR"
install -d -m2750 -o "$CTL_USER" -g "$JOB_GROUP" "$SELF_DIR"
install -d -m0750 -o "$CTL_USER" -g "$JOB_GROUP" "$SELF_DIR/package"
install -d -m0770 -o "$CTL_USER" -g "$JOB_GROUP" "$SELF_DIR/output"
chmod 0770 "$SELF_DIR/output"

cat > "$SELF_DIR/package/test.py" <<'PY'
print("BOTMARKET_TEST_EXECUTOR_INSTALL_JOB_PASS")
PY
chown "$CTL_USER:$JOB_GROUP" "$SELF_DIR/package/test.py"
chmod 0440 "$SELF_DIR/package/test.py"
SELF_SHA="$(sha256sum "$SELF_DIR/package/test.py" | awk '{print $1}')"

cat > "$SELF_DIR/job.json" <<EOF
{
  "schema": "botmarket.test_job.v1",
  "job_id": "$SELF_ID",
  "created_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo_head": "$LOCAL_HEAD",
  "repo_url": "$REPO_URL",
  "entrypoint": "test.py",
  "entrypoint_sha256": "$SELF_SHA",
  "args": [],
  "network_profile": "offline",
  "timeout_seconds": 20,
  "snapshot_file_count": 1,
  "snapshot_bytes": 52,
  "trading_credentials_available": false,
  "installer_selftest": true
}
EOF
chown "$CTL_USER:$JOB_GROUP" "$SELF_DIR/job.json"
chmod 0440 "$SELF_DIR/job.json"

as_testctl_root "$LAUNCHER" "$SELF_ID" >/dev/null
READY=0
for _ in $(seq 1 40); do
  if [[ -f "$SELF_DIR/output/job_result.json" ]]; then
    READY=1
    break
  fi
  sleep 0.5
done
[[ "$READY" -eq 1 ]] || {
  systemctl --no-pager --full status "botmarket-test-job-$SELF_ID.service" || true
  [[ -f "$SELF_DIR/output/run.log" ]] && cat "$SELF_DIR/output/run.log" || true
  die "Install self-test did not complete"
}

"$PY" - "$SELF_DIR/output/job_result.json" "$SELF_DIR/output/run.log" <<'PY'
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
log=Path(sys.argv[2]).read_text()
assert r["exit_code"]==0, r
assert r["timed_out"] is False, r
assert "BOTMARKET_TEST_EXECUTOR_INSTALL_JOB_PASS" in log, log
print("ISOLATED_JOB_SELFTEST=PASS")
PY

systemctl stop "botmarket-test-job-$SELF_ID.service" >/dev/null 2>&1 || true
systemctl reset-failed "botmarket-test-job-$SELF_ID.service" >/dev/null 2>&1 || true
rm -rf "$SELF_DIR"

log STEP "Run isolated public-research network self-test"
PUBLIC_ID="job_$(date -u +%Y%m%dT%H%M%SZ)_cafebabe"
PUBLIC_DIR="$JOBS/$PUBLIC_ID"
rm -rf "$PUBLIC_DIR"
install -d -m2750 -o "$CTL_USER" -g "$JOB_GROUP" "$PUBLIC_DIR"
install -d -m2750 -o "$CTL_USER" -g "$JOB_GROUP" "$PUBLIC_DIR/package"
install -d -m0770 -o "$CTL_USER" -g "$JOB_GROUP" "$PUBLIC_DIR/output"
cat > "$PUBLIC_DIR/package/public_test.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
code=""
curl_rc=1
for attempt in 1 2 3; do
  set +e
  code="$(curl -4 --http1.1 -sS --max-time 15 -o /dev/null -w '%{http_code}' https://announcements.bybit.com/en-US/ 2>/dev/null)"
  curl_rc=$?
  set -e
  if [[ $curl_rc -eq 0 && "$code" =~ ^[1-5][0-9][0-9]$ ]]; then
    break
  fi
  if (( attempt < 3 )); then
    sleep "$((attempt*2))"
  fi
done
if [[ $curl_rc -ne 0 || ! "$code" =~ ^[1-5][0-9][0-9]$ ]]; then
  echo "PUBLIC_HTTPS_TRANSPORT_FAILED_AFTER_RETRIES rc=$curl_rc code=$code"
  exit 9
fi
echo "PUBLIC_HTTP_CODE=$code"
if curl -sS --max-time 2 http://127.0.0.1:8768/mcp >/dev/null 2>&1; then
  echo "LOOPBACK_MCP_UNEXPECTEDLY_REACHABLE"
  exit 10
fi
echo "BOTMARKET_TEST_EXECUTOR_PUBLIC_NETWORK_PASS"
SH
chown "$CTL_USER:$JOB_GROUP" "$PUBLIC_DIR/package/public_test.sh"
chmod 0550 "$PUBLIC_DIR/package/public_test.sh"
PUBLIC_SHA="$(sha256sum "$PUBLIC_DIR/package/public_test.sh" | awk '{print $1}')"
cat > "$PUBLIC_DIR/job.json" <<EOF
{
  "schema": "botmarket.test_job.v1",
  "job_id": "$PUBLIC_ID",
  "created_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo_head": "$LOCAL_HEAD",
  "repo_url": "$REPO_URL",
  "entrypoint": "public_test.sh",
  "entrypoint_sha256": "$PUBLIC_SHA",
  "args": [],
  "network_profile": "public_research",
  "timeout_seconds": 30,
  "snapshot_file_count": 1,
  "snapshot_bytes": 1,
  "trading_credentials_available": false,
  "installer_selftest": true
}
EOF
chown "$CTL_USER:$JOB_GROUP" "$PUBLIC_DIR/job.json"
chmod 0440 "$PUBLIC_DIR/job.json"

as_testctl_root "$LAUNCHER" "$PUBLIC_ID" >/dev/null
PUBLIC_READY=0
for _ in $(seq 1 60); do
  if [[ -f "$PUBLIC_DIR/output/job_result.json" ]]; then
    PUBLIC_READY=1
    break
  fi
  sleep 0.5
done
[[ "$PUBLIC_READY" -eq 1 ]] || {
  systemctl --no-pager --full status "botmarket-test-job-$PUBLIC_ID.service" || true
  [[ -f "$PUBLIC_DIR/output/run.log" ]] && cat "$PUBLIC_DIR/output/run.log" || true
  die "Public-network self-test did not complete"
}
"$PY" - "$PUBLIC_DIR/output/job_result.json" "$PUBLIC_DIR/output/run.log" <<'PY'
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
log=Path(sys.argv[2]).read_text()
assert r["exit_code"]==0, r
assert "BOTMARKET_TEST_EXECUTOR_PUBLIC_NETWORK_PASS" in log, log
assert "LOOPBACK_MCP_UNEXPECTEDLY_REACHABLE" not in log, log
print("PUBLIC_NETWORK_SANDBOX_SELFTEST=PASS")
PY
systemctl stop "botmarket-test-job-$PUBLIC_ID.service" >/dev/null 2>&1 || true
systemctl reset-failed "botmarket-test-job-$PUBLIC_ID.service" >/dev/null 2>&1 || true
rm -rf "$PUBLIC_DIR"

log STEP "Probe local MCP"
set +e
TMP="$(mktemp)"
HTTP_CODE="$(curl -sS -N --max-time 2 -o "$TMP" -w '%{http_code}'   -H 'Accept: application/json, text/event-stream' "http://$HOST:$PORT/mcp" 2>/dev/null)"
CURL_RC=$?
set -e
rm -f "$TMP"
if [[ "$HTTP_CODE" != "200" && $CURL_RC -ne 0 ]]; then
  die "Local Test Executor MCP probe failed: HTTP=$HTTP_CODE curl_rc=$CURL_RC"
fi

echo
echo "=== BOTMARKETPLACE TEST EXECUTOR V1 INSTALLED ==="
echo "Repository read: PASS"
echo "Repository write: DENIED_AS_REQUIRED"
echo "MCP service filesystem boundary self-test: PASS"
echo "MCP service restricted sudo bridge self-test: PASS"
echo "Isolated offline job self-test: PASS"
echo "Public research network sandbox self-test: PASS"
echo "Local MCP: http://$HOST:$PORT/mcp"
echo "Service: botmarket-test-executor.service"
echo "Control user: $CTL_USER"
echo "Job user: $JOB_USER"
echo "Network profiles: offline, public_research"
echo "Autonomous limit: 6 runs / rolling hour, 30 runs / UTC day, 1 concurrent"
echo "Trading credentials available to jobs: NO"
echo "Research Runner: NOT MODIFIED"
echo "GitHub Control: NOT MODIFIED"
echo "Backup: $BACKUP"
ERROR: The key you are authenticating with has been marked as read only.\nfatal: Could not read from remote repository.'
TRANSPORT_SAMPLE='ssh: connect to host github.com port 22: Connection timed out'
explicit_readonly_denial "$READONLY_SAMPLE" \
  || die "GITHUB_WRITE_DENIAL_CLASSIFIER_REJECTED_LIVE_GITHUB_SAMPLE"
if explicit_readonly_denial "$TRANSPORT_SAMPLE"; then
  die "GITHUB_WRITE_DENIAL_CLASSIFIER_ACCEPTED_TRANSPORT_FAILURE"
fi
echo "GITHUB_WRITE_DENIAL_CLASSIFIER_SELFTEST=PASS"

if ss -ltnH | awk '{print $4}' | grep -Eq "(^|:)${PORT}$"   && ! systemctl is-active --quiet botmarket-test-executor.service 2>/dev/null; then
  die "Port $PORT is occupied"
fi

"$PY" - <<'PY'
try:
    from mcp.server.mcpserver import MCPServer
except Exception:
    from mcp.server.fastmcp import FastMCP as MCPServer
print("MCP_SDK_IMPORT=PASS")
PY

log STEP "Create isolated users and directories"
getent group "$CTL_GROUP" >/dev/null || groupadd --system "$CTL_GROUP"
getent group "$JOB_GROUP" >/dev/null || groupadd --system "$JOB_GROUP"

id "$CTL_USER" >/dev/null 2>&1 ||   useradd --system --gid "$CTL_GROUP" --home-dir "$STATE" --create-home --shell /usr/sbin/nologin "$CTL_USER"
id "$JOB_USER" >/dev/null 2>&1 ||   useradd --system --gid "$JOB_GROUP" --home-dir /nonexistent --shell /usr/sbin/nologin "$JOB_USER"

usermod -a -G "$JOB_GROUP" "$CTL_USER"

install -d -m0755 -o root -g root "$APP" "$CONF"
install -d -m0750 -o "$CTL_USER" -g "$JOB_GROUP" "$STATE"
install -d -m0700 -o "$CTL_USER" -g "$CTL_GROUP" "$SSHDIR"
install -d -m2770 -o "$CTL_USER" -g "$JOB_GROUP" "$JOBS"
install -d -m0700 -o root -g root "$BACKUP"

for f in "$APP/server.py" "$APP/job_runner.py" "$LAUNCHER" "$CANCELER" "$PRUNER" "$ENVF" "$POLICY" "$UNIT" "$SUDOERS"; do
  [[ -f "$f" ]] && cp -a "$f" "$BACKUP/$(basename "$f").bak"
done

log STEP "Create/read-only GitHub deploy key"
: > "$KH"
for f in /var/lib/botmarket-github-control/ssh/known_hosts /home/botmarket/.ssh/known_hosts /root/.ssh/known_hosts; do
  [[ -r "$f" ]] && grep -E 'github\.com' "$f" >> "$KH" 2>/dev/null || true
done
[[ -s "$KH" ]] || ssh-keyscan -T10 -H github.com >> "$KH" 2>/dev/null || true
[[ -s "$KH" ]] || die "Cannot obtain GitHub host key"
sort -u "$KH" -o "$KH"
chown "$CTL_USER:$CTL_GROUP" "$KH"
chmod 0644 "$KH"

[[ -f "$KEY" ]] ||   ssh-keygen -q -t ed25519 -N '' -C "botmarket-test-executor@$(hostname)" -f "$KEY"
chown "$CTL_USER:$CTL_GROUP" "$KEY" "$KEY.pub"
chmod 0600 "$KEY"
chmod 0644 "$KEY.pub"

SSH="ssh -i $KEY -o IdentitiesOnly=yes -o UserKnownHostsFile=$KH -o StrictHostKeyChecking=yes -o BatchMode=yes"

READ=""
RC=1
for attempt in 1 2 3 4; do
  set +e
  READ="$(runuser -u "$CTL_USER" -- env GIT_SSH_COMMAND="$SSH" git ls-remote "$REPO_URL" "refs/heads/$BRANCH" 2>&1)"
  RC=$?
  set -e
  [[ $RC -eq 0 ]] && break
  if (( attempt < 4 )); then
    echo "[RETRY] GitHub read probe failed rc=$RC attempt=$attempt/4; retrying in $((attempt*2))s" >&2
    sleep "$((attempt*2))"
  fi
done
if [[ $RC -ne 0 ]]; then
  if grep -Eqi 'Permission denied \(publickey\)|Repository not found|repository access denied' <<<"$READ"; then
    echo
    echo "TEST_EXECUTOR_DEPLOY_KEY_NOT_AUTHORIZED_YET"
    echo "Repository: $REPO_NAME"
    echo "GitHub -> Settings -> Deploy keys -> Add deploy key"
    echo "Title: BotMarketplace Test Executor READ ONLY"
    echo "IMPORTANT: DO NOT enable 'Allow write access'"
    echo
    cat "$KEY.pub"
    echo
    echo "After authorizing this READ-ONLY key, rerun this same installer."
    exit 3
  fi
  die "GITHUB_READ_TRANSPORT_FAILURE after 4 attempts: ${READ:0:1200}"
fi

REMOTE_SHA="$(awk 'NF>=2{print $1;exit}' <<<"$READ")"
[[ "$REMOTE_SHA" =~ ^[0-9a-f]{40,64}$ ]] || die "Cannot parse remote branch SHA"
echo "GITHUB_READ=PASS"

log STEP "Create/refresh dedicated read-only clone"
if [[ -d "$REPODIR/.git" ]]; then
  ORIGIN="$(runuser -u "$CTL_USER" -- git -C "$REPODIR" remote get-url origin)"
  [[ "$ORIGIN" == "$REPO_URL" ]] || die "Unexpected origin: $ORIGIN"
  [[ -z "$(runuser -u "$CTL_USER" -- git -C "$REPODIR" status --porcelain=v1)" ]] || die "Test Executor clone is dirty"
  retry_cmd 4 runuser -u "$CTL_USER" -- env GIT_SSH_COMMAND="$SSH" git -C "$REPODIR" fetch --prune origin "$BRANCH" \
    || die "Git fetch failed after retries"
  runuser -u "$CTL_USER" -- git -C "$REPODIR" checkout "$BRANCH"
  runuser -u "$CTL_USER" -- git -C "$REPODIR" merge --ff-only "origin/$BRANCH"
else
  CLONE_OK=0
  for attempt in 1 2 3 4; do
    rm -rf "$REPODIR"
    if runuser -u "$CTL_USER" -- env GIT_SSH_COMMAND="$SSH" git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$REPODIR"; then
      CLONE_OK=1
      break
    fi
    if (( attempt < 4 )); then
      echo "[RETRY] Git clone failed attempt=$attempt/4; retrying in $((attempt*2))s" >&2
      sleep "$((attempt*2))"
    fi
  done
  [[ "$CLONE_OK" -eq 1 ]] || die "Git clone failed after retries"
fi
chmod 0700 "$REPODIR"
LOCAL_HEAD="$(runuser -u "$CTL_USER" -- git -C "$REPODIR" rev-parse HEAD)"
[[ "$LOCAL_HEAD" == "$REMOTE_SHA" ]] || die "Clone HEAD != origin/$BRANCH"
echo "TEST_EXECUTOR_REPO_HEAD=$LOCAL_HEAD"

log STEP "Verify deploy key is truly read-only"
WRITE_PROBE=""
WRITE_RC=1
for attempt in 1 2 3; do
  set +e
  WRITE_PROBE="$(runuser -u "$CTL_USER" -- env GIT_SSH_COMMAND="$SSH" git -C "$REPODIR" push --dry-run origin "HEAD:refs/heads/__botmarket_test_executor_write_probe__" 2>&1)"
  WRITE_RC=$?
  set -e
  if [[ $WRITE_RC -eq 0 ]]; then
    die "Deploy key appears write-enabled. Disable 'Allow write access' before continuing."
  fi
  if grep -Eqi 'write access.*not granted|permission to .* denied|deploy key.*read.?only|permission denied.*write' <<<"$WRITE_PROBE"; then
    break
  fi
  if (( attempt < 3 )); then
    echo "[RETRY] GitHub write-denial probe was transport-indeterminate attempt=$attempt/3; retrying in $((attempt*2))s" >&2
    sleep "$((attempt*2))"
  fi
done
if ! grep -Eqi 'write access.*not granted|permission to .* denied|deploy key.*read.?only|permission denied.*write' <<<"$WRITE_PROBE"; then
  die "GITHUB_WRITE_DENIAL_INDETERMINATE: ${WRITE_PROBE:0:1200}"
fi
echo "GITHUB_WRITE=DENIED_AS_REQUIRED"

log STEP "Prepare isolated public-research DNS"
PUBLIC_RESOLV="$STATE/public-resolv.conf"
"$PY" - "$PUBLIC_RESOLV.tmp" <<'PY'
import ipaddress,sys
from pathlib import Path

out=Path(sys.argv[1])
seen=[]
for src in (Path("/run/systemd/resolve/resolv.conf"),Path("/etc/resolv.conf")):
    try:
        lines=src.read_text(encoding="utf-8",errors="ignore").splitlines()
    except Exception:
        continue
    for line in lines:
        parts=line.split()
        if len(parts)<2 or parts[0]!="nameserver":
            continue
        try:
            ip=ipaddress.ip_address(parts[1].split("%",1)[0])
        except ValueError:
            continue
        if ip.is_global and str(ip) not in seen:
            seen.append(str(ip))
if not seen:
    seen=["1.1.1.1","8.8.8.8"]
out.write_text("".join(f"nameserver {ip}\n" for ip in seen[:3]),encoding="utf-8")
PY
mv "$PUBLIC_RESOLV.tmp" "$PUBLIC_RESOLV"
chown root:"$JOB_GROUP" "$PUBLIC_RESOLV"
chmod 0440 "$PUBLIC_RESOLV"

log STEP "Install policy"
cat > "$POLICY" <<'JSON'
{
  "schema": "botmarket.test_executor_policy.v1",
  "allowed_entrypoint_prefixes": [
    "research/",
    "scripts/research/",
    "tests/"
  ],
  "allowed_entrypoint_suffixes": [
    ".py",
    ".sh"
  ],
  "network_profiles": [
    "offline",
    "public_research"
  ],
  "max_timeout_seconds": 900,
  "default_timeout_seconds": 180,
  "max_runs_per_rolling_hour": 6,
  "max_runs_per_utc_day": 30,
  "max_concurrent_jobs": 1,
  "max_args": 24,
  "max_arg_bytes": 512,
  "max_repo_archive_bytes": 134217728,
  "max_repo_files": 6000,
  "max_output_file_bytes": 67108864,
  "completed_job_retention_days": 7,
  "max_retained_jobs": 100,
  "memory_max_bytes": 1073741824,
  "tasks_max": 64,
  "cpu_quota_percent": 200,
  "public_research_blocks_loopback_private_and_link_local": true,
  "public_research_resolver_file": "/var/lib/botmarket-test-executor/public-resolv.conf",
  "trading_credentials_available_to_jobs": false,
  "arbitrary_shell_tool": false,
  "repo_write": false,
  "sudo_inside_job": false
}
JSON
chown root:"$CTL_GROUP" "$POLICY"
chmod 0640 "$POLICY"

cat > "$ENVF" <<EOF
BM_TEST_STATE=$STATE
BM_TEST_REPO_DIR=$REPODIR
BM_TEST_REPO_URL=$REPO_URL
BM_TEST_BRANCH=$BRANCH
BM_TEST_SSH_KEY=$KEY
BM_TEST_KNOWN_HOSTS=$KH
BM_TEST_POLICY=$POLICY
BM_TEST_HOST=$HOST
BM_TEST_PORT=$PORT
BM_TEST_PYTHON=$PY
BM_TEST_JOB_GROUP=$JOB_GROUP
BM_TEST_MAX_TEXT_BYTES=262144
EOF
chown root:"$CTL_GROUP" "$ENVF"
chmod 0640 "$ENVF"

log STEP "Install sandboxed job runner"
cat > "$APP/job_runner.py" <<PY
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE=Path("$JOBS").resolve()
TARGET_PY=Path("$PY")
BASH=Path("/usr/bin/bash")

def utc_now()->str:
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def atomic_json(path:Path,obj:dict)->None:
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def fail(msg:str,rc:int=125)->int:
    print(msg,file=sys.stderr,flush=True)
    return rc

def main()->int:
    if len(sys.argv)!=2:
        return fail("JOB_ID_REQUIRED")
    job_id=sys.argv[1]
    if not job_id.startswith("job_"):
        return fail("BAD_JOB_ID")

    job=(BASE/job_id).resolve()
    try:
        job.relative_to(BASE)
    except ValueError:
        return fail("JOB_ESCAPE")

    manifest_path=job/"job.json"
    package=(job/"package").resolve()
    output=(job/"output").resolve()
    result_path=output/"job_result.json"
    log_path=output/"run.log"

    started=utc_now()
    rc=125
    timed_out=False
    error=None
    command=[]

    try:
        m=json.loads(manifest_path.read_text(encoding="utf-8"))
        if m.get("schema")!="botmarket.test_job.v1" or m.get("job_id")!=job_id:
            raise RuntimeError("MANIFEST_SCHEMA_OR_ID")
        if m.get("trading_credentials_available") is not False:
            raise RuntimeError("TRADING_CREDENTIAL_BOUNDARY")
        entry_rel=m.get("entrypoint")
        if not isinstance(entry_rel,str):
            raise RuntimeError("ENTRYPOINT")
        entry=(package/entry_rel).resolve()
        entry.relative_to(package)
        if not entry.is_file() or entry.is_symlink():
            raise RuntimeError("ENTRYPOINT_NOT_FILE")
        if sha256_file(entry)!=m.get("entrypoint_sha256"):
            raise RuntimeError("ENTRYPOINT_SHA")

        args=m.get("args") or []
        if (
            not isinstance(args,list)
            or len(args)>24
            or not all(isinstance(x,str) and "\x00" not in x and len(x.encode())<=512 for x in args)
        ):
            raise RuntimeError("ARGS")
        timeout=int(m.get("timeout_seconds") or 0)
        if timeout<1 or timeout>900:
            raise RuntimeError("TIMEOUT")

        suffix=entry.suffix.lower()
        if suffix==".py":
            command=[str(TARGET_PY),str(entry),*args]
        elif suffix==".sh":
            command=[str(BASH),str(entry),*args]
        else:
            raise RuntimeError("ENTRYPOINT_SUFFIX")

        env={
            "PATH":"/usr/bin:/bin",
            "HOME":str(output/"home"),
            "LANG":"C.UTF-8",
            "LC_ALL":"C.UTF-8",
            "PYTHONUNBUFFERED":"1",
            "PYTHONDONTWRITEBYTECODE":"1",
            "BM_TEST_EXECUTOR":"1",
            "BM_TEST_NETWORK_PROFILE":str(m.get("network_profile") or "offline"),
            "BM_TEST_OUTPUT_DIR":str(output),
            "B15P2_REPO_ROOT":str(package),
            "SC001_DATA_ROOT":str(output/"data"),
        }
        (output/"home").mkdir(parents=True,exist_ok=True)
        (output/"data").mkdir(parents=True,exist_ok=True)

        with log_path.open("ab",buffering=0) as log:
            p=subprocess.Popen(
                command,
                cwd=str(package),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
            try:
                rc=p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out=True
                error="TIMEOUT"
                try:
                    os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
                rc=p.wait(timeout=10) if p.poll() is None else p.returncode
                if rc==0:
                    rc=124
    except Exception as exc:
        error=f"{type(exc).__name__}:{exc}"
        rc=125

    result={
        "schema":"botmarket.test_job_result.v1",
        "job_id":job_id,
        "started_utc":started,
        "finished_utc":utc_now(),
        "exit_code":int(rc),
        "timed_out":bool(timed_out),
        "error":error,
        "command_kind":"python" if command and command[0]==str(TARGET_PY) else ("bash" if command else None),
        "log_sha256":sha256_file(log_path) if log_path.is_file() else None,
        "network_profile":json.loads(manifest_path.read_text(encoding="utf-8")).get("network_profile") if manifest_path.is_file() else None,
    }
    atomic_json(result_path,result)
    return int(rc)

if __name__=="__main__":
    raise SystemExit(main())
PY
chmod 0755 "$APP/job_runner.py"
chown root:root "$APP/job_runner.py"
"$PY" -m py_compile "$APP/job_runner.py"

log STEP "Install root-only sandbox launcher"
cat > "$LAUNCHER" <<PY
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import pwd
import re
import subprocess
import sys
from pathlib import Path

BASE=Path("$JOBS").resolve()
RUNNER=Path("$APP/job_runner.py").resolve()
JOB_USER="$JOB_USER"
JOB_GROUP="$JOB_GROUP"
JOB_RE=re.compile(r"^job_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
ALLOWED_PREFIXES=("research/","scripts/research/","tests/")
ALLOWED_SUFFIXES={".py",".sh"}
PUBLIC_RESOLV=Path("$STATE/public-resolv.conf").resolve()

def die(msg:str)->None:
    print(f"TEST_LAUNCH_REVIEW:{msg}",file=sys.stderr)
    raise SystemExit(2)

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

if os.geteuid()!=0:
    die("ROOT_REQUIRED")

if len(sys.argv)==2 and sys.argv[1]=="--self-test":
    print("BOTMARKET_TEST_LAUNCHER_SELFTEST_PASS")
    raise SystemExit(0)

if len(sys.argv)!=2 or not JOB_RE.fullmatch(sys.argv[1]):
    die("BAD_JOB_ID")
job_id=sys.argv[1]
job=(BASE/job_id).resolve()
try:
    job.relative_to(BASE)
except ValueError:
    die("JOB_ESCAPE")

manifest_path=job/"job.json"
package=job/"package"
output=job/"output"
for p in (manifest_path,package,output):
    if not p.exists() or p.is_symlink():
        die(f"PATH_INVALID:{p.name}")

try:
    m=json.loads(manifest_path.read_text(encoding="utf-8"))
except Exception as exc:
    die(f"MANIFEST_PARSE:{type(exc).__name__}")

if m.get("schema")!="botmarket.test_job.v1" or m.get("job_id")!=job_id:
    die("MANIFEST_SCHEMA_OR_ID")
if m.get("trading_credentials_available") is not False:
    die("TRADING_CREDENTIAL_BOUNDARY")
repo_head=m.get("repo_head")
if not isinstance(repo_head,str) or not re.fullmatch(r"[0-9a-f]{40,64}",repo_head):
    die("REPO_HEAD")
args=m.get("args")
if not isinstance(args,list) or len(args)>24:
    die("ARGS")
for arg in args:
    if not isinstance(arg,str) or "\x00" in arg or len(arg.encode())>512:
        die("ARG_INVALID")

entry_rel=m.get("entrypoint")
if not isinstance(entry_rel,str):
    die("ENTRYPOINT")
installer_selftest=m.get("installer_selftest") is True
if installer_selftest:
    allowed_install_tests={
        "_deadbeef":"test.py",
        "_cafebabe":"public_test.sh",
    }
    matched=[suffix for suffix,name in allowed_install_tests.items() if job_id.endswith(suffix) and entry_rel==name]
    if len(matched)!=1:
        die("INSTALLER_SELFTEST_BOUNDARY")
else:
    norm=Path(entry_rel).as_posix().lstrip("./")
    if Path(norm).is_absolute() or ".." in Path(norm).parts or ".git" in Path(norm).parts:
        die("ENTRYPOINT_PATH")
    if not any(norm.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        die("ENTRYPOINT_PREFIX")
    if Path(norm).suffix.lower() not in ALLOWED_SUFFIXES:
        die("ENTRYPOINT_SUFFIX")
entry=(package/entry_rel).resolve()
try:
    entry.relative_to(package.resolve())
except ValueError:
    die("ENTRYPOINT_ESCAPE")
if not entry.is_file() or entry.is_symlink():
    die("ENTRYPOINT_NOT_FILE")
if sha256_file(entry)!=m.get("entrypoint_sha256"):
    die("ENTRYPOINT_SHA")

network=m.get("network_profile")
if network not in {"offline","public_research"}:
    die("NETWORK_PROFILE")
timeout=int(m.get("timeout_seconds") or 0)
if timeout<1 or timeout>900:
    die("TIMEOUT")

for root,dirs,files in os.walk(package,followlinks=False):
    rp=Path(root)
    if rp.is_symlink():
        die("PACKAGE_SYMLINK_DIR")
    for name in [*dirs,*files]:
        p=rp/name
        if p.is_symlink():
            die("PACKAGE_SYMLINK")
for root,dirs,files in os.walk(output,followlinks=False):
    rp=Path(root)
    if rp.is_symlink():
        die("OUTPUT_SYMLINK_DIR")
    for name in [*dirs,*files]:
        if (rp/name).is_symlink():
            die("OUTPUT_SYMLINK")

unit=f"botmarket-test-job-{job_id}.service"
show=subprocess.run(
    ["systemctl","show",unit,"-p","LoadState","--value"],
    text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL
)
if show.returncode==0 and show.stdout.strip() not in {"","not-found"}:
    die("UNIT_ALREADY_EXISTS")

common=[
    "systemd-run","--no-block",
    f"--unit={unit}",
    "--description=BotMarketplace isolated Test Executor job",
    "--property=Type=exec",
    f"--property=User={JOB_USER}",
    f"--property=Group={JOB_GROUP}",
    f"--property=WorkingDirectory={package}",
    "--property=UMask=0027",
    "--property=NoNewPrivileges=yes",
    "--property=PrivateTmp=yes",
    "--property=PrivateDevices=yes",
    "--property=ProtectSystem=strict",
    "--property=ProtectHome=yes",
    "--property=ProtectKernelTunables=yes",
    "--property=ProtectKernelModules=yes",
    "--property=ProtectControlGroups=yes",
    "--property=ProtectKernelLogs=yes",
    "--property=ProtectClock=yes",
    "--property=ProtectHostname=yes",
    "--property=ProtectProc=invisible",
    "--property=ProcSubset=pid",
    "--property=RestrictSUIDSGID=yes",
    "--property=RestrictRealtime=yes",
    "--property=RestrictNamespaces=yes",
    "--property=LockPersonality=yes",
    "--property=CapabilityBoundingSet=",
    "--property=AmbientCapabilities=",
    "--property=TasksMax=64",
    "--property=MemoryMax=1073741824",
    "--property=CPUQuota=200%",
    "--property=LimitFSIZE=67108864",
    f"--property=RuntimeMaxSec={timeout+30}",
    f"--property=ReadOnlyPaths={package} {manifest_path} {RUNNER}",
    f"--property=ReadWritePaths={output}",
]

for p in (
    "/etc/botmarket-research",
    "/etc/botmarket-github-control",
    "/etc/botmarket-test-executor",
    "/var/lib/botmarket-github-control",
    "$STATE/repo",
    "$STATE/ssh",
    "/var/lib/botmarket-runner",
    "/var/lib/botmarket-runner-probe",
    "/var/lib/botmarket-tunnel",
    "/run/systemd/private",
    "/run/dbus",
    "/var/run/docker.sock",
    "/run/containerd",
):
    if Path(p).exists():
        common.append(f"--property=InaccessiblePaths={p}")

if network=="offline":
    common += [
        "--property=PrivateNetwork=yes",
        "--property=RestrictAddressFamilies=AF_UNIX",
    ]
else:
    if not PUBLIC_RESOLV.is_file() or PUBLIC_RESOLV.is_symlink():
        die("PUBLIC_RESOLV")
    common += [
        "--property=PrivateNetwork=no",
        "--property=RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
        f"--property=BindReadOnlyPaths={PUBLIC_RESOLV}:/etc/resolv.conf",
        "--property=IPAddressDeny=127.0.0.0/8",
        "--property=IPAddressDeny=::1/128",
        "--property=IPAddressDeny=10.0.0.0/8",
        "--property=IPAddressDeny=172.16.0.0/12",
        "--property=IPAddressDeny=192.168.0.0/16",
        "--property=IPAddressDeny=169.254.0.0/16",
        "--property=IPAddressDeny=fc00::/7",
        "--property=IPAddressDeny=fe80::/10",
        "--property=IPAddressDeny=224.0.0.0/4",
        "--property=IPAddressDeny=ff00::/8",
    ]

cmd=[*common,"$PY",str(RUNNER),job_id]
p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if p.returncode:
    die(f"SYSTEMD_RUN:{p.stderr.strip()[:1200]}")
print(json.dumps({"job_id":job_id,"unit":unit,"network_profile":network,"timeout_seconds":timeout},sort_keys=True))
PY
chmod 0755 "$LAUNCHER"
chown root:root "$LAUNCHER"
"$PY" -m py_compile "$LAUNCHER"

log STEP "Install root-only cancel helper"
cat > "$CANCELER" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, subprocess, sys

JOB_RE=re.compile(r"^job_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")

def die(msg:str)->None:
    print(f"TEST_CANCEL_REVIEW:{msg}",file=sys.stderr)
    raise SystemExit(2)

if os.geteuid()!=0:
    die("ROOT_REQUIRED")
if len(sys.argv)==2 and sys.argv[1]=="--self-test":
    print("BOTMARKET_TEST_CANCEL_SELFTEST_PASS")
    raise SystemExit(0)
if len(sys.argv)!=2 or not JOB_RE.fullmatch(sys.argv[1]):
    die("BAD_JOB_ID")

job_id=sys.argv[1]
unit=f"botmarket-test-job-{job_id}.service"
p=subprocess.run(["systemctl","stop",unit],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if p.returncode:
    die(f"SYSTEMCTL_STOP:{p.stderr.strip()[:800]}")
print(json.dumps({"job_id":job_id,"unit":unit,"stopped":True},sort_keys=True))
PY
chmod 0755 "$CANCELER"
chown root:root "$CANCELER"
"$PY" -m py_compile "$CANCELER"

log STEP "Install root-only retention prune helper"
cat > "$PRUNER" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

JOBS=Path("/var/lib/botmarket-test-executor/jobs").resolve()
POLICY=Path("/etc/botmarket-test-executor/policy.json")
JOB_RE=re.compile(r"^job_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")

def die(msg:str)->None:
    print(f"TEST_PRUNE_REVIEW:{msg}",file=sys.stderr)
    raise SystemExit(2)

def job_created(job_id:str)->datetime:
    try:
        return datetime.strptime(job_id[4:20],"%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        die("JOB_ID_TIMESTAMP")
        raise AssertionError

if os.geteuid()!=0:
    die("ROOT_REQUIRED")
if len(sys.argv)==2 and sys.argv[1]=="--self-test":
    print("BOTMARKET_TEST_PRUNE_SELFTEST_PASS")
    raise SystemExit(0)
if len(sys.argv)!=2 or not JOB_RE.fullmatch(sys.argv[1]):
    die("BAD_JOB_ID")

job_id=sys.argv[1]
raw_job=JOBS/job_id
if raw_job.is_symlink():
    die("JOB_SYMLINK")
job=raw_job.resolve()
try:
    job.relative_to(JOBS)
except ValueError:
    die("PATH_ESCAPE")
if not job.is_dir():
    die("JOB_NOT_FOUND")

manifest=job/"job.json"
result=job/"output/job_result.json"
if not manifest.is_file() or manifest.is_symlink():
    die("MANIFEST_REQUIRED")
if not result.is_file() or result.is_symlink():
    die("COMPLETED_RESULT_REQUIRED")

try:
    obj=json.loads(manifest.read_text(encoding="utf-8"))
    policy=json.loads(POLICY.read_text(encoding="utf-8"))
except Exception:
    die("JSON_INVALID")
if obj.get("job_id")!=job_id:
    die("MANIFEST_JOB_ID_MISMATCH")
if policy.get("schema")!="botmarket.test_executor_policy.v1":
    die("POLICY_SCHEMA")

retention_days=int(policy["completed_job_retention_days"])
max_retained=int(policy["max_retained_jobs"])
if retention_days<1 or max_retained<1:
    die("POLICY_RETENTION")

completed:list[tuple[datetime,str]]=[]
for d in JOBS.iterdir():
    if d.is_symlink() or not d.is_dir() or not JOB_RE.fullmatch(d.name):
        continue
    if not (d/"job.json").is_file() or not (d/"output/job_result.json").is_file():
        continue
    completed.append((job_created(d.name),d.name))
completed.sort(key=lambda item:(item[0],item[1]),reverse=True)

rank=next((idx for idx,(_,jid) in enumerate(completed) if jid==job_id),None)
if rank is None:
    die("COMPLETED_JOB_NOT_INDEXED")
cutoff=datetime.now(timezone.utc)-timedelta(days=retention_days)
if not (job_created(job_id)<cutoff or rank>=max_retained):
    die("NOT_RETENTION_ELIGIBLE")

unit=f"botmarket-test-job-{job_id}.service"
state=subprocess.run(
    ["systemctl","is-active",unit],
    text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
)
active_state=state.stdout.strip()
if active_state in {"active","activating","reloading","deactivating"}:
    die("JOB_ACTIVE")

shutil.rmtree(job)
if job.exists():
    die("DELETE_INCOMPLETE")
print(json.dumps({"job_id":job_id,"pruned":True},sort_keys=True))
PY
chmod 0755 "$PRUNER"
chown root:root "$PRUNER"
"$PY" -m py_compile "$PRUNER"

log STEP "Install restricted sudo policy"
cat > "$SUDOERS" <<EOF
$CTL_USER ALL=(root) NOPASSWD: $LAUNCHER
$CTL_USER ALL=(root) NOPASSWD: $CANCELER
$CTL_USER ALL=(root) NOPASSWD: $PRUNER
EOF
chmod 0440 "$SUDOERS"
visudo -cf "$SUDOERS" >/dev/null

as_testctl_root "$LAUNCHER" --self-test | grep -qx 'BOTMARKET_TEST_LAUNCHER_SELFTEST_PASS' || die "Launcher sudo escalation self-test failed"
as_testctl_root "$CANCELER" --self-test | grep -qx 'BOTMARKET_TEST_CANCEL_SELFTEST_PASS' || die "Cancel sudo escalation self-test failed"
as_testctl_root "$PRUNER" --self-test | grep -qx 'BOTMARKET_TEST_PRUNE_SELFTEST_PASS' || die "Prune sudo escalation self-test failed"

PRUNE_SMOKE_ID="job_20000101T000000Z_feedface"
PRUNE_SMOKE_DIR="$JOBS/$PRUNE_SMOKE_ID"
rm -rf "$PRUNE_SMOKE_DIR"
install -d -m0750 -o "$CTL_USER" -g "$JOB_GROUP" "$PRUNE_SMOKE_DIR"
install -d -m0770 -o "$CTL_USER" -g "$JOB_GROUP" "$PRUNE_SMOKE_DIR/output"
cat > "$PRUNE_SMOKE_DIR/job.json" <<EOF
{"schema":"botmarket.test_job.v1","job_id":"$PRUNE_SMOKE_ID","created_utc":"2000-01-01T00:00:00+00:00"}
EOF
cat > "$PRUNE_SMOKE_DIR/output/job_result.json" <<EOF
{"schema":"botmarket.test_job_result.v1","job_id":"$PRUNE_SMOKE_ID","exit_code":0}
EOF
install -d -m0700 -o "$JOB_USER" -g "$JOB_GROUP" "$PRUNE_SMOKE_DIR/output/nested"
echo "protected worker output" > "$PRUNE_SMOKE_DIR/output/nested/worker-owned.txt"
chown "$JOB_USER:$JOB_GROUP" "$PRUNE_SMOKE_DIR/output/nested/worker-owned.txt"
chmod 0600 "$PRUNE_SMOKE_DIR/output/nested/worker-owned.txt"
chown "$CTL_USER:$JOB_GROUP" "$PRUNE_SMOKE_DIR/job.json" "$PRUNE_SMOKE_DIR/output/job_result.json"
chmod 0440 "$PRUNE_SMOKE_DIR/job.json" "$PRUNE_SMOKE_DIR/output/job_result.json"
as_testctl_root "$PRUNER" "$PRUNE_SMOKE_ID" >/dev/null
[[ ! -e "$PRUNE_SMOKE_DIR" ]] || die "Retention prune helper failed synthetic ownership smoke"
echo "RETENTION_PRUNE_OWNERSHIP_SELFTEST=PASS"

set +e
ARBITRARY_ROOT_PROBE="$(runuser -u "$CTL_USER" -- sudo -n -- /usr/bin/id -u 2>&1)"
ARBITRARY_ROOT_RC=$?
set -e
if [[ $ARBITRARY_ROOT_RC -eq 0 ]]; then
  echo "$ARBITRARY_ROOT_PROBE"
  die "Test Executor control user unexpectedly has arbitrary sudo"
fi
echo "ARBITRARY_ROOT_SUDO=DENIED_AS_REQUIRED"

log STEP "Install MCP server"
cat > "$APP/server.py" <<'PY'
from __future__ import annotations

import grp
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from mcp.server.mcpserver import MCPServer
except Exception:
    from mcp.server.fastmcp import FastMCP as MCPServer

NAME="BotMarketplace Test Executor"
STATE=Path(os.environ["BM_TEST_STATE"]).resolve()
REPO=Path(os.environ["BM_TEST_REPO_DIR"]).resolve()
JOBS=(STATE/"jobs").resolve()
URL=os.environ["BM_TEST_REPO_URL"]
BRANCH=os.getenv("BM_TEST_BRANCH","main")
KEY=Path(os.environ["BM_TEST_SSH_KEY"])
KH=Path(os.environ["BM_TEST_KNOWN_HOSTS"])
POLICY_PATH=Path(os.environ["BM_TEST_POLICY"])
HOST=os.getenv("BM_TEST_HOST","127.0.0.1")
PORT=int(os.getenv("BM_TEST_PORT","8769"))
TARGET_PY=os.environ["BM_TEST_PYTHON"]
JOB_GROUP_NAME=os.environ["BM_TEST_JOB_GROUP"]
JOB_GID=grp.getgrnam(JOB_GROUP_NAME).gr_gid
MAX_TEXT=int(os.getenv("BM_TEST_MAX_TEXT_BYTES","262144"))

LAUNCHER="/usr/local/sbin/botmarket-test-launch"
CANCELER="/usr/local/sbin/botmarket-test-cancel"
PRUNER="/usr/local/sbin/botmarket-test-prune"
JOB_RE=re.compile(r"^job_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")

mcp=MCPServer(NAME)

def utc_now()->datetime:
    return datetime.now(timezone.utc)

def iso(dt:datetime)->str:
    return dt.isoformat()

def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def policy()->dict[str,Any]:
    obj=json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if obj.get("schema")!="botmarket.test_executor_policy.v1":
        raise ValueError("POLICY_SCHEMA")
    return obj

def sshcmd()->str:
    return f"ssh -i {KEY} -o IdentitiesOnly=yes -o UserKnownHostsFile={KH} -o StrictHostKeyChecking=yes -o BatchMode=yes"

def git(args:list[str],check:bool=True)->subprocess.CompletedProcess[str]:
    env=os.environ.copy()
    env["GIT_SSH_COMMAND"]=sshcmd()
    p=subprocess.run(
        ["git","-C",str(REPO),*args],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        env=env,timeout=120,
    )
    if check and p.returncode:
        raise ValueError(f"GIT_FAILED rc={p.returncode} stderr={p.stderr.strip()[:1600]}")
    return p

def repo_head()->str:
    return git(["rev-parse","HEAD"]).stdout.strip()

def repo_branch()->str:
    return git(["branch","--show-current"]).stdout.strip()

def repo_status()->str:
    return git(["status","--porcelain=v1","--untracked-files=all"]).stdout

def resolve_job(job_id:str)->Path:
    if not isinstance(job_id,str) or not JOB_RE.fullmatch(job_id):
        raise ValueError("BAD_JOB_ID")
    p=(JOBS/job_id).resolve()
    p.relative_to(JOBS)
    return p

def read_json(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def atomic_json(path:Path,obj:dict[str,Any])->None:
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(tmp,path)

def set_job_group(path:Path)->None:
    # Control user owns the path and is a supplementary member of JOB_GROUP.
    # This avoids setgid chmod operations, which are intentionally blocked by
    # RestrictSUIDSGID=true on the MCP control service.
    os.chown(path,-1,JOB_GID)

def validate_entrypoint(path:str)->str:
    if not isinstance(path,str) or not path or "\x00" in path or Path(path).is_absolute():
        raise ValueError("ENTRYPOINT_PATH")
    norm=Path(path).as_posix().lstrip("./")
    parts=Path(norm).parts
    if ".." in parts or ".git" in parts:
        raise ValueError("ENTRYPOINT_PATH")
    p=policy()
    if not any(norm.startswith(prefix) for prefix in p["allowed_entrypoint_prefixes"]):
        raise ValueError("ENTRYPOINT_PREFIX_FORBIDDEN")
    if Path(norm).suffix.lower() not in set(p["allowed_entrypoint_suffixes"]):
        raise ValueError("ENTRYPOINT_SUFFIX_FORBIDDEN")
    return norm

def validate_args(args:list[str]|None)->list[str]:
    p=policy()
    args=[] if args is None else args
    if not isinstance(args,list) or len(args)>int(p["max_args"]):
        raise ValueError("ARGS")
    out=[]
    for x in args:
        if not isinstance(x,str) or "\x00" in x or len(x.encode())>int(p["max_arg_bytes"]):
            raise ValueError("ARG_INVALID")
        out.append(x)
    return out

def unit_state(job_id:str)->dict[str,Any]:
    unit=f"botmarket-test-job-{job_id}.service"
    p=subprocess.run(
        ["systemctl","show",unit,
         "-p","LoadState","-p","ActiveState","-p","SubState",
         "-p","Result","-p","ExecMainCode","-p","ExecMainStatus","--no-pager"],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,
    )
    data={"unit":unit}
    if p.returncode:
        data.update({"load_state":"not-found","active_state":"unknown","sub_state":"unknown"})
        return data
    for line in p.stdout.splitlines():
        if "=" in line:
            k,v=line.split("=",1)
            data[k.lower()]=v
    return data

def recent_manifests()->list[dict[str,Any]]:
    out=[]
    if not JOBS.exists():
        return out
    for d in JOBS.iterdir():
        if not d.is_dir() or not JOB_RE.fullmatch(d.name):
            continue
        mp=d/"job.json"
        if not mp.is_file():
            continue
        try:
            out.append(read_json(mp))
        except Exception:
            continue
    return out

def prune_completed_jobs()->dict[str,int]:
    p=policy()
    now=utc_now()
    cutoff=now-timedelta(days=int(p["completed_job_retention_days"]))
    jobs=[]
    for m in recent_manifests():
        try:
            job_id=m["job_id"]
            created=datetime.strptime(job_id[4:20],"%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            job=resolve_job(job_id)
        except Exception:
            continue
        result=(job/"output/job_result.json").is_file()
        if result:
            jobs.append((created,job_id,job))
    jobs.sort(key=lambda x:(x[0],x[1]),reverse=True)
    removed=0
    for idx,(created,job_id,job) in enumerate(jobs):
        if created<cutoff or idx>=int(p["max_retained_jobs"]):
            if not job.exists():
                continue
            prune=subprocess.run(
                ["sudo","-n",PRUNER,job_id],
                text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,
            )
            if prune.returncode:
                raise ValueError(
                    f"RETENTION_PRUNE_FAILED job_id={job_id} stderr={prune.stderr.strip()[:800]}"
                )
            if job.exists():
                raise ValueError(f"RETENTION_PRUNE_INCOMPLETE job_id={job_id}")
            removed+=1
    return {"removed":removed}

def prune_orphan_jobs()->dict[str,int]:
    now=utc_now().timestamp()
    removed=0
    if not JOBS.exists():
        return {"removed":0}
    for d in JOBS.iterdir():
        if not d.is_dir() or not JOB_RE.fullmatch(d.name):
            continue
        if (d/"job.json").exists():
            continue
        try:
            age=max(0.0,now-d.stat().st_mtime)
        except FileNotFoundError:
            continue
        if age>=3600:
            shutil.rmtree(d,ignore_errors=True)
            removed+=1
    return {"removed":removed}

def rate_limit_check()->dict[str,int]:
    p=policy()
    now=utc_now()
    hour_cut=now-timedelta(hours=1)
    day=now.date()
    hour_count=0
    day_count=0
    running=0
    for m in recent_manifests():
        try:
            created=datetime.fromisoformat(m["created_utc"])
        except Exception:
            continue
        if created>=hour_cut:
            hour_count+=1
        if created.date()==day:
            day_count+=1
        s=unit_state(str(m.get("job_id") or ""))
        if s.get("activestate") in {"active","activating","reloading"}:
            running+=1
    if hour_count>=int(p["max_runs_per_rolling_hour"]):
        raise ValueError("RUN_RATE_LIMIT_HOURLY")
    if day_count>=int(p["max_runs_per_utc_day"]):
        raise ValueError("RUN_RATE_LIMIT_DAILY")
    if running>=int(p["max_concurrent_jobs"]):
        raise ValueError("RUN_CONCURRENCY_LIMIT")
    return {"rolling_hour":hour_count,"utc_day":day_count,"running":running}

def secret_like_path(name:str)->bool:
    p=Path(name)
    base=p.name.lower()
    if base in {".env","id_rsa","id_ed25519","authorized_keys",".npmrc",".pypirc"}:
        return True
    if base.startswith(".env.") and base not in {".env.example",".env.sample"}:
        return True
    if p.suffix.lower() in {".pem",".p12",".pfx"}:
        return True
    if p.suffix.lower()==".key" and base not in {"package-lock.key"}:
        return True
    return False

def snapshot_repo(head:str,package:Path)->dict[str,int]:
    p=policy()

    def ensure_package_dir(path:Path)->None:
        path=path.resolve()
        path.relative_to(package.resolve())
        rel=path.relative_to(package.resolve())
        cur=package.resolve()
        set_job_group(cur)
        cur.chmod(0o750)
        for part in rel.parts:
            cur=cur/part
            if not cur.exists():
                cur.mkdir(mode=0o750)
            if not cur.is_dir() or cur.is_symlink():
                raise ValueError(f"REPO_DIR_INVALID:{cur}")
            set_job_group(cur)
            cur.chmod(0o750)
    raw=subprocess.run(
        ["git","-C",str(REPO),"archive","--format=tar",head],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120,
    )
    if raw.returncode:
        raise ValueError(f"GIT_ARCHIVE_FAILED:{raw.stderr.decode(errors='replace')[:800]}")
    if len(raw.stdout)>int(p["max_repo_archive_bytes"]):
        raise ValueError("REPO_ARCHIVE_TOO_LARGE")
    total=0
    count=0
    with tarfile.open(fileobj=io.BytesIO(raw.stdout),mode="r:") as tf:
        members=tf.getmembers()
        if len(members)>int(p["max_repo_files"]):
            raise ValueError("REPO_FILE_COUNT")
        for m in members:
            name=Path(m.name).as_posix()
            if m.issym() or m.islnk() or m.isdev():
                raise ValueError(f"REPO_SPECIAL_FILE:{name}")
            if Path(name).is_absolute() or ".." in Path(name).parts or ".git" in Path(name).parts:
                raise ValueError(f"REPO_PATH:{name}")
            if secret_like_path(name):
                raise ValueError(f"REPO_SECRET_LIKE_PATH:{name}")
            target=(package/name).resolve()
            target.relative_to(package.resolve())
            if m.isdir():
                ensure_package_dir(target)
                continue
            if not m.isfile():
                raise ValueError(f"REPO_MEMBER_TYPE:{name}")
            f=tf.extractfile(m)
            if f is None:
                raise ValueError(f"REPO_EXTRACT:{name}")
            data=f.read()
            total+=len(data)
            if total>int(p["max_repo_archive_bytes"]):
                raise ValueError("REPO_EXTRACTED_TOO_LARGE")
            ensure_package_dir(target.parent)
            target.write_bytes(data)
            set_job_group(target)
            # Preserve only the executable semantic from Git; never preserve
            # owner/group/world write bits from the repository archive.
            target.chmod(0o550 if (m.mode & 0o111) else 0o440)
            count+=1
    return {"file_count":count,"bytes":total}

def read_text_file(path:Path,offset:int,max_bytes:int)->dict[str,Any]:
    n=max(1,min(int(max_bytes),MAX_TEXT))
    off=max(0,int(offset))
    if not path.is_file() or path.is_symlink():
        raise ValueError("FILE_NOT_FOUND")
    data=path.read_bytes()
    chunk=data[off:off+n]
    while chunk:
        try:
            text=chunk.decode("utf-8")
            break
        except UnicodeDecodeError as exc:
            if exc.start>=len(chunk)-4:
                chunk=chunk[:-1]
                continue
            raise ValueError("NOT_UTF8_TEXT") from exc
    else:
        text=""
    nxt=off+len(chunk)
    return {
        "size_bytes":len(data),
        "sha256":sha256_bytes(data),
        "offset_bytes":off,
        "text":text,
        "next_offset_bytes":None if nxt>=len(data) else nxt,
    }

def filesystem_boundary_selftest()->dict[str,Any]:
    probe=(JOBS/f".service-fs-selftest-{os.getpid()}").resolve()
    try:
        probe.relative_to(JOBS)
        package=probe/"package"
        output=probe/"output"
        manifest=probe/"job.json"
        probe.mkdir(mode=0o750,exist_ok=False)
        package.mkdir(mode=0o750)
        output.mkdir(mode=0o770)
        for pth,mode in ((probe,0o750),(package,0o750),(output,0o770)):
            set_job_group(pth)
            pth.chmod(mode)
        sample=package/"sample.py"
        sample.write_text("print('ok')\n",encoding="utf-8")
        set_job_group(sample)
        sample.chmod(0o440)
        atomic_json(manifest,{"schema":"botmarket.service_fs_selftest.v1"})
        set_job_group(manifest)
        manifest.chmod(0o440)
        checks={
            "probe_gid":probe.stat().st_gid,
            "package_gid":package.stat().st_gid,
            "output_gid":output.stat().st_gid,
            "sample_gid":sample.stat().st_gid,
            "manifest_gid":manifest.stat().st_gid,
            "output_group_writable":bool(output.stat().st_mode & 0o020),
        }
        ok=all(checks[k]==JOB_GID for k in ("probe_gid","package_gid","output_gid","sample_gid","manifest_gid")) and checks["output_group_writable"]
        return {"ok":ok,**checks}
    except Exception as exc:
        return {"ok":False,"error":f"{type(exc).__name__}:{exc}"}
    finally:
        shutil.rmtree(probe,ignore_errors=True)

def privilege_bridge_selftest()->dict[str,Any]:
    specs=(
        ("launcher",LAUNCHER,"BOTMARKET_TEST_LAUNCHER_SELFTEST_PASS"),
        ("canceler",CANCELER,"BOTMARKET_TEST_CANCEL_SELFTEST_PASS"),
        ("pruner",PRUNER,"BOTMARKET_TEST_PRUNE_SELFTEST_PASS"),
    )
    checks={}
    for name,path,token in specs:
        p=subprocess.run(
            ["sudo","-n",path,"--self-test"],
            text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,
        )
        checks[name]={
            "ok":p.returncode==0 and p.stdout.strip()==token,
            "returncode":p.returncode,
            "stdout":p.stdout.strip()[:500],
            "stderr":p.stderr.strip()[:500],
        }
    return {"ok":all(x["ok"] for x in checks.values()),"helpers":checks}

@mcp.tool()
def get_test_executor_info()->dict[str,Any]:
    p=policy()
    h=repo_head()
    counts={"rolling_hour":0,"utc_day":0,"running":0}
    try:
        counts=rate_limit_check()
    except ValueError as exc:
        # expose counters even when a limit is reached
        now=utc_now()
        manifests=recent_manifests()
        counts={
            "rolling_hour":sum(
                1 for m in manifests
                if datetime.fromisoformat(m["created_utc"])>=now-timedelta(hours=1)
            ),
            "utc_day":sum(
                1 for m in manifests
                if datetime.fromisoformat(m["created_utc"]).date()==now.date()
            ),
            "running":sum(
                1 for m in manifests
                if unit_state(m["job_id"]).get("activestate") in {"active","activating","reloading"}
            ),
        }
    return {
        "name":NAME,
        "repo_url":URL,
        "branch":repo_branch(),
        "head":h,
        "worktree_clean":not bool(repo_status()),
        "repo_write":False,
        "arbitrary_shell_tool":False,
        "trading_credentials_available_to_jobs":False,
        "network_profiles":p["network_profiles"],
        "limits":{
            "max_timeout_seconds":p["max_timeout_seconds"],
            "max_runs_per_rolling_hour":p["max_runs_per_rolling_hour"],
            "max_runs_per_utc_day":p["max_runs_per_utc_day"],
            "max_concurrent_jobs":p["max_concurrent_jobs"],
            "completed_job_retention_days":p["completed_job_retention_days"],
            "max_retained_jobs":p["max_retained_jobs"],
        },
        "current_counts":counts,
        "privilege_bridge":privilege_bridge_selftest(),
        "filesystem_boundary":filesystem_boundary_selftest(),
    }

@mcp.tool()
def refresh_repo(expected_head:str|None=None)->dict[str,Any]:
    if repo_status():
        raise ValueError("WORKTREE_DIRTY")
    if repo_branch()!=BRANCH:
        raise ValueError("UNEXPECTED_BRANCH")
    before=repo_head()
    git(["fetch","--prune","origin",BRANCH])
    origin=git(["rev-parse",f"origin/{BRANCH}"]).stdout.strip()
    if expected_head is not None and origin!=expected_head:
        raise ValueError(f"REMOTE_HEAD_MISMATCH origin={origin}")
    git(["merge","--ff-only",f"origin/{BRANCH}"])
    after=repo_head()
    if after!=origin:
        raise ValueError("REFRESH_NOT_AT_ORIGIN")
    return {"before":before,"after":after,"origin":origin,"worktree_clean":not bool(repo_status())}

@mcp.tool()
def run_repo_test(
    repo_head_sha:str,
    entrypoint:str,
    args:list[str]|None=None,
    network_profile:str="offline",
    timeout_seconds:int|None=None,
)->dict[str,Any]:
    p=policy()
    if repo_status():
        raise ValueError("WORKTREE_DIRTY")
    if repo_branch()!=BRANCH:
        raise ValueError("UNEXPECTED_BRANCH")
    local=repo_head()
    git(["fetch","--prune","origin",BRANCH])
    origin=git(["rev-parse",f"origin/{BRANCH}"]).stdout.strip()
    if local!=origin:
        raise ValueError(f"REPO_NOT_REFRESHED local={local} origin={origin}")
    if repo_head_sha!=local:
        raise ValueError(f"HEAD_MISMATCH actual={local}")

    entry=validate_entrypoint(entrypoint)
    argv=validate_args(args)
    if network_profile not in set(p["network_profiles"]):
        raise ValueError("NETWORK_PROFILE")
    timeout=int(timeout_seconds or p["default_timeout_seconds"])
    if timeout<1 or timeout>int(p["max_timeout_seconds"]):
        raise ValueError("TIMEOUT")

    prune_orphan_jobs()
    prune_completed_jobs()
    counts=rate_limit_check()

    job_id=utc_now().strftime("job_%Y%m%dT%H%M%SZ_")+secrets.token_hex(4)
    job=resolve_job(job_id)
    package=job/"package"
    output=job/"output"
    job.mkdir(mode=0o750,parents=False,exist_ok=False)
    package.mkdir(mode=0o750)
    output.mkdir(mode=0o770)
    for pth,mode in ((job,0o750),(package,0o750),(output,0o770)):
        set_job_group(pth)
        pth.chmod(mode)

    try:
        snap=snapshot_repo(local,package)
        ep=(package/entry).resolve()
        ep.relative_to(package.resolve())
        if not ep.is_file() or ep.is_symlink():
            raise ValueError("ENTRYPOINT_NOT_IN_SNAPSHOT")
        manifest={
            "schema":"botmarket.test_job.v1",
            "job_id":job_id,
            "created_utc":iso(utc_now()),
            "repo_head":local,
            "repo_url":URL,
            "entrypoint":entry,
            "entrypoint_sha256":sha256_file(ep),
            "args":argv,
            "network_profile":network_profile,
            "timeout_seconds":timeout,
            "snapshot_file_count":snap["file_count"],
            "snapshot_bytes":snap["bytes"],
            "trading_credentials_available":False,
        }
        atomic_json(job/"job.json",manifest)
        set_job_group(job/"job.json")
        os.chmod(job/"job.json",0o440)

        launch=subprocess.run(
            ["sudo","-n",LAUNCHER,job_id],
            text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,
        )
        if launch.returncode:
            atomic_json(output/"launch_error.json",{
                "schema":"botmarket.test_launch_error.v1",
                "job_id":job_id,
                "returncode":launch.returncode,
                "stderr":launch.stderr.strip()[:4000],
            })
            raise ValueError(f"LAUNCH_FAILED:{launch.stderr.strip()[:1200]}")

        return {
            "job_id":job_id,
            "repo_head":local,
            "entrypoint":entry,
            "entrypoint_sha256":manifest["entrypoint_sha256"],
            "network_profile":network_profile,
            "timeout_seconds":timeout,
            "unit_state":unit_state(job_id),
            "rate_counts_before_launch":counts,
        }
    except Exception:
        raise

@mcp.tool()
def get_job_status(job_id:str)->dict[str,Any]:
    job=resolve_job(job_id)
    manifest=read_json(job/"job.json")
    result=None
    rp=job/"output/job_result.json"
    if rp.is_file():
        result=read_json(rp)
    return {
        "job_id":job_id,
        "manifest":manifest,
        "unit_state":unit_state(job_id),
        "result":result,
        "log_present":(job/"output/run.log").is_file(),
    }

@mcp.tool()
def list_recent_jobs(limit:int=20)->dict[str,Any]:
    n=max(1,min(int(limit),100))
    items=[]
    for m in recent_manifests():
        try:
            items.append({
                "job_id":m["job_id"],
                "created_utc":m["created_utc"],
                "repo_head":m["repo_head"],
                "entrypoint":m["entrypoint"],
                "network_profile":m["network_profile"],
                "unit_state":unit_state(m["job_id"]),
                "result":read_json(resolve_job(m["job_id"])/"output/job_result.json")
                    if (resolve_job(m["job_id"])/"output/job_result.json").is_file() else None,
            })
        except Exception:
            continue
    items.sort(key=lambda x:x["created_utc"],reverse=True)
    return {"jobs":items[:n]}

@mcp.tool()
def read_job_log(job_id:str,offset_bytes:int=0,max_bytes:int=65536)->dict[str,Any]:
    job=resolve_job(job_id)
    out=read_text_file(job/"output/run.log",offset_bytes,max_bytes)
    out["job_id"]=job_id
    out["path"]="output/run.log"
    return out

@mcp.tool()
def list_job_files(job_id:str,recursive:bool=False,limit:int=200)->dict[str,Any]:
    job=resolve_job(job_id)
    root=(job/"output").resolve()
    n=max(1,min(int(limit),1000))
    it=root.rglob("*") if recursive else root.iterdir()
    entries=[]
    for x in it:
        if x.is_symlink():
            continue
        rel=x.resolve().relative_to(root).as_posix()
        entries.append({
            "path":rel,
            "kind":"dir" if x.is_dir() else "file",
            "size_bytes":None if x.is_dir() else x.stat().st_size,
        })
        if len(entries)>=n:
            break
    return {"job_id":job_id,"entries":sorted(entries,key=lambda x:x["path"]),"truncated":len(entries)>=n}

@mcp.tool()
def read_job_text(job_id:str,path:str,offset_bytes:int=0,max_bytes:int=65536)->dict[str,Any]:
    if not isinstance(path,str) or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError("PATH")
    job=resolve_job(job_id)
    root=(job/"output").resolve()
    target=(root/path).resolve()
    target.relative_to(root)
    out=read_text_file(target,offset_bytes,max_bytes)
    out["job_id"]=job_id
    out["path"]=Path(path).as_posix()
    return out

@mcp.tool()
def cancel_job(job_id:str)->dict[str,Any]:
    resolve_job(job_id)
    p=subprocess.run(
        ["sudo","-n",CANCELER,job_id],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,
    )
    if p.returncode:
        raise ValueError(f"CANCEL_FAILED:{p.stderr.strip()[:1200]}")
    return {"job_id":job_id,"cancelled":True,"unit_state":unit_state(job_id)}

if __name__=="__main__":
    fscheck=filesystem_boundary_selftest()
    if not fscheck["ok"]:
        raise SystemExit("FILESYSTEM_BOUNDARY_SELFTEST_FAILED:"+json.dumps(fscheck,sort_keys=True))
    bridge=privilege_bridge_selftest()
    if not bridge["ok"]:
        raise SystemExit("PRIVILEGE_BRIDGE_SELFTEST_FAILED:"+json.dumps(bridge,sort_keys=True))
    try:
        mcp.run(
            transport="streamable-http",
            host=HOST,
            port=PORT,
            streamable_http_path="/mcp",
            stateless_http=True,
            json_response=True,
        )
    except TypeError:
        mcp.run(
            transport="streamable-http",
            host=HOST,
            port=PORT,
            streamable_http_path="/mcp",
        )
PY

chmod 0755 "$APP/server.py"
chown root:root "$APP/server.py"
"$PY" -m py_compile "$APP/server.py"
echo "SERVER_PY_COMPILE=PASS"

log STEP "Install MCP service"
cat > "$UNIT" <<EOF
[Unit]
Description=BotMarketplace Test Executor MCP
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$CTL_USER
Group=$CTL_GROUP
SupplementaryGroups=$JOB_GROUP
WorkingDirectory=$STATE
Environment=HOME=$STATE
EnvironmentFile=$ENVF
ExecStart=$PY $APP/server.py
Restart=on-failure
RestartSec=3
TimeoutStopSec=20
UMask=0027
# Deliberately NOT using NoNewPrivileges/empty CapabilityBoundingSet here:
# this control service must traverse the exact sudoers bridge to the three
# root-owned helpers (launch/cancel/retention-prune). The helpers themselves
# remain narrowly scoped; jobs stay tightly sandboxed.
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
ProtectKernelLogs=true
RestrictSUIDSGID=true
LockPersonality=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
ReadWritePaths=$REPODIR $JOBS
ReadOnlyPaths=$ENVF $POLICY $APP $SSHDIR $STATE/public-resolv.conf

[Install]
WantedBy=multi-user.target
EOF
chmod 0644 "$UNIT"

systemctl daemon-reload
systemctl enable botmarket-test-executor.service >/dev/null

if ! systemctl restart botmarket-test-executor.service; then
  echo "[WARN] New Test Executor failed to restart; attempting bounded runtime rollback" >&2
  if [[ "$SERVICE_WAS_ACTIVE" -eq 1 && -f "$BACKUP/server.py.bak" && -f "$BACKUP/botmarket-test-executor.service.bak" ]]; then
    cp -a "$BACKUP/server.py.bak" "$APP/server.py"
    cp -a "$BACKUP/botmarket-test-executor.service.bak" "$UNIT"
    [[ -f "$BACKUP/env.bak" ]] && cp -a "$BACKUP/env.bak" "$ENVF"
    [[ -f "$BACKUP/policy.json.bak" ]] && cp -a "$BACKUP/policy.json.bak" "$POLICY"
    [[ -f "$BACKUP/botmarket-test-executor.bak" ]] && cp -a "$BACKUP/botmarket-test-executor.bak" "$SUDOERS"
    systemctl daemon-reload
    systemctl restart botmarket-test-executor.service || true
  fi
  systemctl --no-pager --full status botmarket-test-executor.service || true
  journalctl -u botmarket-test-executor.service -n100 --no-pager || true
  die "Test Executor restart failed; bounded rollback attempted"
fi
sleep 2

systemctl is-active --quiet botmarket-test-executor.service || {
  systemctl --no-pager --full status botmarket-test-executor.service || true
  journalctl -u botmarket-test-executor.service -n100 --no-pager || true
  die "Test Executor service is not active after explicit restart"
}

ss -ltnH | awk '{print $4}' | grep -Eq "127\.0\.0\.1:${PORT}$|\[::1\]:${PORT}$"   || die "Port $PORT not listening"

log STEP "Run isolated offline install self-test"
SELF_ID="job_$(date -u +%Y%m%dT%H%M%SZ)_deadbeef"
SELF_DIR="$JOBS/$SELF_ID"
rm -rf "$SELF_DIR"
install -d -m2750 -o "$CTL_USER" -g "$JOB_GROUP" "$SELF_DIR"
install -d -m0750 -o "$CTL_USER" -g "$JOB_GROUP" "$SELF_DIR/package"
install -d -m0770 -o "$CTL_USER" -g "$JOB_GROUP" "$SELF_DIR/output"
chmod 0770 "$SELF_DIR/output"

cat > "$SELF_DIR/package/test.py" <<'PY'
print("BOTMARKET_TEST_EXECUTOR_INSTALL_JOB_PASS")
PY
chown "$CTL_USER:$JOB_GROUP" "$SELF_DIR/package/test.py"
chmod 0440 "$SELF_DIR/package/test.py"
SELF_SHA="$(sha256sum "$SELF_DIR/package/test.py" | awk '{print $1}')"

cat > "$SELF_DIR/job.json" <<EOF
{
  "schema": "botmarket.test_job.v1",
  "job_id": "$SELF_ID",
  "created_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo_head": "$LOCAL_HEAD",
  "repo_url": "$REPO_URL",
  "entrypoint": "test.py",
  "entrypoint_sha256": "$SELF_SHA",
  "args": [],
  "network_profile": "offline",
  "timeout_seconds": 20,
  "snapshot_file_count": 1,
  "snapshot_bytes": 52,
  "trading_credentials_available": false,
  "installer_selftest": true
}
EOF
chown "$CTL_USER:$JOB_GROUP" "$SELF_DIR/job.json"
chmod 0440 "$SELF_DIR/job.json"

as_testctl_root "$LAUNCHER" "$SELF_ID" >/dev/null
READY=0
for _ in $(seq 1 40); do
  if [[ -f "$SELF_DIR/output/job_result.json" ]]; then
    READY=1
    break
  fi
  sleep 0.5
done
[[ "$READY" -eq 1 ]] || {
  systemctl --no-pager --full status "botmarket-test-job-$SELF_ID.service" || true
  [[ -f "$SELF_DIR/output/run.log" ]] && cat "$SELF_DIR/output/run.log" || true
  die "Install self-test did not complete"
}

"$PY" - "$SELF_DIR/output/job_result.json" "$SELF_DIR/output/run.log" <<'PY'
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
log=Path(sys.argv[2]).read_text()
assert r["exit_code"]==0, r
assert r["timed_out"] is False, r
assert "BOTMARKET_TEST_EXECUTOR_INSTALL_JOB_PASS" in log, log
print("ISOLATED_JOB_SELFTEST=PASS")
PY

systemctl stop "botmarket-test-job-$SELF_ID.service" >/dev/null 2>&1 || true
systemctl reset-failed "botmarket-test-job-$SELF_ID.service" >/dev/null 2>&1 || true
rm -rf "$SELF_DIR"

log STEP "Run isolated public-research network self-test"
PUBLIC_ID="job_$(date -u +%Y%m%dT%H%M%SZ)_cafebabe"
PUBLIC_DIR="$JOBS/$PUBLIC_ID"
rm -rf "$PUBLIC_DIR"
install -d -m2750 -o "$CTL_USER" -g "$JOB_GROUP" "$PUBLIC_DIR"
install -d -m2750 -o "$CTL_USER" -g "$JOB_GROUP" "$PUBLIC_DIR/package"
install -d -m0770 -o "$CTL_USER" -g "$JOB_GROUP" "$PUBLIC_DIR/output"
cat > "$PUBLIC_DIR/package/public_test.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
code=""
curl_rc=1
for attempt in 1 2 3; do
  set +e
  code="$(curl -4 --http1.1 -sS --max-time 15 -o /dev/null -w '%{http_code}' https://announcements.bybit.com/en-US/ 2>/dev/null)"
  curl_rc=$?
  set -e
  if [[ $curl_rc -eq 0 && "$code" =~ ^[1-5][0-9][0-9]$ ]]; then
    break
  fi
  if (( attempt < 3 )); then
    sleep "$((attempt*2))"
  fi
done
if [[ $curl_rc -ne 0 || ! "$code" =~ ^[1-5][0-9][0-9]$ ]]; then
  echo "PUBLIC_HTTPS_TRANSPORT_FAILED_AFTER_RETRIES rc=$curl_rc code=$code"
  exit 9
fi
echo "PUBLIC_HTTP_CODE=$code"
if curl -sS --max-time 2 http://127.0.0.1:8768/mcp >/dev/null 2>&1; then
  echo "LOOPBACK_MCP_UNEXPECTEDLY_REACHABLE"
  exit 10
fi
echo "BOTMARKET_TEST_EXECUTOR_PUBLIC_NETWORK_PASS"
SH
chown "$CTL_USER:$JOB_GROUP" "$PUBLIC_DIR/package/public_test.sh"
chmod 0550 "$PUBLIC_DIR/package/public_test.sh"
PUBLIC_SHA="$(sha256sum "$PUBLIC_DIR/package/public_test.sh" | awk '{print $1}')"
cat > "$PUBLIC_DIR/job.json" <<EOF
{
  "schema": "botmarket.test_job.v1",
  "job_id": "$PUBLIC_ID",
  "created_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repo_head": "$LOCAL_HEAD",
  "repo_url": "$REPO_URL",
  "entrypoint": "public_test.sh",
  "entrypoint_sha256": "$PUBLIC_SHA",
  "args": [],
  "network_profile": "public_research",
  "timeout_seconds": 30,
  "snapshot_file_count": 1,
  "snapshot_bytes": 1,
  "trading_credentials_available": false,
  "installer_selftest": true
}
EOF
chown "$CTL_USER:$JOB_GROUP" "$PUBLIC_DIR/job.json"
chmod 0440 "$PUBLIC_DIR/job.json"

as_testctl_root "$LAUNCHER" "$PUBLIC_ID" >/dev/null
PUBLIC_READY=0
for _ in $(seq 1 60); do
  if [[ -f "$PUBLIC_DIR/output/job_result.json" ]]; then
    PUBLIC_READY=1
    break
  fi
  sleep 0.5
done
[[ "$PUBLIC_READY" -eq 1 ]] || {
  systemctl --no-pager --full status "botmarket-test-job-$PUBLIC_ID.service" || true
  [[ -f "$PUBLIC_DIR/output/run.log" ]] && cat "$PUBLIC_DIR/output/run.log" || true
  die "Public-network self-test did not complete"
}
"$PY" - "$PUBLIC_DIR/output/job_result.json" "$PUBLIC_DIR/output/run.log" <<'PY'
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
log=Path(sys.argv[2]).read_text()
assert r["exit_code"]==0, r
assert "BOTMARKET_TEST_EXECUTOR_PUBLIC_NETWORK_PASS" in log, log
assert "LOOPBACK_MCP_UNEXPECTEDLY_REACHABLE" not in log, log
print("PUBLIC_NETWORK_SANDBOX_SELFTEST=PASS")
PY
systemctl stop "botmarket-test-job-$PUBLIC_ID.service" >/dev/null 2>&1 || true
systemctl reset-failed "botmarket-test-job-$PUBLIC_ID.service" >/dev/null 2>&1 || true
rm -rf "$PUBLIC_DIR"

log STEP "Probe local MCP"
set +e
TMP="$(mktemp)"
HTTP_CODE="$(curl -sS -N --max-time 2 -o "$TMP" -w '%{http_code}'   -H 'Accept: application/json, text/event-stream' "http://$HOST:$PORT/mcp" 2>/dev/null)"
CURL_RC=$?
set -e
rm -f "$TMP"
if [[ "$HTTP_CODE" != "200" && $CURL_RC -ne 0 ]]; then
  die "Local Test Executor MCP probe failed: HTTP=$HTTP_CODE curl_rc=$CURL_RC"
fi

echo
echo "=== BOTMARKETPLACE TEST EXECUTOR V1 INSTALLED ==="
echo "Repository read: PASS"
echo "Repository write: DENIED_AS_REQUIRED"
echo "MCP service filesystem boundary self-test: PASS"
echo "MCP service restricted sudo bridge self-test: PASS"
echo "Isolated offline job self-test: PASS"
echo "Public research network sandbox self-test: PASS"
echo "Local MCP: http://$HOST:$PORT/mcp"
echo "Service: botmarket-test-executor.service"
echo "Control user: $CTL_USER"
echo "Job user: $JOB_USER"
echo "Network profiles: offline, public_research"
echo "Autonomous limit: 6 runs / rolling hour, 30 runs / UTC day, 1 concurrent"
echo "Trading credentials available to jobs: NO"
echo "Research Runner: NOT MODIFIED"
echo "GitHub Control: NOT MODIFIED"
echo "Backup: $BACKUP"
