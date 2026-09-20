# SC001 Dialog Handoff — 2026-09-20 v7.0

Date: 2026-09-20
Status: **CURRENT HANDOFF / CONTINUE IN NEW DIALOG**
Scope: `BotMarketplace / SCALPING RESEARCH / SC001`

Repository:

`AlexeyIvy/-botmarketplace-site`

---

## 1. Read first in the new dialog

Use as primary context, in this order:

1. `docs/research/dialog-handoff-2026-09-20-v7.0.md`
2. `docs/research/sc001-current-roadmap-and-stop-rules-v5.36.md`
3. `docs/research/sc001-b15-p1-transferability-shock-four-role-optimization-review-v0.2.md`
4. `docs/research/sc001-b15-p1-readonly-capability-pass-v0.1.md`
5. `docs/research/sc001-b15-p1-transferability-shock-source-access-semantic-feasibility-audit-v0.1.md`
6. `docs/research/sc001-b15-p1-read-only-credential-security-contract-v0.1.md`

Useful background:

7. `docs/research/sc001-strategy-landscape-v0.9.md`
8. `docs/research/sc001-current-four-role-critical-review-v0.1.md`
9. `docs/research/sc001-preoutcome-semantic-implementation-gate-v0.1.md`
10. `docs/research/sc001-background-collector-operational-resilience-plan-v0.1.md`

---

## 2. Global SC001 frozen history

All previous terminal decisions remain binding.

Do not rescue-tune or reopen:

- C1-C10 terminal/closed;
- C11 = `C11_TERMINAL_REJECT_DIRECTION_CAPTURE`;
- C12 = `C12_S0_REJECT_PARITY_REVERSION`;
- B13-A = `B13A_REJECT_STRUCTURAL`, scoped specifically to the tested single-settlement four-fill funding-differential architecture;
- B13-B historical S0 = `B13B_S0_DEFER_SAMPLE` after cross-venue underlying-identity failure.

No future work may retroactively change those verdicts.

---

## 3. B13-C — prospective liquidation collector

Purpose:

build a protected prospective raw liquidation-event database for future liquidation/scalping research.

Current state:

`B13C_COLLECTION_RUNNING`

Final supervised runner:

`research/sc001/sc001_b13c_bybit_prospective_liquidation_collector_v0_3.py`

Systemd service:

`sc001-b13c-liquidation.service`

Operational protection:

- starts at VPS boot;
- restarts on failure;
- ordered after network/time sync;
- persistent heartbeat;
- network-gap ledger;
- process/reboot-gap ledger.

Important research firewall:

Do not inspect B13-C protected data for alpha yet.

Forbidden until a separate future design is frozen:

- post-liquidation returns;
- continuation/reversal;
- threshold selection;
- symbol ranking;
- execution;
- PnL.

B13-C remains the main active source-building branch for future scalping research.

---

## 4. B14-A — dated-futures final-settlement convergence

Current state:

`B14A_P0_COLLECTION_WAITING`

Final supervised runner:

`research/sc001/sc001_b14a_p0_prospective_trade_collector_v0_3.py`

Systemd service:

`sc001-b14a-p0.service`

Exact frozen event:

- expiry: `2026-09-25T08:00:00Z`;
- connect: `2026-09-25T07:28:30Z`;
- capture: `2026-09-25T07:29:00Z .. 08:02:00Z`;
- decision anchor T0: `2026-09-25T07:30:00Z`.

Frozen pairs:

BTC:
- `BTC-USD-260925`
- `BTC-USD-SWAP`

ETH:
- `ETH-USD-260925`
- `ETH-USD-SWAP`

Frozen structural economics:

- final structural burden = 37 bps;
- P0 headroom hurdle = 50 bps.

Frozen readout rule:

`STRICT_COACTIVE_1S_NO_CARRY_FORWARD`

P0 remains only a prospective headroom pilot.

Do not alter B14-A before the Sep25 event.

No convergence/PnL is authorized yet.

---

## 5. Collector infrastructure migration

The B13-C and B14-A collectors were migrated from tmux to systemd successfully.

Observed terminal token:

`SC001_COLLECTOR_SYSTEMD_MIGRATION_PASS`

Binding record:

`docs/research/sc001-collector-systemd-migration-pass-v0.1.md`

Old tmux supervision is retired for these two collectors.

Single-VPS residual risks remain:

- complete provider outage spanning critical event time;
- permanent disk/host loss.

No redundant second VPS has been added yet.

---

## 6. B15 purpose and corrected interpretation

The user agreed to investigate B15 as a side branch while keeping scalping as the main SC001 mission.

B15 is NOT a replacement for scalping.

Current preferred B15 mechanism:

`B15-P1 INVENTORY-BACKED EFFECTIVE-TRANSFERABILITY SEGMENTATION`

Earlier shorthand:

transferability shock / capital segmentation.

Do not call it proven or risk-free arbitrage.

Economic hypothesis:

`LOSS OF EFFECTIVE CROSS-VENUE TRANSFERABILITY -> CAPITAL/INVENTORY SEGMENTATION -> POSSIBLE PRICE DISLOCATION`

Preferred first venue pair:

- OKX;
- Bybit.

---

## 7. B15-P1 second-pass lessons

Binding review:

`docs/research/sc001-b15-p1-transferability-shock-four-role-optimization-review-v0.2.md`

Key corrections:

### Financial

Two market fills do not complete the full economic cycle.

After rich/cheap cross-venue execution, inventory must later be restored.

Full-cycle structural burden must eventually include:

- two taker fills;
- spread/depth/slippage;
- base-asset rebalance transfer fee;
- quote-asset rebalance transfer fee;
- confirmation delay;
- capital-lock/opportunity cost;
- inventory/counterparty reserve.

Do not assume free rebalance or netting in the first sentinel.

### Trader

One disabled chain is not enough.

The relevant state is:

`EFFECTIVE DIRECTED TRANSFERABILITY`

If another common valid network remains usable, full segmentation may not exist.

Transfer direction matters separately:

- A withdrawal -> B deposit;
- B withdrawal -> A deposit.

Primary clean event stratum:

`VENUE_SPECIFIC_OPERATIONAL/WALLET_MAINTENANCE`

Separate from:

- chain-wide halt;
- exploit/security incident;
- token migration;
- delisting;
- compliance/account-specific restriction;
- project failure.

Scheduled and unscheduled events should also remain separate strata.

### Programmer

Use a canonical directed route graph.

At minimum identity must include:

`venue × asset × network × native/token × contract-address/native identity`

Ticker-only mapping is forbidden.

### Mathematics/statistics

Inference unit is not tick or asset-row count.

Primary unit:

`VENUE-LEVEL TRANSFERABILITY OUTAGE CLUSTER`

Nested dimensions may include:

- asset;
- network;
- transfer direction;
- venue pair.

Do not treat many tokens affected by one network outage as independent events.

Opportunity frequency is a first-class gate.

If clean events are too rare, keep B15 as opportunistic background research and return active research effort to scalping.

---

## 8. B15 source/access audit

Binding:

`docs/research/sc001-b15-p1-transferability-shock-source-access-semantic-feasibility-audit-v0.1.md`

Verdict:

`B15_P1_SOURCE_FEASIBILITY_PASS_AUTH_READ_ONLY_REQUIRED`

Source endpoints:

OKX:

`GET /api/v5/asset/currencies`

Bybit:

`GET /v5/asset/coin/query-info`

These provide chain-level deposit/withdraw state.

They are not treated as historical event archives.

B15 creates its own prospective chronology.

State-change causal time must be represented as an interval:

`(last_seen_old_state, first_seen_new_state]`

No fabricated exact exchange transition timestamp.

---

## 9. B15 credentials and security state

Dedicated read-only credentials now exist for both venues.

Security contract:

`docs/research/sc001-b15-p1-read-only-credential-security-contract-v0.1.md`

Local secret file:

`/home/botmarket/.config/sc001/b15-p1.env`

Mode:

`0600`

DO NOT:

- print secrets;
- paste secrets into chat;
- commit secrets to Git.

Current authenticated REST transport for B15 is process-local IPv4-only.

Reason:

- VPS dual-stack previously caused OKX to egress over IPv6;
- Bybit API-key whitelist UI accepted the stable VPS IPv4 but rejected the supplied IPv6;
- stable authenticated source-address behavior is preferable.

No system-wide routing was changed.

---

## 10. B15 credential-debug history — now resolved

This history is useful only to avoid repeating work.

Initial problems:

1. OKX returned 50110 because request egressed over IPv6 not in whitelist.
2. B15 was changed to IPv4-only transport.
3. Bybit initially returned 10003 because the VPS stored an old/deleted API key.
4. The Bybit public key was replaced.
5. Then 10004 confirmed the new public key was recognized but the key/secret pair needed correction.
6. During re-entry, the Bybit REST base URL was accidentally overwritten with the VPS IPv4.
7. Base URL was repaired to `https://api.bybit.com`.
8. Final capability run passed for both venues.

Do not reopen these issues unless a future capability check fails.

---

## 11. B15 read-only capability gate — PASS

Binding result:

`docs/research/sc001-b15-p1-readonly-capability-pass-v0.1.md`

Exact terminal token:

`B15_P1_READONLY_CAPABILITY_PASS`

Observed OKX state:

- `OKX = PASS`;
- base URL = `https://openapi.okx.com`;
- permission = `read_only`;
- IP bound = true;
- currency/chain rows = 591;
- clock skew approximately -241 ms.

Observed Bybit state:

- `BYBIT = PASS`;
- base URL = `https://api.bybit.com`;
- `readOnly = 1`;
- IP bound = true;
- wallet Withdraw token present = false;
- coin rows = 793;
- chain rows = 1035;
- clock skew approximately -130 ms.

Security confirmation:

- secret values printed = false;
- price endpoints called = false;
- order endpoints called = false;
- transfer endpoints called = false;
- withdrawal endpoints called = false.

API credential/access stage is complete.

---

## 12. Current roadmap

Binding current roadmap:

`docs/research/sc001-current-roadmap-and-stop-rules-v5.36.md`

Current exact next stage:

`CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE`

No B15 price-bearing research is authorized yet.

---

## 13. Exact next research task

In the new dialog, continue with B15-P1 and perform a NON-PRICE canonical route/universe identity design.

Goal:

freeze the first clean common OKX/Bybit spot-USDT asset/network universe before launching the 15-second status collector.

Required design questions:

1. What exact common mature spot-USDT assets should be admitted?
2. What maturity rule should be used?
3. How are same economic assets matched across venues?
4. How are chain names normalized?
5. How are native assets handled when contract address is empty?
6. How are token-contract addresses used for identity?
7. How are wrapped/rebased/rebranded/migrating assets excluded?
8. How are multiple common networks represented?
9. How is directed transferability computed?
10. What constitutes an identity conflict / IDENTITY_REVIEW?
11. How are chain disappearances/schema changes handled?
12. What fixed universe is frozen before the collector starts?

Suggested initial universe class from the second-pass review:

`COMMON MATURE SPOT-USDT ASSETS`

Initial exclusions:

- stablecoin base assets;
- leveraged tokens;
- pre-market/recent launch assets;
- active delisting;
- token migration;
- unresolved wrapped/native ambiguity;
- unresolved cross-venue contract-address/network identity.

No asset may be selected using price/spread/PnL behavior.

---

## 14. After route identity freeze

Only after the identity/universe freeze:

design and launch a prospective status-only collector with:

- OKX + Bybit requests in parallel;
- fixed 15-second cadence;
- IPv4-only authenticated REST;
- raw append-only snapshots;
- normalized chain-state snapshots;
- explicit state-transition events;
- directed route graph;
- outage-cluster IDs;
- heartbeat;
- source-gap ledger;
- schema-drift fail-closed behavior;
- systemd supervision.

The collector must NOT access:

- prices;
- spreads;
- returns;
- execution;
- PnL.

---

## 15. Price-bearing gate sequence after collector launch

Do not skip stages.

Required sequence:

1. canonical route/universe identity freeze;
2. status collector launch;
3. source-only opportunity-rate checkpoint;
4. full-cycle Edge-to-Fill card;
5. freeze event-specific price protocol;
6. first headroom sentinel;
7. only survivors may proceed to convergence/rebalance/execution/PnL.

First future price-bearing question:

`Does raw executable cross-venue dislocation exceed the frozen full-cycle structural burden?`

No price-threshold shopping.

---

## 16. Current user preference / workflow

User prefers:

- continue from one exact next step at a time;
- use expert-role critical reviews before important design choices;
- preserve results and next steps in GitHub;
- receive copy-paste terminal commands;
- use Android + Termux to operate the VPS;
- avoid paid datasets when free sources are adequate.

Do not ask the user to paste API secrets into chat.

---

## 17. New-dialog opening prompt

Copy/paste:

```
Продолжаем проект BotMarketplace, независимая ветка SCALPING RESEARCH / SC001.
Репозиторий: AlexeyIvy/-botmarketplace-site.

Сначала прочитай и используй как основной контекст:

1. docs/research/dialog-handoff-2026-09-20-v7.0.md
2. docs/research/sc001-current-roadmap-and-stop-rules-v5.36.md
3. docs/research/sc001-b15-p1-transferability-shock-four-role-optimization-review-v0.2.md
4. docs/research/sc001-b15-p1-readonly-capability-pass-v0.1.md
5. docs/research/sc001-b15-p1-transferability-shock-source-access-semantic-feasibility-audit-v0.1.md
6. docs/research/sc001-b15-p1-read-only-credential-security-contract-v0.1.md

Важно:
- C1-C12 и B13-A/B13-B historical verdicts остаются frozen/terminal.
- B13-C prospective liquidation collector работает под systemd и его protected data нельзя открывать для alpha.
- B14-A P0 работает под systemd и ждёт событие 2026-09-25; его правила до события не менять.
- B15-P1 = INVENTORY-BACKED EFFECTIVE-TRANSFERABILITY SEGMENTATION.
- OKX + Bybit read-only capability gate успешно пройден: B15_P1_READONLY_CAPABILITY_PASS.
- API credentials уже установлены на VPS в защищённом локальном файле; никаких ключей/secret в чат не просить.
- B15 authenticated REST для этой ветки использует IPv4-only.
- Цены/spread/PnL по B15 пока НЕ открывать.

Текущий точный следующий этап:
CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE.

Нужно сначала критически спроектировать и заморозить:
- общий mature spot-USDT universe OKX/Bybit;
- exact asset identity;
- exact network mapping;
- native/token + contract-address rules;
- directed transferability graph;
- ambiguity/IDENTITY_REVIEW rules;
- universe exclusions;
- fail-closed schema/chain disappearance behavior.

После этого, и только после этого, проектировать 15-секундный prospective transferability-state collector без цен.

Начни с анализа следующего этапа из ролей:
1) финансовый эксперт,
2) трейдер,
3) программист,
4) математик-статист,
затем сделай общий синтез и предложи оптимизированный canonical identity/universe freeze.
```
