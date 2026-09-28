#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
SOURCE_DIR="/home/botmarket/sc001_data/SC001_B15P2_NEXT_DATA_STRUCTURE_PROBE"
TARGET_REL="docs/research/runtime-inbox/sc001-b15p2-next-data-structure-v0.4-latest.json"
TARGET="$REPO/$TARGET_REL"
META_REL="docs/research/runtime-inbox/sc001-b15p2-next-data-structure-v0.4-latest.meta.json"
META="$REPO/$META_REL"

die() {
  echo "B15P2_V04_RESULT_PUBLISH_REVIEW"
  echo "reason=$1"
  exit 2
}

[[ "${EUID:-$(id -u)}" -eq 0 ]] || die "must_run_as_root"

for cmd in find sort head cut sha256sum install python3 dirname date stat mv; do
  command -v "$cmd" >/dev/null 2>&1 || die "missing_tool:$cmd"
done

latest="$(
  find "$SOURCE_DIR" -maxdepth 1 -type f -name 'next_data_structure_probe_v0_4_*.json'     -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-
)"
[[ -n "$latest" ]] || die "v04_result_not_found"
[[ -f "$latest" && ! -L "$latest" ]] || die "result_missing_or_symlink"

size="$(stat -c '%s' "$latest")"
[[ "$size" -gt 0 && "$size" -le 1048576 ]] || die "unexpected_result_size:$size"

python3 - "$latest" <<'PY'
import json,sys
from pathlib import Path

p=Path(sys.argv[1])
obj=json.loads(p.read_text(encoding="utf-8"))

def req(cond,code):
    if not cond:
        raise SystemExit(f"VALIDATION_FAILED:{code}")

req(obj.get("schema")=="sc001.b15p2_next_data_structure_probe.v0.4","SCHEMA")
req(obj.get("status") in {
    "B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_COMPLETE",
    "B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_REVIEW",
},"STATUS")
req(obj.get("article_body_text_persisted") is False,"ARTICLE_TEXT")
req(obj.get("semantic_classification_performed") is False,"SEMANTIC")
for k in (
    "price_accessed","external_reference_price_accessed","index_value_accessed",
    "basis_accessed","returns_accessed","pnl_accessed",
):
    req(obj.get(k) is False,k.upper())

events=obj.get("events")
req(isinstance(events,list),"EVENTS")
for row in events:
    req(row.get("symbol") in {"DOGUSDT","TONUSDT"},"SYMBOL")
    req(isinstance(row.get("hydration"),dict),"HYDRATION")

if obj.get("status")=="B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_COMPLETE":
    req(len(events)==2,"COMPLETE_EVENT_COUNT")
    req({r.get("symbol") for r in events}=={"DOGUSDT","TONUSDT"},"COMPLETE_SYMBOLS")
    req(isinstance(obj.get("consensus"),dict),"CONSENSUS")

print("B15P2_V04_RESULT_VALIDATION_PASS")
print("status =",obj.get("status"))
print("events =",len(events))
print("high_confidence =", (obj.get("consensus") or {}).get("high_confidence_candidate_count"))
PY

source_sha="$(sha256sum "$latest" | awk '{print $1}')"

install -d -m 0750 -o botmarket-github -g botmarket-github "$(dirname "$TARGET")"

tmp="$TARGET.tmp"
install -m 0640 -o botmarket-github -g botmarket-github "$latest" "$tmp"
copied_sha="$(sha256sum "$tmp" | awk '{print $1}')"
[[ "$copied_sha" == "$source_sha" ]] || die "copy_sha_mismatch"
mv "$tmp" "$TARGET"

meta_tmp="$META.tmp"
python3 - "$latest" "$source_sha" "$size" > "$meta_tmp" <<'PY'
import json,sys,datetime
from pathlib import Path
src=Path(sys.argv[1])
print(json.dumps({
    "schema":"sc001.runtime_result_publish_meta.v0.1",
    "published_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_path":str(src),
    "source_sha256":sys.argv[2],
    "source_size_bytes":int(sys.argv[3]),
    "target_relative_path":"docs/research/runtime-inbox/sc001-b15p2-next-data-structure-v0.4-latest.json",
    "content_mutated":False,
},indent=2,sort_keys=True))
PY
chown botmarket-github:botmarket-github "$meta_tmp"
chmod 0640 "$meta_tmp"
mv "$meta_tmp" "$META"

echo "B15P2_V04_RESULT_PUBLISHED_TO_GITHUB_INBOX"
echo "source=$latest"
echo "source_sha256=$source_sha"
echo "target=$TARGET_REL"
echo "meta=$META_REL"
