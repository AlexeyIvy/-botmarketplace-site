#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
OUT_DIR="/home/botmarket/sc001_data/SC001_B15P2_ANNOUNCEMENT_SEMANTIC_AUDIT"

SMOKE="$OUT_DIR/sc001_b15p2_announcement_body_hydration_smoke_v0_1_5.json"
RESULT="$OUT_DIR/sc001_b15p2_announcement_body_semantic_audit_v0_1_5.json"
LOG="$OUT_DIR/networked_semantic_audit_v0_4.log"
MARKER="$OUT_DIR/networked_semantic_audit_v0_4.launch.json"
EXIT_FILE="$OUT_DIR/networked_semantic_audit_v0_4.exit_code"

INBOX_DIR="$REPO/docs/research/runtime-inbox"
SMOKE_DST="$INBOX_DIR/sc001-b15p2-hydration-smoke-v0.1.5-latest.json"
RESULT_DST="$INBOX_DIR/sc001-b15p2-semantic-audit-v0.1.5-latest.json"
LOG_DST="$INBOX_DIR/sc001-b15p2-semantic-audit-v0.1.5-latest.log"
MARKER_DST="$INBOX_DIR/sc001-b15p2-semantic-audit-v0.1.5-latest.marker.json"
EXIT_DST="$INBOX_DIR/sc001-b15p2-semantic-audit-v0.1.5-latest.exit_code"
META_DST="$INBOX_DIR/sc001-b15p2-semantic-runtime-v0.1.5-latest.meta.json"

die() {
  echo "B15P2_SEMANTIC_RUNTIME_SNAPSHOT_REVIEW"
  echo "reason=$1"
  exit 2
}

[[ "${EUID:-$(id -u)}" -eq 0 ]] || die "must_run_as_root"

for cmd in sha256sum install python3 stat mv date dirname; do
  command -v "$cmd" >/dev/null 2>&1 || die "missing_tool:$cmd"
done

install -d -m 0750 -o botmarket-github -g botmarket-github "$INBOX_DIR"

copy_fixed() {
  local src="$1" dst="$2" max_bytes="$3"
  [[ -f "$src" && ! -L "$src" ]] || return 1
  local size sha tmp copied
  size="$(stat -c '%s' "$src")"
  [[ "$size" -gt 0 && "$size" -le "$max_bytes" ]] || die "size_rejected:$src:$size"
  sha="$(sha256sum "$src" | awk '{print $1}')"
  tmp="$dst.tmp"
  install -m 0640 -o botmarket-github -g botmarket-github "$src" "$tmp"
  copied="$(sha256sum "$tmp" | awk '{print $1}')"
  [[ "$copied" == "$sha" ]] || die "copy_sha_mismatch:$src"
  mv "$tmp" "$dst"
  printf '%s' "$sha"
}

validate_smoke() {
  python3 - "$SMOKE" <<'PY'
import json,sys
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert o.get("schema")=="sc001.b15p2_announcement_body_hydration_smoke.v0.1.5"
assert o.get("status") in {
    "B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_PASS",
    "B15P2_ANNOUNCEMENT_BODY_HYDRATION_SMOKE_V015_REVIEW",
}
assert o.get("article_body_text_persisted") is False
assert o.get("semantic_classification_performed") is False
for k in ("price_accessed","external_reference_price_accessed","index_value_accessed","basis_accessed","returns_accessed","pnl_accessed"):
    assert o.get(k) is False,(k,o.get(k))
PY
}

validate_result() {
  python3 - "$RESULT" <<'PY'
import json,sys
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert o.get("schema")=="sc001.b15p2_announcement_body_semantic_audit_result.v0.1"
assert o.get("status") in {
    "B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_PASS",
    "B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_REVIEW",
}
fw=o.get("firewalls") or {}
for k,v in fw.items():
    if k.endswith(("accessed","calculated")) or k=="event_ranked_by_outcome":
        assert v is False,(k,v)
ex=o.get("body_extraction")
if ex is not None:
    assert ex.get("source")=="__NEXT_DATA__"
    assert ex.get("primary_body_path")=="$.props.pageProps.articleDetail.content.json.children"
    assert ex.get("secondary_consistency_path")=="$.props.pageProps.articleDetail.entry.entryKey.children"
    assert ex.get("adaptive_fallback_paths") is False
PY
}

validate_marker() {
  python3 - "$MARKER" <<'PY'
import json,sys,re
from pathlib import Path
o=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert o.get("schema")=="sc001.b15p2_semantic_audit_launch_marker.v0.4"
unit=o.get("unit") or ""
assert re.fullmatch(r"sc001-b15p2-semantic-audit-v04-\d{8}T\d{6}Z",unit),unit
assert o.get("body_source")=="NEXT_DATA_HYDRATION"
assert o.get("hydration_smoke_status")=="PASS"
for k in ("price_access_authorized","external_reference_price_access_authorized","index_value_access_authorized","basis_access_authorized","returns_access_authorized","pnl_authorized"):
    assert o.get(k) is False,(k,o.get(k))
PY
}

smoke_sha=""
result_sha=""
log_sha=""
marker_sha=""
exit_sha=""

if [[ -f "$SMOKE" ]]; then
  validate_smoke || die "smoke_validation_failed"
  smoke_sha="$(copy_fixed "$SMOKE" "$SMOKE_DST" 524288)"
fi

if [[ -f "$RESULT" ]]; then
  validate_result || die "result_validation_failed"
  result_sha="$(copy_fixed "$RESULT" "$RESULT_DST" 2097152)"
fi

if [[ -f "$LOG" ]]; then
  log_sha="$(copy_fixed "$LOG" "$LOG_DST" 2097152)"
fi

if [[ -f "$MARKER" ]]; then
  validate_marker || die "marker_validation_failed"
  marker_sha="$(copy_fixed "$MARKER" "$MARKER_DST" 65536)"
fi

if [[ -f "$EXIT_FILE" ]]; then
  exit_sha="$(copy_fixed "$EXIT_FILE" "$EXIT_DST" 4096)"
fi

meta_tmp="$META_DST.tmp"
python3 -   "$smoke_sha" "$result_sha" "$log_sha" "$marker_sha" "$exit_sha"   "$SMOKE_DST" "$RESULT_DST" "$LOG_DST" "$MARKER_DST" "$EXIT_DST" > "$meta_tmp" <<'PY'
import json,sys,datetime
smoke_sha,result_sha,log_sha,marker_sha,exit_sha=sys.argv[1:6]
paths=sys.argv[6:11]
print(json.dumps({
  "schema":"sc001.b15p2_semantic_runtime_snapshot.v0.1",
  "published_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "artifacts":{
    "smoke":{"present":bool(smoke_sha),"sha256":smoke_sha or None,"path":paths[0] if smoke_sha else None},
    "result":{"present":bool(result_sha),"sha256":result_sha or None,"path":paths[1] if result_sha else None},
    "log":{"present":bool(log_sha),"sha256":log_sha or None,"path":paths[2] if log_sha else None},
    "marker":{"present":bool(marker_sha),"sha256":marker_sha or None,"path":paths[3] if marker_sha else None},
    "exit_code":{"present":bool(exit_sha),"sha256":exit_sha or None,"path":paths[4] if exit_sha else None},
  },
  "content_mutated":False,
},indent=2,sort_keys=True))
PY
chown botmarket-github:botmarket-github "$meta_tmp"
chmod 0640 "$meta_tmp"
mv "$meta_tmp" "$META_DST"

echo "B15P2_SEMANTIC_RUNTIME_SNAPSHOT_PUBLISHED"
echo "smoke_present=$([[ -n "$smoke_sha" ]] && echo True || echo False)"
echo "result_present=$([[ -n "$result_sha" ]] && echo True || echo False)"
echo "log_present=$([[ -n "$log_sha" ]] && echo True || echo False)"
echo "marker_present=$([[ -n "$marker_sha" ]] && echo True || echo False)"
echo "exit_code_present=$([[ -n "$exit_sha" ]] && echo True || echo False)"
echo "meta=docs/research/runtime-inbox/sc001-b15p2-semantic-runtime-v0.1.5-latest.meta.json"
