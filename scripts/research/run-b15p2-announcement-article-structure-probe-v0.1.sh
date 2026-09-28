#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

REPO="/var/lib/botmarket-github-control/repo"
PROBE_REL="scripts/research/probe-b15p2-announcement-article-structure-v0.1.py"
PROBE="$REPO/$PROBE_REL"
EXPECTED_PROBE_SHA="73c14a0963a245ad9ee431f6e76d16deed99d698fddeb32f78ca4c1fb685fa81"

OUT_DIR="/home/botmarket/sc001_data/SC001_B15P2_ANNOUNCEMENT_STRUCTURE_PROBE"
MARKER="$OUT_DIR/article_structure_probe_v0_1.launch.json"
SELFTEST_PASS="B15P2_ANNOUNCEMENT_ARTICLE_STRUCTURE_PROBE_V01_SELF_TEST_PASS"

die() {
  echo "B15P2_ARTICLE_STRUCTURE_PROBE_HOST_REVIEW"
  echo "reason=$1"
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

  echo "B15P2_ARTICLE_STRUCTURE_PROBE_HOST_PREFLIGHT_PASS"
  echo "probe_sha256=$actual"
  echo "network_calls_performed=False"
  echo "semantic_classification_performed=False"
  echo "price/index-values/basis/returns/PnL=CLOSED"
}

latest_result() {
  find "$OUT_DIR" -maxdepth 1 -type f -name 'announcement_article_structure_probe_v0_1_*.json' \
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
    v=row.get("visible") or {}
    s=row.get("scripts") or {}
    rm=row.get("raw_markers") or {}
    print(
        row.get("symbol"),
        "pattern="+str(row.get("derived_structure_pattern")),
        "raw_bytes="+str(row.get("raw_html_bytes")),
        "visible_len="+str(v.get("visible_text_length")),
        "title_count="+str(v.get("exact_title_count")),
        "title_pos="+str(v.get("exact_title_position")),
        "pre_cut_len="+str(v.get("pre_cut_region_length")),
        "post_cut_len="+str(v.get("post_cut_region_length")),
        "terminators="+json.dumps(v.get("terminator_positions"),sort_keys=True),
        "scripts="+str(s.get("script_count")),
        "scripts_with_title="+str(s.get("scripts_with_exact_title_count")),
        "json_scripts="+str(s.get("json_script_count")),
        "jsonld="+str(s.get("jsonld_script_count")),
        "articlebody_candidates="+str(s.get("articlebody_candidate_count")),
        "json_title_candidates="+str(s.get("json_string_with_title_candidate_count")),
        "next_data="+str(rm.get("has_next_data_marker")),
        "next_f="+str(rm.get("has_next_f_marker")),
        sep=" | ",
    )
print("semantic_classification_performed =",obj.get("semantic_classification_performed"))
print("article_body_text_persisted =",obj.get("article_body_text_persisted"))
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
    journalctl -u "$unit" -n 80 --no-pager -o cat 2>/dev/null || true
  else
    echo "launch_marker=ABSENT"
  fi

  echo "--- result summary ---"
  show_result_summary
}

launch() {
  preflight

  # systemd ReadWritePaths targets must exist before namespace setup.
  install -d -m 0750 -o botmarket -g botmarket "$OUT_DIR"

  local unit
  unit="sc001-b15p2-article-structure-probe-v01-$(date -u +%Y%m%dT%H%M%SZ)"

  local marker_tmp="$MARKER.tmp"
  cat > "$marker_tmp" <<EOF
{
  "schema": "sc001.b15p2_article_structure_probe_launch_marker.v0.1",
  "unit": "$unit",
  "probe_sha256": "$EXPECTED_PROBE_SHA",
  "execution_mode": "ASYNC_SYSTEMD_TYPE_EXEC",
  "runtime_bound_seconds": 180,
  "launched_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
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
    --description="SC001 B15-P2 announcement article structure probe v0.1" \
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

  echo "B15P2_ARTICLE_STRUCTURE_PROBE_ASYNC_LAUNCHED"
  echo "unit=$unit"
  echo "termux_prompt_can_return=True"
  echo "status_command=sudo bash /var/lib/botmarket-github-control/repo/scripts/research/run-b15p2-announcement-article-structure-probe-v0.1.sh --status"
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
