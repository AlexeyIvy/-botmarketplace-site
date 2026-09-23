#!/usr/bin/env bash
set -Eeuo pipefail

REPO="${BM_GH_REPO:-AlexeyIvy/-botmarketplace-site}"
URL="git@github.com:${REPO}.git"
BRANCH="${BM_GH_BRANCH:-main}"

USER_NAME="botmarket-github"
GROUP_NAME="botmarket-github"
STATE="/var/lib/botmarket-github-control"
REPODIR="$STATE/repo"
SSHDIR="$STATE/ssh"
KEY="$SSHDIR/id_ed25519"
KH="$SSHDIR/known_hosts"

APP="/opt/botmarket-github-control"
CONF="/etc/botmarket-github-control"
ENVF="$CONF/env"
UNIT="/etc/systemd/system/botmarket-github-control.service"

PY="${BM_GH_PYTHON:-/opt/botmarket-research/venv/bin/python}"
HOST="127.0.0.1"
PORT="${BM_GH_PORT:-8768}"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/botmarket-github-control-backups/$TS"

log(){ printf '\n[%s] %s\n' "$1" "$2"; }
die(){ echo "[FAIL] $*" >&2; exit 1; }

log STEP "Preflight"
for c in git ssh ssh-keygen ssh-keyscan systemctl runuser curl ss; do
  command -v "$c" >/dev/null || die "$c missing"
done
[[ -x "$PY" ]] || die "Python missing: $PY"

if ss -ltnH | awk '{print $4}' | grep -Eq "(^|:)${PORT}$"   && ! systemctl is-active --quiet botmarket-github-control.service 2>/dev/null; then
  die "Port $PORT is occupied"
fi

"$PY" - <<'PY'
try:
    from mcp.server.mcpserver import MCPServer
except Exception:
    from mcp.server.fastmcp import FastMCP as MCPServer
print("MCP_SDK_IMPORT=PASS")
PY

log STEP "Create isolated account/directories"
getent group "$GROUP_NAME" >/dev/null || groupadd --system "$GROUP_NAME"
id "$USER_NAME" >/dev/null 2>&1 ||   useradd --system --gid "$GROUP_NAME" --home-dir "$STATE" --create-home --shell /usr/sbin/nologin "$USER_NAME"

install -d -m0755 -o root -g root "$APP" "$CONF"
install -d -m0750 -o "$USER_NAME" -g "$GROUP_NAME" "$STATE"
install -d -m0700 -o "$USER_NAME" -g "$GROUP_NAME" "$SSHDIR"
install -d -m0700 -o root -g root "$BACKUP"

for f in "$APP/server.py" "$ENVF" "$UNIT"; do
  [[ -f "$f" ]] && cp -a "$f" "$BACKUP/$(basename "$f").bak"
done

log STEP "Known hosts + dedicated deploy key"
: > "$KH"
for f in /home/botmarket/.ssh/known_hosts /root/.ssh/known_hosts; do
  [[ -r "$f" ]] && grep -E 'github\.com' "$f" >> "$KH" 2>/dev/null || true
done
[[ -s "$KH" ]] || ssh-keyscan -T10 -H github.com >> "$KH" 2>/dev/null || true
[[ -s "$KH" ]] || die "Cannot obtain GitHub host key"
sort -u "$KH" -o "$KH"
chown "$USER_NAME:$GROUP_NAME" "$KH"
chmod 0644 "$KH"

[[ -f "$KEY" ]] ||   ssh-keygen -q -t ed25519 -N '' -C "botmarket-github-control@$(hostname)" -f "$KEY"
chown "$USER_NAME:$GROUP_NAME" "$KEY" "$KEY.pub"
chmod 0600 "$KEY"
chmod 0644 "$KEY.pub"

SSH="ssh -i $KEY -o IdentitiesOnly=yes -o UserKnownHostsFile=$KH -o StrictHostKeyChecking=yes -o BatchMode=yes"

set +e
READ="$(GIT_SSH_COMMAND="$SSH" git ls-remote "$URL" "refs/heads/$BRANCH" 2>&1)"
RC=$?
set -e

if [[ $RC -ne 0 ]]; then
  echo
  echo "GITHUB_DEPLOY_KEY_NOT_AUTHORIZED_YET"
  echo "Repository: $REPO"
  echo "GitHub -> Settings -> Deploy keys -> Add deploy key"
  echo "Title: BotMarketplace GitHub Control MCP"
  echo "IMPORTANT: enable Allow write access"
  echo
  cat "$KEY.pub"
  echo
  echo "After authorizing this public key, rerun this same script."
  exit 0
fi

SHA="$(awk 'NF>=2{print $1;exit}' <<<"$READ")"
[[ "$SHA" =~ ^[0-9a-f]{40,64}$ ]] || die "Cannot parse remote branch SHA"
echo "GITHUB_READ=PASS"

log STEP "Create/refresh dedicated clean clone"
if [[ -d "$REPODIR/.git" ]]; then
  R="$(runuser -u "$USER_NAME" -- git -C "$REPODIR" remote get-url origin)"
  [[ "$R" == "$URL" ]] || die "Unexpected origin: $R"
  [[ -z "$(runuser -u "$USER_NAME" -- git -C "$REPODIR" status --porcelain=v1)" ]]     || die "Control clone is dirty"
  runuser -u "$USER_NAME" -- env GIT_SSH_COMMAND="$SSH" git -C "$REPODIR" fetch --prune origin "$BRANCH"
  runuser -u "$USER_NAME" -- git -C "$REPODIR" checkout "$BRANCH"
  runuser -u "$USER_NAME" -- git -C "$REPODIR" merge --ff-only "origin/$BRANCH"
else
  rm -rf "$REPODIR"
  runuser -u "$USER_NAME" -- env GIT_SSH_COMMAND="$SSH"     git clone --branch "$BRANCH" --single-branch "$URL" "$REPODIR"
fi

runuser -u "$USER_NAME" -- git -C "$REPODIR" config user.name "BotMarketplace GitHub Control"
runuser -u "$USER_NAME" -- git -C "$REPODIR" config user.email "botmarket-github-control@users.noreply.github.com"
runuser -u "$USER_NAME" -- git -C "$REPODIR" config pull.ff only

HEAD="$(runuser -u "$USER_NAME" -- git -C "$REPODIR" rev-parse HEAD)"
[[ "$HEAD" == "$SHA" ]] || die "Clone HEAD != origin/$BRANCH"
echo "CONTROL_REPO_HEAD=$HEAD"

log STEP "Verify write permission without changing GitHub"
set +e
OUT="$(runuser -u "$USER_NAME" -- env GIT_SSH_COMMAND="$SSH"   git -C "$REPODIR" push --dry-run origin 'HEAD:refs/heads/__botmarket_mcp_write_probe__' 2>&1)"
RC=$?
set -e
if [[ $RC -ne 0 ]]; then
  echo "GITHUB_WRITE=FAIL"
  echo "Enable Allow write access for this deploy key:"
  cat "$KEY.pub"
  exit 1
fi
echo "GITHUB_WRITE_DRY_RUN=PASS"

log STEP "Install GitHub Control MCP"
cat > "$APP/server.py" <<'PY'
from __future__ import annotations
import hashlib, os, re, subprocess, tempfile
from pathlib import Path
from typing import Any

try:
    from mcp.server.mcpserver import MCPServer
except Exception:
    from mcp.server.fastmcp import FastMCP as MCPServer

NAME='BotMarketplace GitHub Control'
ROOT=Path(os.environ['BM_GH_REPO_DIR']).resolve()
URL=os.environ['BM_GH_REPO_URL']
BRANCH=os.getenv('BM_GH_BRANCH','main')
KEY=Path(os.environ['BM_GH_SSH_KEY'])
KH=Path(os.environ['BM_GH_KNOWN_HOSTS'])
HOST=os.getenv('BM_GH_HOST','127.0.0.1')
PORT=int(os.getenv('BM_GH_PORT','8768'))
MAX=int(os.getenv('BM_GH_MAX_TEXT_BYTES','262144'))

mcp=MCPServer(NAME)

DENY_PREFIX=('.git/','.github/workflows/')
DENY_NAMES={'.env','id_rsa','id_ed25519','authorized_keys','.npmrc','.pypirc'}
DENY_SUFFIX=('.pem','.key','.p12','.pfx')
SECRET=[
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\bghp_[A-Za-z0-9]{20,}\b'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{20,}\b'),
]

def sshcmd():
    return f'ssh -i {KEY} -o IdentitiesOnly=yes -o UserKnownHostsFile={KH} -o StrictHostKeyChecking=yes -o BatchMode=yes'

def git(args, check=True):
    e=os.environ.copy()
    e['GIT_SSH_COMMAND']=sshcmd()
    p=subprocess.run(
        ['git','-C',str(ROOT),*args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=e,
        timeout=120,
    )
    if check and p.returncode:
        raise ValueError(f'GIT_FAILED rc={p.returncode} stderr={p.stderr.strip()[:1600]}')
    return p

def head():
    return git(['rev-parse','HEAD']).stdout.strip()

def branch():
    return git(['branch','--show-current']).stdout.strip()

def status():
    return git(['status','--porcelain=v1','--untracked-files=all']).stdout

def sha(b:bytes):
    return hashlib.sha256(b).hexdigest()

def resolve(path, root_ok=False):
    if not isinstance(path,str) or '\x00' in path or Path(path).is_absolute():
        raise ValueError('INVALID_PATH')
    p=(ROOT/(path.strip() or '.')).resolve(strict=False)
    try:
        rel=p.relative_to(ROOT).as_posix()
    except ValueError as e:
        raise ValueError('PATH_ESCAPE') from e
    if rel=='.' and not root_ok:
        raise ValueError('ROOT_NOT_FILE')
    if '.git' in Path(rel).parts:
        raise ValueError('GIT_INTERNAL_FORBIDDEN')
    return p,rel

def write_ok(rel, content=None):
    n=rel.lstrip('./')
    base=Path(n).name
    if any(n==x.rstrip('/') or n.startswith(x) for x in DENY_PREFIX):
        raise ValueError(f'WRITE_FORBIDDEN:{rel}')
    if base in DENY_NAMES or base.endswith(DENY_SUFFIX) or (
        base.startswith('.env') and base not in {'.env.example','.env.sample'}
    ):
        raise ValueError(f'SECRET_PATH_FORBIDDEN:{rel}')
    if content is not None:
        for rx in SECRET:
            if rx.search(content):
                raise ValueError('SECRET_LIKE_CONTENT_FORBIDDEN')

def changed():
    s=set()
    for a in (
        ['diff','--name-only'],
        ['diff','--cached','--name-only'],
        ['ls-files','--others','--exclude-standard'],
    ):
        s.update(x.strip() for x in git(a).stdout.splitlines() if x.strip())
    return sorted(s)

@mcp.tool()
def get_github_control_info()->dict[str,Any]:
    return {
        'name':NAME,
        'repo_url':URL,
        'branch':branch(),
        'head':head(),
        'worktree_clean':not bool(status()),
        'force_push':False,
        'arbitrary_shell':False,
        'workflow_write':False,
    }

@mcp.tool()
def get_repo_status()->dict[str,Any]:
    return {
        'branch':branch(),
        'head':head(),
        'porcelain':status(),
        'changed_paths':changed(),
    }

@mcp.tool()
def refresh_repo()->dict[str,Any]:
    if status():
        raise ValueError('WORKTREE_DIRTY')
    if branch()!=BRANCH:
        raise ValueError('UNEXPECTED_BRANCH')
    before=head()
    git(['fetch','--prune','origin',BRANCH])
    git(['merge','--ff-only',f'origin/{BRANCH}'])
    return {'before':before,'after':head()}

@mcp.tool()
def list_files(path:str='.', recursive:bool=False, limit:int=200)->dict[str,Any]:
    p,rel=resolve(path,True)
    limit=max(1,min(int(limit),1000))
    out=[]
    if not p.exists():
        raise ValueError('PATH_NOT_FOUND')
    it=[p] if p.is_file() else (p.rglob('*') if recursive else p.iterdir())
    for x in it:
        if '.git' in x.parts:
            continue
        try:
            rp=x.resolve(strict=False).relative_to(ROOT).as_posix()
        except ValueError:
            continue
        out.append({
            'path':rp,
            'kind':'dir' if x.is_dir() else 'file',
            'size_bytes':None if x.is_dir() else x.stat().st_size,
        })
        if len(out)>=limit:
            break
    return {'path':rel,'entries':sorted(out,key=lambda z:z['path']),'truncated':len(out)>=limit}

@mcp.tool()
def read_text(path:str, offset_bytes:int=0, max_bytes:int=65536)->dict[str,Any]:
    p,rel=resolve(path)
    max_bytes=max(1,min(int(max_bytes),MAX))
    off=max(0,int(offset_bytes))
    if not p.is_file():
        raise ValueError('FILE_NOT_FOUND')
    data=p.read_bytes()
    chunk=data[off:off+max_bytes]
    while chunk:
        try:
            text=chunk.decode('utf-8')
            break
        except UnicodeDecodeError as e:
            if e.start>=len(chunk)-4:
                chunk=chunk[:-1]
                continue
            raise ValueError('NOT_UTF8_TEXT') from e
    else:
        text=''
    nxt=off+len(chunk)
    nxt=None if nxt>=len(data) else nxt
    return {
        'path':rel,
        'size_bytes':len(data),
        'sha256':sha(data),
        'offset_bytes':off,
        'text':text,
        'next_offset_bytes':nxt,
    }

@mcp.tool()
def show_diff(max_bytes:int=131072)->dict[str,Any]:
    n=max(1,min(int(max_bytes),524288))
    t='# UNSTAGED\n'+git(['diff','--no-color']).stdout+'\n# STAGED\n'+git(['diff','--cached','--no-color']).stdout
    b=t.encode()
    return {'text':b[:n].decode(errors='replace'),'truncated':len(b)>n,'changed_paths':changed()}

@mcp.tool()
def write_text_file(path:str, content:str, expected_head:str, expected_sha256:str)->dict[str,Any]:
    if branch()!=BRANCH or head()!=expected_head:
        raise ValueError(f'HEAD_MISMATCH actual={head()}')
    data=content.encode()
    if len(data)>MAX:
        raise ValueError('CONTENT_TOO_LARGE')
    p,rel=resolve(path)
    write_ok(rel,content)
    old=None
    if p.exists():
        if not p.is_file():
            raise ValueError('TARGET_NOT_FILE')
        old=sha(p.read_bytes())
        if expected_sha256=='ABSENT':
            raise ValueError('FILE_EXISTS')
        if expected_sha256!=old:
            raise ValueError(f'FILE_SHA_MISMATCH actual={old}')
    elif expected_sha256!='ABSENT':
        raise ValueError('FILE_ABSENT')
    p.parent.mkdir(parents=True,exist_ok=True)
    parent=p.parent.resolve(strict=True)
    try:
        parent.relative_to(ROOT)
    except ValueError as e:
        raise ValueError('PARENT_ESCAPE') from e
    fd,tmp=tempfile.mkstemp(prefix='.bmgh.',dir=str(parent))
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return {
        'path':rel,
        'previous_sha256':old,
        'sha256':sha(data),
        'head':expected_head,
        'committed':False,
        'pushed':False,
    }

@mcp.tool()
def commit_and_push(message:str, expected_head:str)->dict[str,Any]:
    msg=message.strip()
    pre=head()
    if not 3<=len(msg)<=200:
        raise ValueError('BAD_COMMIT_MESSAGE')
    if branch()!=BRANCH or pre!=expected_head:
        raise ValueError(f'HEAD_MISMATCH actual={pre}')
    paths=changed()
    if not paths:
        raise ValueError('NO_CHANGES')
    for x in paths:
        write_ok(x)
    git(['fetch','--prune','origin',BRANCH])
    origin=git(['rev-parse',f'origin/{BRANCH}']).stdout.strip()
    if origin!=pre:
        raise ValueError(f'REMOTE_MOVED origin={origin}')
    git(['add','--',*paths])
    git(['commit','-m',msg])
    new=head()
    p=git(['push','origin',f'HEAD:refs/heads/{BRANCH}'],False)
    if p.returncode:
        git(['reset','--soft',pre])
        raise ValueError(f'PUSH_FAILED_CHANGES_PRESERVED:{p.stderr.strip()[:1200]}')
    return {
        'previous_head':pre,
        'commit':new,
        'branch':BRANCH,
        'paths':paths,
        'pushed':True,
    }

if __name__=='__main__':
    try:
        mcp.run(
            transport='streamable-http',
            host=HOST,
            port=PORT,
            streamable_http_path='/mcp',
            stateless_http=True,
            json_response=True,
        )
    except TypeError:
        mcp.run(
            transport='streamable-http',
            host=HOST,
            port=PORT,
            streamable_http_path='/mcp',
        )
PY

chmod 0755 "$APP/server.py"
chown root:root "$APP/server.py"
"$PY" -m py_compile "$APP/server.py"
echo "SERVER_PY_COMPILE=PASS"

cat > "$ENVF" <<EOF
BM_GH_REPO_DIR=$REPODIR
BM_GH_REPO_URL=$URL
BM_GH_BRANCH=$BRANCH
BM_GH_SSH_KEY=$KEY
BM_GH_KNOWN_HOSTS=$KH
BM_GH_HOST=$HOST
BM_GH_PORT=$PORT
BM_GH_MAX_TEXT_BYTES=262144
EOF

chmod 0640 "$ENVF"
chown root:"$GROUP_NAME" "$ENVF"

cat > "$UNIT" <<EOF
[Unit]
Description=BotMarketplace GitHub Control MCP
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
Group=$GROUP_NAME
WorkingDirectory=$STATE
EnvironmentFile=$ENVF
ExecStart=$PY $APP/server.py
Restart=on-failure
RestartSec=3
TimeoutStopSec=20
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
ReadWritePaths=$STATE

[Install]
WantedBy=multi-user.target
EOF

chmod 0644 "$UNIT"
systemctl daemon-reload
systemctl enable --now botmarket-github-control.service

sleep 2

systemctl is-active --quiet botmarket-github-control.service || {
  systemctl --no-pager --full status botmarket-github-control.service || true
  journalctl -u botmarket-github-control.service -n80 --no-pager || true
  die "Service failed"
}

ss -ltnH | awk '{print $4}' | grep -Eq "127\.0\.0\.1:${PORT}$|\[::1\]:${PORT}$"   || die "Port $PORT not listening"

set +e
PROBE_OUT="$(mktemp)"
HTTP_CODE="$(curl -sS -N --max-time 2 -o "$PROBE_OUT" -w '%{http_code}'   -H 'Accept: application/json, text/event-stream' "http://$HOST:$PORT/mcp" 2>/dev/null)"
CURL_RC=$?
set -e
rm -f "$PROBE_OUT"

if [[ "$HTTP_CODE" != "200" && $CURL_RC -ne 0 ]]; then
  die "Local MCP probe failed: HTTP=$HTTP_CODE curl_rc=$CURL_RC"
fi

echo
echo "=== BOTMARKETPLACE GITHUB CONTROL MCP INSTALLED ==="
echo "GitHub read: PASS"
echo "GitHub write dry-run: PASS"
echo "Local MCP: http://$HOST:$PORT/mcp"
echo "Research Runner: NOT MODIFIED"
echo "Backup: $BACKUP"
