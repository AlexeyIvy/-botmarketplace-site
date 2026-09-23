# BotMarketplace — SC001 B15-P1 identity/route v0.2.1 checkpoint backup v1.0

Date: 2026-09-23  
Scope: \`CHECKPOINT_BACKUP_AFTER_IDENTITY_ROUTE_V021_SNAPSHOT_FREEZE\`

## Purpose

Create a portable **non-secret host checkpoint** immediately after the SC001/B15-P1 identity/route v0.2.1 snapshot freeze and verify that the archive can be restored structurally.

This checkpoint is narrower than the later full B15 disaster-recovery package, but it preserves the current research state, Git history, Runner state, MCP/control-plane code, systemd configuration, redacted config structure and package manifests.

## Frozen anchor

Freeze commit:

\`a59cb2e2042579dfe12384c2fe6a4115d75b6790\`

Freeze record SHA256:

\`7818ec383728e8501decb1b133e0c1d766345f88df28021feb49a7a2a803bac6\`

Exact replay manifest SHA256:

\`6a0b39aea071b88fed9b957286a428ffcd98f60d7d9ef1e95c45f7381e21e856\`

Freeze candidate manifest SHA256:

\`63393e97573b9d64980f671f08e14071473d624682e4f8d67a2d21236ef0307d\`

## Script

\`scripts/backup/create-b15-v021-checkpoint.sh\`

Run on the VPS:

\`\`\`bash
sudo bash /var/lib/botmarket-github-control/repo/scripts/backup/create-b15-v021-checkpoint.sh
\`\`\`

Optional destination override:

\`\`\`bash
sudo BM_CHECKPOINT_DIR=/path/to/backup-dir \
  bash /var/lib/botmarket-github-control/repo/scripts/backup/create-b15-v021-checkpoint.sh
\`\`\`

Default destination:

\`/var/backups/botmarketplace/\`

## Archive contents

The normal archive contains Git history/bundle, a HEAD source snapshot, research freeze/replay artifacts already persisted in Git, non-secret Runner state, \`/opt/botmarket-*\` code with secret-like files excluded, dependency manifests, sanitized systemd units, redacted config structure, runtime/service metadata, an internal SHA256 manifest, and an explicit secrets-exclusion record.

## Secrets policy

The normal checkpoint deliberately excludes exchange API secrets, private SSH/deploy keys, OpenAI runtime API keys, plaintext \`.env\` values, and other credential/secret-like files.

Secrets belong only in a separate encrypted secrets archive. This script does **not** create that archive.

## Fail-closed preconditions

The script aborts if it is not root, the dedicated GitHub clone or Runner state is missing, the freeze commit is unavailable, HEAD is not a descendant of the freeze commit, the repository is dirty, any freeze/replay anchor SHA differs, or required host utilities are unavailable.

## Automatic restore verification

After creating the archive the script extracts it into a temporary directory, validates \`MANIFEST.sha256\`, runs \`git bundle verify\`, validates the Runner-state tar, extracts the repository snapshot and re-checks the freeze record, exact replay manifest and freeze candidate manifest SHA anchors.

Success output:

\`CHECKPOINT_BACKUP_RESTORE_VERIFY_PASS\`

It also writes:

\`<archive>.restore-verify.txt\`

Keep the archive, its \`.sha256\` file and restore-verification record together.

## Gate after success

A successful checkpoint/restore verification satisfies the immediate post-freeze preservation step. It does **not** authorize final zero-review route-universe PASS, the 15-second collector, or price/PnL research.

Remaining identity work stays GRAM, QTUM, STX, XLM, USDT/Bybit CORN and USDT/OKX Tempo. A new versioned preflight is required before later gates.
