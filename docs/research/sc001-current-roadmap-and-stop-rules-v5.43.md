# SC001 Current Roadmap and Stop Rules v5.43

Date: 2026-09-23  
Status: **B15-P1 v0.2.1 RESEARCH STATE RESTORE VERIFIED / HOST CHECKPOINT PENDING**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.42.md`

## Current frozen research state

Identity/route snapshot v0.2.1 remains frozen with explicit quarantine.

Composite snapshot:
- total assets = 201
- admitted = 188
- review/quarantine = 4: GRAM, QTUM, STX, XLM
- excluded = 9
- canonical representations = 203
- directed identity edges = 406
- USDT common representations = 12
- quote_review = true
- remaining unresolved rows = 9
- USDT hold rows = 2: Bybit CORN, OKX Tempo

Exact replay and freeze-preflight remain PASS with zero alias collisions and zero disposition mismatches.

## GitHub restore verification

The first GitHub-only restore verifier job:

`job_20260923T203019Z_5100d22b`

returned a technical false-negative because the verifier used `bybitReadOnly` while the immutable source manifest key is `bybit_readOnly`.

All SHA, source, base-v0.1, exact-replay, freeze, quarantine and safety checks other than that checker were already PASS.

Correction audit:

- bundle: `bundle_20260923T203154Z_95c98996`
- SHA256: `d5bf680d7d0bb29eddbb8255577f956edbb212ca9c0822ad151a8ac949beec15`
- job: `job_20260923T203506Z_2cca7a49`
- status: `B15_P1_V021_GITHUB_CHECKPOINT_RESTORE_VERIFY_PASS_AFTER_CHECKER_CORRECTION`
- failed_checks = []
- research inputs changed = false
- research logic changed = false

This verifies that the research state can be reconstructed from GitHub-persisted artifacts independently of prior Runner job storage.

## What is still not complete

The physical VPS host checkpoint has **not** yet been run.

Current host checkpoint state:

`RUN_PENDING`

Required script:

`scripts/backup/create-b15-v021-checkpoint.sh`

Required VPS command:

```bash
sudo bash /var/lib/botmarket-github-control/repo/scripts/backup/create-b15-v021-checkpoint.sh
```

The script creates a non-secret portable archive, SHA256 manifest and immediate restore verification.

## Safety gates

Still false:
- final zero-review route-universe PASS
- collector authorization
- price/economic research authorization

Do not start price/PnL or the 15-second collector until the host checkpoint is PASS and later versioned identity hold-resolution gates are satisfied.

## Next state

`RUN_HOST_CHECKPOINT_SCRIPT_AND_CAPTURE_PASS_RECORD`
