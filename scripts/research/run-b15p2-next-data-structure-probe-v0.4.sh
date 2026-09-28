#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
PROBE_REL="scripts/research/probe-b15p2-next-data-structure-v0.4.py"
PROBE="$REPO/$PROBE_REL"
EXPECTED_PROBE_SHA="5517ec5304e44e1ea5ebbaef043223a1f09067256da10d20ddf9837d7513181f"

SOURCE_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json"
FREEZE_REL="docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json"
EXPECTED_SOURCE_SHA="c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c"
EXPECTED_FREEZE_SHA="81952c83e7397481035cc00354388dfe3470ad17993c6e80665a7d376be907ed"

STAGE="/home/botmarket/.local/share/botmarket/b15p2-next-data-structure-v0.4-stage"
STAGED_PROBE="$STAGE/$PROBE_REL"

OUT_DIR="/home/botmarket/sc001_data/SC001_B15P2_NEXT_DATA_STRUCTURE_PROBE"
MARKER="$OUT_DIR/next_data_structure_probe_v0_4.launch.json"
SELFTEST_PASS="B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_SELF_TEST_PASS"

die() {
  echo "B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_HOST_REVIEW"
  echo "reason=$1"
  echo "article_body_text_persisted=False"
  echo "semantic_classification_performed=False"
  echo "price/index-values/basis/returns/PnL=CLOSED"
  exit 2
}

need_root() {
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "wrapper_must_run_as_root"
}

check_tools() {
  local cmd
  for cmd in sha256sum awk install sudo python3 systemd-run systemctl journalctl date find sort head cut grep chown chmod mv test rm dirname wc env; do
    command -v "$cmd" >/dev/null 2>&1 || die "required_command_missing:$cmd"
  done
}

preflight() {
  need_root
  check_tools

  [[ -f "$PROBE" && ! -L "$PROBE" ]] || die "probe_missing_or_symlink"
  [[ -f "$REPO/$SOURCE_REL" && ! -L "$REPO/$SOURCE_REL" ]] || die "source_missing_or_symlink"
  [[ -f "$REPO/$FREEZE_REL" && ! -L "$REPO/$FREEZE_REL" ]] || die "freeze_missing_or_symlink"

  local actual source_actual freeze_actual
  actual="$(sha256sum "$PROBE" | awk '{print $1}')"
  source_actual="$(sha256sum "$REPO/$SOURCE_REL" | awk '{print $1}')"
  freeze_actual="$(sha256sum "$REPO/$FREEZE_REL" | awk '{print $1}')"

  [[ "$actual" == "$EXPECTED_PROBE_SHA" ]] || die "probe_sha_mismatch"
  [[ "$source_actual" == "$EXPECTED_SOURCE_SHA" ]] || die "source_sha_mismatch"
  [[ "$freeze_actual" == "$EXPECTED_FREEZE_SHA" ]] || die "freeze_sha_mismatch"

  rm -rf "$STAGE"
  install -d -m 0750 -o root -g botmarket "$STAGE"

  local rel src dst expected staged_actual
  for rel in "$PROBE_REL" "$SOURCE_REL" "$FREEZE_REL"; do
    case "$rel" in
      "$PROBE_REL") expected="$EXPECTED_PROBE_SHA" ;;
      "$SOURCE_REL") expected="$EXPECTED_SOURCE_SHA" ;;
      "$FREEZE_REL") expected="$EXPECTED_FREEZE_SHA" ;;
      *) die "unexpected_stage_path:$rel" ;;
    esac
    src="$REPO/$rel"
    dst="$STAGE/$rel"
    install -d -m 0750 -o root -g botmarket "$(dirname "$dst")"
    install -m 0440 -o root -g botmarket "$src" "$dst"
    staged_actual="$(sha256sum "$dst" | awk '{print $1}')"
    [[ "$staged_actual" == "$expected" ]] || die "staged_sha_mismatch:$rel"
    sudo -u botmarket -H test -r "$dst" || die "staged_not_readable_by_botmarket:$rel"
    if sudo -u botmarket -H test -w "$dst"; then
      die "staged_unexpectedly_writable_by_botmarket:$rel"
    fi
  done

  [[ -z "$(find "$STAGE" -type l -print -quit)" ]] || die "staging_symlink_detected"
  local stage_count
  stage_count="$(find "$STAGE" -type f | wc -l | awk '{print $1}')"
  [[ "$stage_count" == "3" ]] || die "unexpected_staging_file_count:$stage_count"

  local selftest_out
  if selftest_out="$(
    sudo -u botmarket -H env -i       HOME=/home/botmarket       PATH=/usr/bin:/bin       B15P2_REPO_ROOT="$STAGE"       /usr/bin/python3 "$STAGED_PROBE" --mode self-test 2>&1
  )"; then
    :
  else
    printf '%s\n' "$selftest_out"
    die "probe_selftest_failed"
  fi

  printf '%s\n' "$selftest_out"
  printf '%s\n' "$selftest_out" | grep -qx "$SELFTEST_PASS" || die "probe_selftest_pass_token_missing"

  echo "B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_HOST_PREFLIGHT_PASS"
  echo "probe_sha256=$actual"
  echo "source_sha256=$source_actual"
  echo "freeze_sha256=$freeze_actual"
  echo "staging_file_count=$stage_count"
  echo "network_calls_performed=False"
  echo "article_body_text_persisted=False"
  echo "semantic_classification_performed=False"
  echo "price/index-values/basis/returns/PnL=CLOSED"
}

latest_result() {
  find "$OUT_DIR" -maxdepth 1 -type f -name 'next_data_structure_probe_v0_4_*.json' \
    -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-
}

show_result_summary() {
  local latest
  latest="$(latest_result)"
  if [[ -z "$latest" ]]; then
    echo "result_file=ABSENT"
    return 0
  fi
  echo "result_file=$latest"
  /usr/bin/python3 - "$latest" <<'PY'
import json,sys
from pathlib import Path
obj=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("result_status =",obj.get("status"))
for row in obj.get("events") or []:
    h=row.get("hydration") or {}
    print(
        row.get("symbol"),
        "title_nodes="+str(h.get("exact_title_node_count")),
        "candidates="+str(h.get("structural_candidate_count")),
        "parseable_json_scripts="+str(h.get("parseable_json_script_count")),
        "next_data_scripts="+str(h.get("next_data_script_count")),
        "next_data_has_title="+str(h.get("next_data_contains_exact_title")),
        "title_outside_next_data="+str(h.get("title_outside_next_data")),
        sep=" | ",
    )
    for node in (h.get("exact_title_nodes") or [])[:3]:
        print(
            "TITLE_NODE",
            row.get("symbol"),
            "identity="+str(node.get("identity")),
            "script_role="+str(node.get("script_role")),
            "path="+str(node.get("path")),
            "ancestor_paths="+json.dumps([a.get("path") for a in node.get("ancestors",[])]),
        )
    for cand in (h.get("structural_candidates") or [])[:12]:
        html_tags=(cand.get("html_tag_count")
                   if cand.get("kind")=="string"
                   else cand.get("descendant_html_tag_count"))
        print(
            "CANDIDATE",
            row.get("symbol"),
            "identity="+str(cand.get("identity")),
            "script_role="+str(cand.get("script_role")),
            "path="+str(cand.get("path")),
            "kind="+str(cand.get("kind")),
            "score="+str(cand.get("score")),
            "chars="+str(cand.get("chars")),
            "html_tags="+str(html_tags),
            "fallback_large="+str(cand.get("fallback_large")),
        )

cons=obj.get("consensus") or {}
print(
    "CONSENSUS",
    "common_title_identities="+json.dumps(cons.get("common_exact_title_identities"),sort_keys=True),
    "common_candidates="+str(cons.get("common_candidate_count")),
    "high_confidence="+str(cons.get("high_confidence_candidate_count")),
)
for cand in (cons.get("high_confidence_candidates") or [])[:12]:
    print(
        "CONSENSUS_CANDIDATE",
        "identity="+str(cand.get("identity")),
        "script_role="+str(cand.get("script_role")),
        "path="+str(cand.get("path")),
        "min_score="+str(cand.get("min_score")),
        "min_chars="+str(cand.get("min_chars")),
        "path_depth="+str(cand.get("path_depth")),
        "types="+json.dumps(cand.get("types"),sort_keys=True),
        "kinds="+json.dumps(cand.get("kinds"),sort_keys=True),
    )

print("article_body_text_persisted =",obj.get("article_body_text_persisted"))
print("semantic_classification_performed =",obj.get("semantic_classification_performed"))
print("price/index-values/basis/returns/PnL=CLOSED")
PY
}

status() {
  need_root
  check_tools
  if [[ -f "$MARKER" ]]; then
    local unit
    unit="$(/usr/bin/python3 - "$MARKER" <<'PY'
import json,sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["unit"])
PY
)"
    echo "unit=$unit"
    systemctl show "$unit" \
      -p ActiveState -p SubState -p Result -p ExecMainCode -p ExecMainStatus \
      --no-pager 2>/dev/null || true
    echo "--- journal tail ---"
    journalctl -u "$unit" -n 100 --no-pager -o cat 2>/dev/null || true
  else
    echo "launch_marker=ABSENT"
  fi
  echo "--- result summary ---"
  show_result_summary
}

launch() {
  [[ ! -e "$MARKER" ]] || die "one_shot_launch_marker_exists"
  preflight

  install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"

  local unit
  unit="sc001-b15p2-next-data-structure-probe-v04-$(date -u +%Y%m%dT%H%M%SZ)"


  set +e
  systemd-run \
    --no-block \
    --unit="$unit" \
    --description="SC001 B15-P2 Next.js hydration mapper v0.4" \
    --property=Type=exec \
    --property=TimeoutStartSec=30 \
    --property=RuntimeMaxSec=180 \
    --property=User=botmarket \
    --property=Group=botmarket \
    --property=UMask=0027 \
    --property=NoNewPrivileges=yes \
    --property=PrivateTmp=yes \
    --property=PrivateDevices=yes \
    --property=ProtectSystem=strict \
    --property=ProtectKernelTunables=yes \
    --property=ProtectKernelModules=yes \
    --property=ProtectControlGroups=yes \
    --property=RestrictSUIDSGID=yes \
    --property=LockPersonality=yes \
    --property="ReadWritePaths=$OUT_DIR" \
    --property="RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6" \
    /usr/bin/env -i       HOME=/home/botmarket       PATH=/usr/bin:/bin       B15P2_REPO_ROOT="$STAGE"       /usr/bin/python3 "$STAGED_PROBE" --mode live
  local rc="$?"
  set -e

  if [[ "$rc" -ne 0 ]]; then
    status || true
    die "systemd_launch_failed"
  fi

  local marker_tmp="$MARKER.tmp"
  cat > "$marker_tmp" <<EOF
{
  "schema": "sc001.b15p2_next_data_structure_probe_launch_marker.v0.4",
  "unit": "$unit",
  "probe_sha256": "$EXPECTED_PROBE_SHA",
  "source_sha256": "$EXPECTED_SOURCE_SHA",
  "freeze_sha256": "$EXPECTED_FREEZE_SHA",
  "execution_mode": "ASYNC_SYSTEMD_TYPE_EXEC_AS_BOTMARKET_FROM_EXACT_STAGE",
  "staging_root": "$STAGE",
  "runtime_bound_seconds": 180,
  "launched_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "article_body_text_persisted": false,
  "semantic_classification_authorized": false,
  "price_access_authorized": false,
  "external_reference_price_access_authorized": false,
  "index_value_access_authorized": false,
  "basis_access_authorized": false,
  "returns_access_authorized": false,
  "pnl_access_authorized": false
}
EOF
  mv "$marker_tmp" "$MARKER"
  chown botmarket:botmarket "$MARKER"
  chmod 0640 "$MARKER"


  echo "B15P2_NEXT_DATA_STRUCTURE_PROBE_V04_ASYNC_LAUNCHED"
  echo "unit=$unit"
  echo "termux_prompt_can_return=True"
  echo "status_command=sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p2-next-data-structure-probe-v0.4.sh --status"
  echo "article_body_text_persisted=False"
  echo "semantic_classification_performed=False"
  echo "price/index-values/basis/returns/PnL=CLOSED"
}

case "${1:-}" in
  --preflight)
    preflight
    ;;
  --launch)
    launch
    ;;
  --status)
    status
    ;;
  *)
    echo "Usage:"
    echo "  sudo bash $0 --preflight"
    echo "  sudo bash $0 --launch"
    echo "  sudo bash $0 --status"
    exit 2
    ;;
esac
