# BotMarketplace — SC001 B15-P1 v0.2.2 final-freeze checkpoint backup v1.0

Date: 2026-09-24  
Scope: `CHECKPOINT_BACKUP_AFTER_V022_FINAL_IDENTITY_ROUTE_FREEZE`

## Purpose

Create and immediately restore-verify a portable non-secret VPS checkpoint after the final v0.2.2 identity/route freeze.

## Frozen anchors

Freeze commit:

`7fdaf8c8e3053e2bbf266ec7d89c3abc90c3661f`

Freeze record:

`docs/research/sc001-b15-p1-final-identity-route-v0.2.2-freeze-v1.json`

Freeze record SHA256:

`dfa7466e6133ba8adef99d64114d5651199c0f6432a14a5b76434a200b5b937b`

Exact replay manifest SHA256:

`ad842a5f7be42c7c4cae6ce13b91846de7e17e17cb06cf1152aa4f69538c1f7b`

Final freeze candidate SHA256:

`1519940e2580fc246d745e11cb06dda564b83f6b7cb689583eb2d1c386c8fabd`

## Script

`scripts/backup/create-b15-v022-final-freeze-checkpoint.sh`

Run on the VPS:

```bash
sudo bash /var/lib/botmarket-github-control/repo/scripts/backup/create-b15-v022-final-freeze-checkpoint.sh
```

Default destination:

`/var/backups/botmarketplace/`

## Safety

The normal checkpoint intentionally excludes plaintext secrets, private SSH/deploy keys, exchange API secrets, OpenAI runtime API keys, plaintext `.env` values and secret-like files.

The script is fail-closed:
- dirty repo => abort;
- wrong/missing freeze commit => abort;
- freeze/replay/freeze-candidate SHA mismatch => abort;
- restore verification failure => the new archive is deleted.

## Automatic verification

The script:
1. creates a Git bundle and HEAD snapshot;
2. archives non-secret Runner state and MCP/control-plane code;
3. writes `MANIFEST.sha256`;
4. creates the final archive;
5. re-extracts it;
6. verifies every internal SHA;
7. verifies the Git bundle in a temporary Git repository;
8. checks the Runner-state tar;
9. restores the repo snapshot;
10. re-checks the final freeze, replay and freeze-candidate SHA anchors.

Required success line:

`CHECKPOINT_BACKUP_RESTORE_VERIFY_PASS`

Keep together:
- archive;
- `.sha256`;
- `.restore-verify.txt`.

## Gate after success

A PASS satisfies the post-freeze preservation gate.

It does **not** itself authorize:
- collector launch;
- live execution;
- price/PnL research.

Those remain separate versioned authorization gates.
