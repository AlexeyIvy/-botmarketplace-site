#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# BotMarketplace SC001/B15-P1 v0.2.2 artifact-complete checkpoint.
# Creates a non-secret portable host checkpoint and immediately performs
# a structural restore verification in a temporary directory.

FREEZE_COMMIT="f0b069efdd382d6f35d9a2b3e9668f35b8a48235"
ORIGINAL_FREEZE_COMMIT="7fdaf8c8e3053e2bbf266ec7d89c3abc90c3661f"
FREEZE_RECORD_REL="docs/research/sc001-b15-p1-final-identity-route-v0.2.2-freeze-v1.json"
FREEZE_RECORD_SHA256="dfa7466e6133ba8adef99d64114d5651199c0f6432a14a5b76434a200b5b937b"
REPLAY_MANIFEST_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/replay/integrated_replay_manifest_v0.2.2.json"
REPLAY_MANIFEST_SHA256="ad842a5f7be42c7c4cae6ce13b91846de7e17e17cb06cf1152aa4f69538c1f7b"
FREEZE_MANIFEST_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-preflight/identity_route_v0.2.2_final_freeze_candidate_manifest.json"
FREEZE_MANIFEST_SHA256="1519940e2580fc246d745e11cb06dda564b83f6b7cb689583eb2d1c386c8fabd"

ARTIFACT_SUPPLEMENT_REL="docs/research/sc001-b15-p1-v0.2.2-final-freeze-artifact-supplement-v1.json"
ARTIFACT_SUPPLEMENT_SHA256="6241a66f93dfcbd74d2ea8c3ac164c746f87236d653895b8cbf01ce348913997"
ARTIFACT_MANIFEST_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/final_freeze_artifact_manifest.v0.2.2.json"
ARTIFACT_MANIFEST_SHA256="a1a813244dc8cd81c2002e54650b8202c318ee9589f443301a9e624c46bb7b79"
ROUTE_SHARD_INDEX_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/directed_route_graph.v0.2.2.shard-index.json"
ROUTE_SHARD_INDEX_SHA256="001c89a7d4e973ed33ab072ec43746f6f7b6c0105912a24ae0483955ac93a50a"
ROUTE_SHARD_DIR_REL="docs/research/artifacts/b15-p1-v0.2.2/20260920T210446Z/final-freeze-materialized/route-graph-shards"
ROUTE_GRAPH_SHA256="06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928"

REPO="${BM_REPO_DIR:-/var/lib/botmarket-github-control/repo}"
BACKUP_ROOT="${BM_CHECKPOINT_DIR:-/var/backups/botmarketplace}"
RUNNER_STATE="${BM_RUNNER_STATE_DIR:-/var/lib/botmarket-runner}"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
NAME="botmarketplace-sc001-b15-v022-artifact-complete-checkpoint-${RUN_ID}"
WORK="${BACKUP_ROOT}/.${NAME}.staging"
ARCHIVE="${BACKUP_ROOT}/${NAME}.tar.gz"
ARCHIVE_SHA="${ARCHIVE}.sha256"
VERIFY_DIR=""

die() { echo "ERROR: $*" >&2; exit 1; }
note() { printf '%s\n' "$*"; }

# GitHub Control owns this dedicated clone under a service account. The
# checkpoint itself must run as root to read host state, so scope Git's
# safe.directory exception to this repository and this process only.
git_repo() {
  git -c "safe.directory=$REPO" -C "$REPO" "$@"
}

cleanup() {
  rc=$?
  [[ -n "${VERIFY_DIR:-}" && -d "$VERIFY_DIR" ]] && rm -rf -- "$VERIFY_DIR"
  [[ -d "${WORK:-}" ]] && rm -rf -- "$WORK"
  if (( rc != 0 )) && [[ -n "${ARCHIVE:-}" ]]; then
    rm -f -- "$ARCHIVE" "${ARCHIVE_SHA:-}" "${ARCHIVE}.restore-verify.txt"
  fi
  exit "$rc"
}
trap cleanup EXIT

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "Run as root (sudo)."
command -v git >/dev/null || die "git is required"
command -v tar >/dev/null || die "tar is required"
command -v sha256sum >/dev/null || die "sha256sum is required"
command -v python3 >/dev/null || die "python3 is required"
[[ -d "$REPO/.git" ]] || die "Repository clone not found: $REPO"
[[ -d "$RUNNER_STATE" ]] || die "Runner state not found: $RUNNER_STATE"

mkdir -p "$BACKUP_ROOT"
rm -rf -- "$WORK"
mkdir -p "$WORK"/{repo,runner,mcp,system,configs,manifests,verification}

git_repo rev-parse --verify "${FREEZE_COMMIT}^{commit}" >/dev/null \
  || die "Freeze commit missing from repository"
git_repo merge-base --is-ancestor "$FREEZE_COMMIT" HEAD \
  || die "Current HEAD is not a descendant of freeze commit"
[[ -z "$(git_repo status --porcelain=v1 --untracked-files=all)" ]] \
  || die "Repository worktree is not clean"

actual_freeze_sha="$(sha256sum "$REPO/$FREEZE_RECORD_REL" | awk '{print $1}')"
[[ "$actual_freeze_sha" == "$FREEZE_RECORD_SHA256" ]] \
  || die "Freeze record SHA mismatch: $actual_freeze_sha"
actual_replay_sha="$(sha256sum "$REPO/$REPLAY_MANIFEST_REL" | awk '{print $1}')"
[[ "$actual_replay_sha" == "$REPLAY_MANIFEST_SHA256" ]] \
  || die "Replay manifest SHA mismatch: $actual_replay_sha"
actual_candidate_sha="$(sha256sum "$REPO/$FREEZE_MANIFEST_REL" | awk '{print $1}')"
[[ "$actual_candidate_sha" == "$FREEZE_MANIFEST_SHA256" ]] \
  || die "Freeze candidate manifest SHA mismatch: $actual_candidate_sha"

actual_supplement_sha="$(sha256sum "$REPO/$ARTIFACT_SUPPLEMENT_REL" | awk '{print $1}')"
[[ "$actual_supplement_sha" == "$ARTIFACT_SUPPLEMENT_SHA256" ]] \
  || die "Artifact supplement SHA mismatch: $actual_supplement_sha"
actual_artifact_manifest_sha="$(sha256sum "$REPO/$ARTIFACT_MANIFEST_REL" | awk '{print $1}')"
[[ "$actual_artifact_manifest_sha" == "$ARTIFACT_MANIFEST_SHA256" ]] \
  || die "Artifact manifest SHA mismatch: $actual_artifact_manifest_sha"
actual_shard_index_sha="$(sha256sum "$REPO/$ROUTE_SHARD_INDEX_REL" | awk '{print $1}')"
[[ "$actual_shard_index_sha" == "$ROUTE_SHARD_INDEX_SHA256" ]] \
  || die "Route shard index SHA mismatch: $actual_shard_index_sha"
actual_route_graph_sha="$(
  cat \
    "$REPO/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part01.raw" \
    "$REPO/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part02.raw" \
    "$REPO/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part03.raw" \
    "$REPO/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part04.raw" \
    "$REPO/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part05.raw" \
    | sha256sum | awk '{print $1}'
)"
[[ "$actual_route_graph_sha" == "$ROUTE_GRAPH_SHA256" ]] \
  || die "Reassembled route graph SHA mismatch: $actual_route_graph_sha"

git_repo rev-parse HEAD > "$WORK/repo/HEAD.txt"
git_repo branch --show-current > "$WORK/repo/BRANCH.txt"
git_repo remote -v > "$WORK/repo/remotes.txt"
git_repo status --porcelain=v1 --untracked-files=all > "$WORK/repo/status.txt"
git_repo bundle create "$WORK/repo/repository.bundle" --all
git_repo archive --format=tar HEAD -o "$WORK/repo/repository-head.tar"

cat > "$WORK/repo/freeze-anchor.txt" <<EOF
freeze_commit=$FREEZE_COMMIT
freeze_record=$FREEZE_RECORD_REL
freeze_record_sha256=$FREEZE_RECORD_SHA256
replay_manifest=$REPLAY_MANIFEST_REL
replay_manifest_sha256=$REPLAY_MANIFEST_SHA256
freeze_candidate_manifest=$FREEZE_MANIFEST_REL
freeze_candidate_manifest_sha256=$FREEZE_MANIFEST_SHA256
artifact_supplement=$ARTIFACT_SUPPLEMENT_REL
artifact_supplement_sha256=$ARTIFACT_SUPPLEMENT_SHA256
artifact_manifest=$ARTIFACT_MANIFEST_REL
artifact_manifest_sha256=$ARTIFACT_MANIFEST_SHA256
route_shard_index=$ROUTE_SHARD_INDEX_REL
route_shard_index_sha256=$ROUTE_SHARD_INDEX_SHA256
route_graph_logical_sha256=$ROUTE_GRAPH_SHA256
original_freeze_commit=$ORIGINAL_FREEZE_COMMIT
checkpoint_source_head=$(git_repo rev-parse HEAD)
EOF

tar -C "$(dirname "$RUNNER_STATE")" -czf "$WORK/runner/botmarket-runner-state.tar.gz" \
  --exclude='*.env' \
  --exclude='*.key' \
  --exclude='*.pem' \
  --exclude='id_rsa*' \
  --exclude='id_ed25519*' \
  --exclude='*secret*' \
  --exclude='*credential*' \
  --exclude='*/ssh/*' \
  "$(basename "$RUNNER_STATE")"

mapfile -t OPT_DIRS < <(find /opt -maxdepth 1 -mindepth 1 -type d -name 'botmarket-*' -print | sort)
((${#OPT_DIRS[@]} > 0)) || die "No /opt/botmarket-* application directories found"
for d in "${OPT_DIRS[@]}"; do
  b="$(basename "$d")"
  tar -C /opt -czf "$WORK/mcp/${b}.tar.gz" \
    --exclude='.venv' --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='*.env' --exclude='*.key' --exclude='*.pem' \
    --exclude='id_rsa*' --exclude='id_ed25519*' --exclude='*secret*' \
    "$b"
done

while IFS= read -r -d '' f; do
  rel="${f#/}"
  dest="$WORK/manifests/$rel"
  mkdir -p "$(dirname "$dest")"
  cp -a -- "$f" "$dest"
done < <(find /opt -maxdepth 4 -type f \( \
  -name 'requirements*.txt' -o -name 'pyproject.toml' -o -name 'poetry.lock' \
  -o -name 'uv.lock' -o -name 'package.json' -o -name 'package-lock.json' \
  \) -path '/opt/botmarket-*/*' -print0 2>/dev/null || true)

python3 - "$WORK/system" <<'PY'
from pathlib import Path
import re, sys
out=Path(sys.argv[1])
for src in sorted(Path("/etc/systemd/system").glob("botmarket-*.service")):
    text=src.read_text(errors="replace")
    lines=[]
    for line in text.splitlines():
        if re.match(r"^\s*Environment\s*=", line):
            prefix=line.split("=",1)[0]
            line=prefix+"=<REDACTED>"
        lines.append(line)
    (out/src.name).write_text("\n".join(lines)+"\n")
PY

python3 - "$WORK/configs" <<'PY'
from pathlib import Path
import re, sys
out=Path(sys.argv[1])
roots=[Path("/etc/botmarket-research"),Path("/etc/botmarket-github-control")]
key_re=re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
for root in roots:
    if not root.exists():
        continue
    for src in sorted(p for p in root.rglob("*") if p.is_file()):
        rel=src.relative_to("/etc")
        dest=out/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        result=[]
        try:
            lines=src.read_text(errors="replace").splitlines()
        except Exception:
            dest.write_text("<UNREADABLE_OR_BINARY_REDACTED>\n")
            continue
        for line in lines:
            m=key_re.match(line.strip())
            if m:
                result.append(f"{m.group(1)}=<REDACTED>")
            elif not line.strip() or line.lstrip().startswith("#"):
                result.append(line)
            else:
                result.append("<REDACTED_NON_ENV_LINE>")
        dest.write_text("\n".join(result)+"\n")
PY

{
  echo "checkpoint_id=$NAME"
  echo "created_utc=$(date -u +%FT%TZ)"
  echo "hostname=$(hostname)"
  echo "kernel=$(uname -srmo)"
  echo "python=$(python3 --version 2>&1)"
  echo "git=$(git --version)"
} > "$WORK/system/runtime.txt"

if [[ -r /etc/os-release ]]; then cp -a /etc/os-release "$WORK/system/os-release"; fi

services=(
  botmarket-reader-mcp.service
  botmarket-runner-probe.service
  botmarket-runner.service
  botmarket-github-control.service
  botmarket-openai-tunnel.service
  botmarket-runner-tunnel.service
  botmarket-github-tunnel.service
)
: > "$WORK/system/service-state.txt"
for svc in "${services[@]}"; do
  enabled="$(systemctl is-enabled "$svc" 2>/dev/null || true)"
  active="$(systemctl is-active "$svc" 2>/dev/null || true)"
  printf '%s enabled=%s active=%s\n' "$svc" "${enabled:-unknown}" "${active:-unknown}" >> "$WORK/system/service-state.txt"
done

cat > "$WORK/SECRETS_NOT_INCLUDED.txt" <<'EOF'
This normal checkpoint intentionally excludes plaintext secrets.
Not included:
- exchange API secrets
- private SSH/deploy keys
- OpenAI runtime API keys
- plaintext .env values
- other credential/secret-like files

Secrets must be backed up separately in an encrypted secrets archive.
EOF

(
  cd "$WORK"
  find . -type f ! -name 'MANIFEST.sha256' -print0 \
    | sort -z \
    | xargs -0 sha256sum > MANIFEST.sha256
)

tar -C "$WORK" -czf "$ARCHIVE" .
sha256sum "$ARCHIVE" > "$ARCHIVE_SHA"

VERIFY_DIR="$(mktemp -d "${BACKUP_ROOT}/.${NAME}.verify.XXXXXX")"
tar -C "$VERIFY_DIR" -xzf "$ARCHIVE"
(
  cd "$VERIFY_DIR"
  sha256sum -c MANIFEST.sha256 >/dev/null
)
git bundle list-heads "$VERIFY_DIR/repo/repository.bundle" >/dev/null
mkdir -p "$VERIFY_DIR/bundle-verify-repo"
git -C "$VERIFY_DIR/bundle-verify-repo" init -q
git -C "$VERIFY_DIR/bundle-verify-repo" bundle verify "$VERIFY_DIR/repo/repository.bundle" >/dev/null
tar -tzf "$VERIFY_DIR/runner/botmarket-runner-state.tar.gz" >/dev/null

mkdir -p "$VERIFY_DIR/restored-repo"
tar -C "$VERIFY_DIR/restored-repo" -xf "$VERIFY_DIR/repo/repository-head.tar"

verify_sha="$(sha256sum "$VERIFY_DIR/restored-repo/$FREEZE_RECORD_REL" | awk '{print $1}')"
[[ "$verify_sha" == "$FREEZE_RECORD_SHA256" ]] || die "Restored freeze record SHA mismatch"
verify_replay="$(sha256sum "$VERIFY_DIR/restored-repo/$REPLAY_MANIFEST_REL" | awk '{print $1}')"
[[ "$verify_replay" == "$REPLAY_MANIFEST_SHA256" ]] || die "Restored replay manifest SHA mismatch"
verify_candidate="$(sha256sum "$VERIFY_DIR/restored-repo/$FREEZE_MANIFEST_REL" | awk '{print $1}')"
[[ "$verify_candidate" == "$FREEZE_MANIFEST_SHA256" ]] || die "Restored freeze candidate SHA mismatch"

verify_supplement="$(sha256sum "$VERIFY_DIR/restored-repo/$ARTIFACT_SUPPLEMENT_REL" | awk '{print $1}')"
[[ "$verify_supplement" == "$ARTIFACT_SUPPLEMENT_SHA256" ]] || die "Restored artifact supplement SHA mismatch"
verify_artifact_manifest="$(sha256sum "$VERIFY_DIR/restored-repo/$ARTIFACT_MANIFEST_REL" | awk '{print $1}')"
[[ "$verify_artifact_manifest" == "$ARTIFACT_MANIFEST_SHA256" ]] || die "Restored artifact manifest SHA mismatch"
verify_shard_index="$(sha256sum "$VERIFY_DIR/restored-repo/$ROUTE_SHARD_INDEX_REL" | awk '{print $1}')"
[[ "$verify_shard_index" == "$ROUTE_SHARD_INDEX_SHA256" ]] || die "Restored route shard index SHA mismatch"
verify_route_graph="$(
  cat \
    "$VERIFY_DIR/restored-repo/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part01.raw" \
    "$VERIFY_DIR/restored-repo/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part02.raw" \
    "$VERIFY_DIR/restored-repo/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part03.raw" \
    "$VERIFY_DIR/restored-repo/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part04.raw" \
    "$VERIFY_DIR/restored-repo/$ROUTE_SHARD_DIR_REL/directed_route_graph.v0.2.2.part05.raw" \
    | sha256sum | awk '{print $1}'
)"
[[ "$verify_route_graph" == "$ROUTE_GRAPH_SHA256" ]] || die "Restored reassembled route graph SHA mismatch"

cat > "${ARCHIVE}.restore-verify.txt" <<EOF
status=CHECKPOINT_BACKUP_RESTORE_VERIFY_PASS
checkpoint_id=$NAME
archive=$ARCHIVE
archive_sha256=$(sha256sum "$ARCHIVE" | awk '{print $1}')
source_head=$(git_repo rev-parse HEAD)
freeze_commit=$FREEZE_COMMIT
freeze_record_sha256=$FREEZE_RECORD_SHA256
replay_manifest_sha256=$REPLAY_MANIFEST_SHA256
freeze_candidate_manifest_sha256=$FREEZE_MANIFEST_SHA256
artifact_supplement_sha256=$ARTIFACT_SUPPLEMENT_SHA256
artifact_manifest_sha256=$ARTIFACT_MANIFEST_SHA256
route_shard_index_sha256=$ROUTE_SHARD_INDEX_SHA256
route_graph_logical_sha256=$ROUTE_GRAPH_SHA256
original_freeze_commit=$ORIGINAL_FREEZE_COMMIT
verified_utc=$(date -u +%FT%TZ)
EOF

note "CHECKPOINT_BACKUP_RESTORE_VERIFY_PASS"
note "ARCHIVE=$ARCHIVE"
note "ARCHIVE_SHA256=$(sha256sum "$ARCHIVE" | awk '{print $1}')"
note "VERIFY_RECORD=${ARCHIVE}.restore-verify.txt"
