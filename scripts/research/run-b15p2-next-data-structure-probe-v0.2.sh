#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
PROBE_REL="scripts/research/probe-b15p2-next-data-structure-v0.2.py"
PROBE="$REPO/$PROBE_REL"
EXPECTED_PROBE_SHA="6bd708526944c6b875757f3f5443da1f088289cdc4792952f569642d142703a6"

OUT_DIR="/home/botmarket/sc001_data/SC001_B15P2_NEXT_DATA_STRUCTURE_PROBE"
MARKER="$OUT_DIR/next_data_structure_probe_v0_2.launch.json"
SELFTEST_PASS="B15P2_NEXT_DATA_STRUCTURE_PROBE_V02_SELF_TEST_PASS"

die() {
  echo "B15P2_NEXT_DATA_STRUCTURE_PROBE_HOST_REVIEW"
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
  for cmd in sha256sum awk install python3 systemd-run systemctl journalctl date find sort head cut grep chown chmod mv; do
    command -v "$cmd" >/dev/null 2>&1 || die "required_command_missing:$cmd"
  done
}

preflight() {
  need_root
  check_tools
  [[ -f "$PROBE" ]] || die "probe_missing"
  [[ ! -L "$PROBE" ]] || die "probe_symlink_forbidden"

  local actual
  actual="$(sha256sum "$PROBE" | awk '{print $1}')"
  [[ "$actual" == "$EXPECTED_PROBE_SHA" ]] || die "probe_sha_mismatch"

  local selftest_out
  if selftest_out="$(/usr/bin/python3 "$PROBE" --mode self-test 2>&1)"; then
    :
  else
    printf '%s\n' "$selftest_out"
    die "probe_selftest_failed"
  fi
  printf '%s\n' "$selftest_out"
  printf '%s\n' "$selftest_out" | grep -qx "$SELFTEST_PASS" || die "probe_selftest_pass_token_missing"

  echo "B15P2_NEXT_DATA_STRUCTURE_PROBE_HOST_PREFLIGHT_PASS"
  echo "probe_sha256=$actual"
  echo "network_calls_performed=False"
  echo "article_body_text_persisted=False"
  echo "semantic_classification_performed=False"
  echo "price/index-values/basis/returns/PnL=CLOSED"
}

latest_result() {
  find "$OUT_DIR" -maxdepth 1 -type f -name 'next_data_structure_probe_v0_2_*.json' \
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
    nd=row.get("next_data") or {}
    print(
        row.get("symbol"),
        "title_nodes="+str(nd.get("exact_title_node_count")),
        "candidates="+str(nd.get("structural_string_candidate_count")),
        "pageprops_keys="+json.dumps(nd.get("pageprops_keys"),sort_keys=True),
        sep=" | ",
    )
    for node in (nd.get("exact_title_nodes") or [])[:3]:
        parent=node.get("parent") or {}
        fields=[]
        for f in (parent.get("fields") or []):
            fields.append({
                "key":f.get("key"),
                "type":f.get("type"),
                "length":f.get("length"),
                "html_tag_count":f.get("html_tag_count"),
                "contains_exact_title":f.get("contains_exact_title"),
            })
        print(
            "TITLE_PARENT",
            row.get("symbol"),
            "path="+str(parent.get("parent_path")),
            "fields="+json.dumps(fields,sort_keys=True),
        )
    for cand in (nd.get("structural_string_candidates") or [])[:10]:
        print(
            "CANDIDATE",
            row.get("symbol"),
            "path="+str(cand.get("path")),
            "score="+str(cand.get("score")),
            "length="+str(cand.get("length")),
            "html_tags="+str(cand.get("html_tag_count")),
            "escaped_html="+str(cand.get("escaped_html_marker_count")),
            "contains_title="+str(cand.get("contains_exact_title")),
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
  preflight

  install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"

  local unit
  unit="sc001-b15p2-next-data-structure-probe-v02-$(date -u +%Y%m%dT%H%M%SZ)"

  local marker_tmp="$MARKER.tmp"
  cat > "$marker_tmp" <<EOF
{
  "schema": "sc001.b15p2_next_data_structure_probe_launch_marker.v0.2",
  "unit": "$unit",
  "probe_sha256": "$EXPECTED_PROBE_SHA",
  "execution_mode": "ASYNC_SYSTEMD_TYPE_EXEC",
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

  set +e
  systemd-run \
    --no-block \
    --unit="$unit" \
    --description="SC001 B15-P2 Next.js hydration structure probe v0.2" \
    --property=Type=exec \
    --property=TimeoutStartSec=30 \
    --property=RuntimeMaxSec=180 \
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
    /usr/bin/python3 "$PROBE" --mode live
  local rc="$?"
  set -e

  if [[ "$rc" -ne 0 ]]; then
    status || true
    die "systemd_launch_failed"
  fi

  echo "B15P2_NEXT_DATA_STRUCTURE_PROBE_V02_ASYNC_LAUNCHED"
  echo "unit=$unit"
  echo "termux_prompt_can_return=True"
  echo "status_command=sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p2-next-data-structure-probe-v0.2.sh --status"
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
