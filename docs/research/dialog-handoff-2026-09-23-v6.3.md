# SC001 / B15-P1 — dialog handoff v6.3 — 2026-09-23

Latest state:

`B15_P1_V021_GITHUB_CHECKPOINT_RESTORE_VERIFY_PASS_AFTER_CHECKER_CORRECTION`

The v0.2.1 identity/route snapshot is frozen with explicit quarantine and GitHub research-state restore has been verified.

Current composite:
- 188 admitted
- 4 quarantine: GRAM, QTUM, STX, XLM
- 9 excluded
- 203 canonical representations
- 406 directed identity edges
- 12 USDT common representations
- 9 unresolved rows
- 2 USDT holds: Bybit CORN, OKX Tempo

Freeze commit:

`a59cb2e2042579dfe12384c2fe6a4115d75b6790`

Checkpoint tooling commit:

`0187cd7223298c006b6fb0692c21ea7fd1026116`

Correction audit:
- bundle `bundle_20260923T203154Z_95c98996`
- SHA256 `d5bf680d7d0bb29eddbb8255577f956edbb212ca9c0822ad151a8ac949beec15`
- job `job_20260923T203506Z_2cca7a49`
- manifest SHA256 `620321ac8e788990f6e40bbb3c2cb962ee85359c8d911c8665cd34fdea621f8b`
- failed_checks = []

The prior restore verifier false-negative was only a checker field-name typo:
`bybitReadOnly` -> correct immutable source field `bybit_readOnly`.

No research input or research logic changed.

Host-level VPS checkpoint is still pending because the available MCP tools intentionally do not expose arbitrary host shell access.

Run on VPS:

```bash
sudo bash /var/lib/botmarket-github-control/repo/scripts/backup/create-b15-v021-checkpoint.sh
```

Expected terminal line:

`CHECKPOINT_BACKUP_RESTORE_VERIFY_PASS`

After host backup PASS, capture its archive path/SHA/restore-verify record in GitHub. Then continue evidence-backed resolution of GRAM/QTUM/STX/XLM and USDT CORN/Tempo.

Do not authorize price/PnL, final zero-review PASS or collector launch before those gates.
