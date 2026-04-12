#!/usr/bin/env bash
# Remove stray TypeScript emission (*.js, *.d.ts, *.js.map, *.d.ts.map) that
# leaked into source and test trees outside the canonical dist/ output dir.
#
# Background: a rogue tsc run (wrong tsconfig, IDE misconfig, or ad-hoc
# `tsc tests/...`) can emit JS next to TS sources. Under ESM + NodeNext,
# Vitest/Node resolve `import "./foo.js"` to the stray .js file instead of
# the real .ts source, leading to silent "undefined export" failures
# (e.g. the apps/api graphCompiler MTF fixture incident).
#
# Usage:
#   scripts/clean-stray-ts-artifacts.sh                 # dry-run (default, safe)
#   scripts/clean-stray-ts-artifacts.sh --apply         # actually delete
#   scripts/clean-stray-ts-artifacts.sh --check         # exit 1 if any found (CI)
#   scripts/clean-stray-ts-artifacts.sh --aggressive    # also match *.d.ts (+ dry-run)
#   scripts/clean-stray-ts-artifacts.sh --aggressive --apply
#
# Default extensions: *.js, *.js.map, *.d.ts.map — always emission output.
# *.d.ts is NOT matched by default because hand-written ambient types
# (e.g. apps/api/src/types.d.ts — Fastify module augmentation) are legit.
# Use --aggressive to also sweep .d.ts files; REVIEW the dry-run list first.
#
# Safe by design: only targets apps/*/src, apps/*/tests, packages/*/src,
# packages/*/tests. Never touches dist/, node_modules/, or root configs.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

APPLY=0
CHECK=0
AGGRESSIVE=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --check) CHECK=1 ;;
    --aggressive) AGGRESSIVE=1 ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [[ $APPLY -eq 1 && $CHECK -eq 1 ]]; then
  echo "--apply and --check are mutually exclusive" >&2
  exit 2
fi

TARGETS=(
  "apps/*/src"
  "apps/*/tests"
  "packages/*/src"
  "packages/*/tests"
)

FIND_EXPR=( -name '*.js' -o -name '*.js.map' -o -name '*.d.ts.map' )
if [[ $AGGRESSIVE -eq 1 ]]; then
  FIND_EXPR+=( -o -name '*.d.ts' )
fi

# Collect matches across all target roots.
mapfile -t FILES < <(
  for pattern in "${TARGETS[@]}"; do
    # shellcheck disable=SC2086
    find $pattern \
      -type f \
      \( "${FIND_EXPR[@]}" \) \
      2>/dev/null || true
  done | sort -u
)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No stray TS emission found. Tree is clean."
  exit 0
fi

echo "Found ${#FILES[@]} stray artefact(s):"
printf '  %s\n' "${FILES[@]}"

if [[ $CHECK -eq 1 ]]; then
  echo ""
  echo "ERROR: stray TypeScript emission detected under source/test trees."
  echo "Run 'scripts/clean-stray-ts-artifacts.sh --apply' to remove."
  exit 1
fi

if [[ $APPLY -eq 0 ]]; then
  echo ""
  echo "Dry-run only. Re-run with --apply to delete."
  exit 0
fi

echo ""
echo "Deleting..."
for f in "${FILES[@]}"; do
  rm -f -- "$f"
done
echo "Done. Removed ${#FILES[@]} file(s)."
