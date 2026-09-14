# SC001 VPS Qualification and Q008 Parity Results v0.1

Date: 2026-09-14  
Status: **PASS — VPS QUALIFIED FOR FUTURE HEAVY SC001 COMPUTE**  
Scope: infrastructure qualification only; no new financial rule, alpha, P&L, Q2, formal Validation or Final access.

## 1. Purpose

Qualify the newly purchased Timeweb Cloud VPS as a reproducible heavy-compute environment for future SC001 work without changing frozen financial/statistical semantics.

The migration rule remained unchanged throughout:

- infrastructure changes must not change SC001 financial rules;
- the already-running Android four-day OKX Q1 midquote confirmation must not be moved mid-run merely because a faster environment exists;
- the VPS may become the primary environment for **new** heavy SC001 stages only after exact Q008 parity is demonstrated.

No public IP, password, private SSH key, API credential or other secret is recorded in this document.

## 2. VPS environment qualification

Provider/region:

- Timeweb Cloud;
- Frankfurt, Germany.

Observed environment:

- OS: Ubuntu 24.04.5 LTS;
- kernel: Linux 6.8.0-139-generic;
- architecture: x86_64;
- CPU: 4 vCPU;
- visible CPU model: AMD EPYC-Rome Processor;
- RAM: about 7.8 GiB;
- root filesystem: about 77 GB, with about 75 GB free at initial audit;
- Python: 3.12.3;
- pip: 24.0;
- git: 2.43.0;
- tmux: 3.4;
- curl, wget, htop and jq installed and working.

Result: `VPS-ENV-001 = PASS`, `VPS-ENV-002 = PASS`.

Python 3.12.3 was retained as the Ubuntu system Python. No attempt was made to force Python 3.14 parity with the Android Termux runtime; reproducibility was instead tested directly using the frozen Q008 engine and identical input bytes.

## 3. SSH/security qualification

A dedicated non-root user `botmarket` was created and added to `sudo`.

An ED25519 keypair was generated locally in Termux on the Android phone. Only the public key was installed on the VPS.

Successful checks:

- fresh SSH login as `botmarket` using public-key authentication;
- `sudo whoami` returned `root`;
- OpenSSH config syntax check passed;
- effective SSH config after hardening:
  - `PermitRootLogin no`;
  - `PasswordAuthentication no`;
  - `KbdInteractiveAuthentication no`;
  - `PubkeyAuthentication yes`;
- SSH service was active after reload;
- a **new** post-hardening SSH connection as `botmarket` using the key succeeded.

Result: `VPS-SEC-001 = PASS`.

## 4. Repository qualification

Repository cloned under the `botmarket` account:

`AlexeyIvy/-botmarketplace-site`

Observed branch/HEAD at qualification time:

- branch: `main`;
- HEAD: `99fe3ac31fcdfc1e49090163a5866811d3f5e97b`.

The required SC001 context and Q008 files were present, including:

- `docs/research/dialog-handoff-2026-09-14-v2.0.md`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v1.1.md`;
- `docs/research/dialog-handoff-2026-09-11-v1.0.md`;
- `docs/research/sc001-data-q008-okx-l2-full-day-pilot-results-v0.1.md`;
- `research/sc001/sc001_data_q008_okx_l2_full_day_pilot.py`.

GitHub HTTPS access worked without exposing credentials.

Result: `VPS-REPO-001 = PASS`.

## 5. Network qualification

Outbound connectivity was checked from the VPS to the three required public sources.

Observed:

- raw GitHub: HTTP 200, TLS verification success;
- OKX static host: DNS/TLS successful; root path returned HTTP 403, which is acceptable because the root URL is not the frozen data object;
- Binance public-data object: HTTP 200, TLS verification success.

The exact OKX Q008 discovery path was later exercised with the frozen Q007 discovery logic after adapting only the Android filesystem root to a valid Linux path.

Result: `VPS-NET-001 = PASS`.

## 6. Frozen Q008 code identity

Parity used the frozen Q008 implementation, not a newly rewritten replay engine.

Frozen implementation reference:

- Q008 engine commit: `d4aa9720e43a39e215af7d866bd273c68340381c`;
- frozen engine path: `research/sc001/sc001_data_q008_okx_l2_full_day_pilot.py`.

Verification showed the current repository copy matched the frozen commit for that engine.

Frozen constants confirmed:

- date: `2024-01-05`;
- instrument: `BTC-USDT-SWAP`;
- filename: `BTC-USDT-SWAP-L2orderbook-400lv-2024-01-05.tar.gz`;
- expected compressed bytes: `500060536`.

The frozen engine was extracted from the frozen commit into a separate VPS parity workspace.

## 7. Source discovery / identity

The original Q007/Q008 code was Android-oriented and referenced `/storage/emulated/0/Download`. On Ubuntu this caused an initial local `FileNotFoundError` before any real OKX discovery request completed.

This was treated strictly as an infrastructure-path incompatibility, not a data or strategy failure.

For parity, only the filesystem root used by the frozen discovery module was redirected to an existing Linux home path at runtime. Discovery semantics, date, instrument, filename selection and trusted-host rules were unchanged.

The frozen Q007 discovery logic then returned:

- discovery status: `PASS`;
- exact candidate count: one;
- mode: `EXACT_DATE_FILENAME`;
- filename: `BTC-USDT-SWAP-L2orderbook-400lv-2024-01-05.tar.gz`;
- host: `static.okx.com`;
- discovery API code: `0`;
- HTTP status: `200`.

HEAD identity check returned:

- status: `PASS`;
- HTTP: `200`;
- content length: `500060536`;
- final host: `static.okx.com`.

No archive body was downloaded during the metadata/HEAD checks.

## 8. Archive identity

The exact discovered archive was downloaded to the VPS parity workspace using resumable transfer.

Observed compressed size:

`500060536 bytes`

Observed SHA256:

`7279d6b87021ea64982449f5a7c86e298a5c46c1c107ac41a368debeaaf5929a`

This matches the previously qualified Q008 archive exactly.

Result: `ARCHIVE_IDENTITY_PASS`.

## 9. Q008 semantic replay parity

The frozen Q008 `replay_full_archive()` implementation was run directly against the hash-verified archive.

VPS result:

- status: `FULL_DAY_PASS`;
- records parsed: `7,568,405`;
- snapshots: `1,441`;
- updates: `7,566,964`;
- first timestamp: `2024-01-05T00:00:00.005000+00:00`;
- last timestamp: `2024-01-05T23:59:59.990000+00:00`;
- minute buckets observed: `1440`;
- crossed-book states: `0`;
- empty-book states: `0`;
- delete-missing-level events: `0`.

These values match the original qualified Q008 reference exactly.

Measured VPS elapsed replay time:

`437.88 seconds` (~7 min 18 sec).

This timing is a machine/runtime baseline only. It is not a strategy statistic and must not be used to change research rules.

## 10. Qualification verdict

`VPS-PARITY-001 = PASS`.

Full infrastructure chain:

`VPS-ENV-001 PASS -> VPS-ENV-002 PASS -> VPS-SEC-001 PASS -> VPS-REPO-001 PASS -> VPS-NET-001 PASS -> VPS-PARITY-001 PASS`

Therefore the Frankfurt VPS is now a **qualified primary environment for future heavy SC001 computations**.

This approval applies to new computation stages only. It does **not** authorize changing frozen financial rules, dates, thresholds, gates, latency assumptions or research interpretation.

## 11. Active research boundary remains unchanged

The already-running Android/Termux four-day frozen OKX Q1 midquote confirmation remains authoritative for that stage and must not be moved to the VPS mid-run merely because VPS qualification passed.

Its final verdict was still not established by this infrastructure test.

Do not interpret partial confirmation checkpoints.

After the Android confirmation completes:

- if `MIDQUOTE_CONFIRMATION_PASS`: freeze executable taker economics before any P&L;
- if `MIDQUOTE_CONFIRMATION_FAIL`: stop/downgrade E002 with no rescue tuning;
- if `MIDQUOTE_CONFIRMATION_WEAK`: follow the predeclared frozen interpretation rather than silently treating it as PASS.

Q2 OKX, formal Validation and Final remain unopened.

## 12. Next operational action

Check the Android Termux `confirm` tmux session and determine whether the final four-day confirmation report exists.

Do not infer the verdict from terminal history or partial per-day checkpoints.
