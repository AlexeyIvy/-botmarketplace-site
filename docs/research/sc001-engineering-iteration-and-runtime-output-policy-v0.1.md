# SC001 Engineering Iteration and Runtime Output Policy v0.1

Date: 2026-09-28
Status: **BINDING FOR CURRENT SC001 ENGINEERING WORK**

## 1. Think before iteration

A delegated engineering iteration is not permission to patch the next visible error mechanically.

Before every iteration the executor must perform a programmer-expert pre-iteration review covering:

1. the immediate root cause;
2. adjacent failure modes in the same code path;
3. input/schema assumptions;
4. permissions and ownership;
5. wrapper/systemd/runtime behavior;
6. output persistence and observability;
7. version/SHA/schema consistency;
8. likely next-step conflicts;
9. whether the implementation path itself should be simplified or abandoned.

Where several related defects can be removed coherently in one change, prefer one consolidated correction over sequential line-by-line fixes.

The delegated budget of five iterations is a **maximum failure-recovery budget**, not a target and not a substitute for analysis.

## 2. Iteration accounting

Count an iteration when a materially changed implementation is actually re-executed after a technical failure.

Do not count:
- static review;
- documentation;
- result publication;
- read-only inspection;
- a correction caught before execution.

Stop and return to the user if:
- five failed/recovery iterations are consumed; or
- the next correction would expand network/data scope, alter frozen research rules, open price/index/basis/returns/PnL, or change the hypothesis.

## 3. Runtime output rule

Large terminal output must not depend on screenshots as the primary research handoff.

Every nontrivial SC001 runtime should prefer:

- structured canonical JSON result on VPS;
- persistent log for long-running/diagnostic jobs;
- concise terminal summary;
- exact result/log paths printed at completion.

For results needed by ChatGPT after completion, use a validated **runtime inbox relay** into the dedicated GitHub-Control clone or an explicitly configured read-only VPS Reader root.

The user should normally need to provide at most:
- a short “completed” message; or
- one final screenshot containing the completion token/path.

The full result should then be read by MCP rather than reconstructed from screenshots.

## 4. Runtime inbox safety

A result relay must:

- use an allowlisted source directory/pattern;
- validate schema/status/firewalls before publication;
- preserve bytes and verify SHA256 after copy;
- write only to a fixed `docs/research/runtime-inbox/` target;
- never copy secrets, credentials, raw protected outcomes, or arbitrary files;
- leave commit/push to GitHub Control after assistant validation.

## 5. Current B15-P2 application

For the completed generic hydration mapper v0.4:

- VPS result pattern:
  `/home/botmarket/sc001_data/SC001_B15P2_NEXT_DATA_STRUCTURE_PROBE/next_data_structure_probe_v0_4_*.json`
- relay:
  `scripts/research/publish-b15p2-next-data-v04-result-to-github-v0.1.sh`
- GitHub runtime inbox:
  `docs/research/runtime-inbox/sc001-b15p2-next-data-structure-v0.4-latest.json`

After inbox publication, ChatGPT should inspect the exact JSON through GitHub Control before freezing the final hydration extractor rule.
