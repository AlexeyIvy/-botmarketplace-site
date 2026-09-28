#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

: "${B15P2_STAGE:?B15P2_STAGE required}"
: "${B15P2_DATA_ROOT:?B15P2_DATA_ROOT required}"
: "${B15P2_SCRIPT:?B15P2_SCRIPT required}"
: "${B15P2_LOG:?B15P2_LOG required}"
: "${B15P2_EXIT_FILE:?B15P2_EXIT_FILE required}"

[[ -d "$B15P2_STAGE" ]] || { echo "helper_stage_missing"; exit 120; }
[[ -f "$B15P2_SCRIPT" && ! -L "$B15P2_SCRIPT" ]] || { echo "helper_script_invalid"; exit 121; }
[[ -d "$(/usr/bin/dirname "$B15P2_LOG")" ]] || { echo "helper_log_dir_missing"; exit 122; }
[[ -d "$(/usr/bin/dirname "$B15P2_EXIT_FILE")" ]] || { echo "helper_exit_dir_missing"; exit 123; }

set +e
/usr/bin/env -i   HOME=/home/botmarket   PATH=/usr/bin:/bin   B15P2_REPO_ROOT="$B15P2_STAGE"   SC001_DATA_ROOT="$B15P2_DATA_ROOT"   /usr/bin/python3 "$B15P2_SCRIPT" --mode live 2>&1 | /usr/bin/tee -a "$B15P2_LOG"
pipeline_status=("${PIPESTATUS[@]}")
set -e

python_rc="${pipeline_status[0]:-125}"
tee_rc="${pipeline_status[1]:-125}"

if [[ "$python_rc" -ne 0 ]]; then
  final_rc="$python_rc"
elif [[ "$tee_rc" -ne 0 ]]; then
  final_rc="$tee_rc"
else
  final_rc=0
fi

tmp="$B15P2_EXIT_FILE.tmp"
printf '%s\n' "$final_rc" > "$tmp"
/usr/bin/mv "$tmp" "$B15P2_EXIT_FILE"

echo "B15P2_SEMANTIC_LIVE_HELPER_EXIT"
echo "python_rc=$python_rc"
echo "tee_rc=$tee_rc"
echo "final_rc=$final_rc"
exit "$final_rc"
