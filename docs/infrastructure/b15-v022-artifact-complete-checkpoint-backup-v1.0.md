# BotMarketplace — SC001 B15-P1 v0.2.2 artifact-complete checkpoint backup v1.0

Date: 2026-09-24  
Scope: `CHECKPOINT_BACKUP_AFTER_V022_FINAL_FREEZE_ARTIFACT_COMPLETION`

## Purpose

Create and immediately restore-verify a portable non-secret VPS checkpoint after completion of the final v0.2.2 freeze artifact set.

This checkpoint is anchored to the artifact-completion commit, not merely to the earlier final-freeze commit.

## Preservation anchors

Artifact-completion commit:

`f0b069efdd382d6f35d9a2b3e9668f35b8a48235`

Original final-freeze commit:

`7fdaf8c8e3053e2bbf266ec7d89c3abc90c3661f`

Freeze record SHA256:

`dfa7466e6133ba8adef99d64114d5651199c0f6432a14a5b76434a200b5b937b`

Artifact supplement SHA256:

`6241a66f93dfcbd74d2ea8c3ac164c746f87236d653895b8cbf01ce348913997`

Artifact manifest SHA256:

`a1a813244dc8cd81c2002e54650b8202c318ee9589f443301a9e624c46bb7b79`

Route shard-index SHA256:

`001c89a7d4e973ed33ab072ec43746f6f7b6c0105912a24ae0483955ac93a50a`

Logical full 414-edge route graph SHA256:

`06a9edd309a002aa5dc8408d992cff7b774604fc1cfb04f90fd7f56333f27928`

## Script

`scripts/backup/create-b15-v022-artifact-complete-checkpoint.sh`

Run on VPS:

```bash
sudo bash /var/lib/botmarket-github-control/repo/scripts/backup/create-b15-v022-artifact-complete-checkpoint.sh
```

Default destination:

`/var/backups/botmarketplace/`

## Additional verification versus the prior checkpoint

The script now also fails closed unless:

- the artifact supplement SHA matches;
- the materialized artifact-manifest SHA matches;
- the route-graph shard-index SHA matches;
- concatenating the five raw graph shards reproduces the exact logical graph SHA before backup;
- the same graph reassembly reproduces the exact SHA after test restore.

This ensures the 414-edge graph is not merely referenced by count; its complete content is preserved and recoverable.

## Standard safety

The normal archive excludes plaintext secrets and private credential-like files.

Dirty repository, wrong anchor commit, missing Runner state, hash mismatch, archive corruption or restore mismatch => abort.

A failed run deletes the new unverified archive.

## Required success output

`CHECKPOINT_BACKUP_RESTORE_VERIFY_PASS`

Also record:

- `ARCHIVE=...`
- `ARCHIVE_SHA256=...`
- `VERIFY_RECORD=...`

## Gate after success

After checkpoint PASS, the completed v0.2.2 identity/freeze artifact foundation is preservation-complete.

Then proceed to the already drafted B15-P1 Full-cycle Edge-to-Fill structural preflight.

Collector launch and price/PnL remain separate later gates.
