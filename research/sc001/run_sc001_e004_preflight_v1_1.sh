#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${REPO_ROOT}" ]]; then
  echo "ERROR: run this from inside the BotMarketplace git repository" >&2
  exit 2
fi
cd "${REPO_ROOT}"

ENGINE="research/sc001/sc001_e004_volatility_breakout_v1.py"
CONFIG="research/sc001/sc001_e004_config_v1_0.json"
PREFLIGHT="research/sc001/sc001_e004_preflight_v1_1.py"
DATA_ROOT="${SC001_DATA_ROOT:-${HOME}/sc001_data}"
OUTDIR="${DATA_ROOT}/SC001_E004/preflight"
REPORT="${OUTDIR}/sc001_e004_preflight_report.json"

for f in "${ENGINE}" "${CONFIG}" "${PREFLIGHT}"; do
  [[ -f "${f}" ]] || { echo "ERROR: missing ${f}" >&2; exit 2; }
done

if [[ -e "${REPORT}" ]] || { [[ -d "${OUTDIR}" ]] && [[ -n "$(ls -A "${OUTDIR}" 2>/dev/null)" ]]; }; then
  echo "ERROR: preflight output already exists; refusing to overwrite: ${OUTDIR}" >&2
  exit 2
fi

mkdir -p "${DATA_ROOT}/SC001_E004"

echo "=== SC001-E004 preflight launcher ==="
echo "repo_commit=$(git rev-parse HEAD)"
echo "python=$(python3 --version 2>&1)"
echo "data_root=${DATA_ROOT}"
echo "Discovery=BLOCKED until exact PREFLIGHT_PASS"

git diff --quiet -- "${ENGINE}" "${CONFIG}" "${PREFLIGHT}" || {
  echo "ERROR: frozen E004 executable files have uncommitted changes" >&2
  exit 2
}

python3 -m py_compile "${ENGINE}" "${PREFLIGHT}"
python3 -u "${PREFLIGHT}" --config "${CONFIG}"

python3 - "${REPORT}" <<'PY'
import json, sys
from pathlib import Path
p=Path(sys.argv[1])
obj=json.loads(p.read_text(encoding="utf-8"))
print("=== SAFE PREFLIGHT SUMMARY ===")
print("status =", obj.get("status"))
t=obj.get("tests") or {}
print("tests =", f"{t.get('passed')}/{t.get('total')}")
dry=obj.get("real_data_no_alpha_dry_run") or {}
print("first_eligible_ms =", dry.get("first_eligible_ms"))
print("eligible_minute_count =", dry.get("eligible_minute_count"))
print("decision_count =", dry.get("decision_count"))
print("maximum_decisions_per_day =", dry.get("maximum_decisions_per_day"))
print("maximum_concurrent_positions =", dry.get("maximum_concurrent_positions"))
r=obj.get("resources") or {}
print("peak_rss_bytes =", r.get("peak_rss_bytes"))
print("disk_pass =", r.get("disk_pass"))
print("memory_under_6gib_pass =", r.get("memory_under_6gib_pass"))
print("alpha_calculated =", (obj.get("invariants") or {}).get("alpha_calculated"))
print("Q2/Validation/Final/L2 = CLOSED")
PY
