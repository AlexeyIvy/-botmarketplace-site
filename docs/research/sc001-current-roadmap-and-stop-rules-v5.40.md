# SC001 Current Roadmap and Stop Rules v5.40

Date: 2026-09-23  
Status: **B15-P1 REPRESENTATION DISPOSITION / IDENTITY RESOLUTION PRE-RUN REVIEW**  
Supersedes: `sc001-current-roadmap-and-stop-rules-v5.39.md`

## 1. Global isolation remains binding

SC001 remains independent from:
- R009
- R003
- R010
- Safe-Sleeve S002

Do not change their frozen rules, forward clocks, or terminal decisions.

All prior SC001 terminal/frozen outcomes remain unchanged unless a separately authorized protocol explicitly says otherwise.

## 2. B15-P1 source run remains valid

Source run:

`20260920T210446Z`

Status:

`B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_PASS`

Observed source manifest remains valid:
- Bybit spot USDT rows = 395
- OKX spot USDT rows = 406
- Bybit primary market bases = 369
- OKX primary market bases = 303
- common primary base candidates = 201
- Bybit chain identity rows = 300
- OKX chain identity rows = 265
- Bybit new-listing rows = 681
- Bybit delisting rows = 59
- maturity days = 90
- price endpoints called = false
- order endpoints called = false
- transfer endpoints called = false
- withdrawal endpoints called = false
- secret values printed = false

## 3. Canonical final-builder v0.1 result revalidated

Canonical safe export:

`docs/research/artifacts/b15-p1-canonical-freeze/20260920T210446Z/`

Exact counts:
- admitted assets = 146
- identity review assets = 46
- excluded assets = 9
- directed edges = 310
- proven USDT quote routes = 9
- quote_review = true
- price_data_used = false
- transfer_status_used_for_selection = false

The 46 review assets split:
- 16 = `UNRESOLVED_OBSERVED_ROUTE_OR_IDENTITY`
- 30 = `NO_PROVEN_COMMON_REPRESENTATION`

The v0.1 exit/review state remains intentional fail-closed, not a runtime failure.

## 4. New integrity finding before rerun

A static review on 2026-09-23 found that the next step must not be a blind registry expansion merely to make REVIEW disappear.

Binding audit:

`docs/research/sc001-b15-p1-identity-review-static-integrity-audit-v0.1.md`

Key implementation issues to correct before rerun:
- trim contract whitespace before empty/non-empty semantics;
- avoid case-only chainType false mismatches through explicit deterministic variants;
- canonicalize venue rows independently before cross-venue pairing;
- distinguish known one-sided representations from unresolved identities;
- add network-specific non-EVM normalization only where evidence supports it;
- prevent multiple different same-network representations from creating pairwise false conflicts;
- define quote completeness as complete classification of all observed representations plus all proven common routes, not forced matching of venue-only routes.

No frozen economic or statistical rule is changed by these corrections.

## 5. Current exact task

Current state:

`B15_P1_REPRESENTATION_DISPOSITION_V02_DESIGN_REVIEW`

Design candidate:

`docs/research/sc001-b15-p1-representation-disposition-builder-v0.2-design.md`

Required sequence:

1. finish evidence-backed review of the 46 identity cases;
2. freeze explicit network/native/normalization candidate v0.2;
3. implement v0.2 row-first representation audit/builder;
4. freeze exact code + registry hashes;
5. create immutable Runner bundle;
6. show SHA256 + approval code;
7. run only after explicit user approval;
8. read logs/artifacts;
9. accept PASS only if:
   - zero unresolved identity-review assets;
   - quote route graph is complete under the frozen v0.2 disposition semantics;
   - no price data was used;
   - no transfer ON/OFF status was used for selection.

## 6. Identity-review cases

Already-proven representation + additional unresolved observed identity (16):

`AVAX, BABYDOGE, BCH, BTC, ETC, ETH, FIL, G, LINK, LTC, SHIB, SOL, SUSHI, TRX, UNI, XRP`

No proven common representation under v0.1 (30):

`CC, CELO, DOT, EGLD, ENJ, FLR, FOGO, GRAM, HBAR, HYPE, ICP, KAIA, KSM, LUNA, MINA, MON, NIGHT, ORDI, QTUM, RVN, S, SATS, STX, THETA, TIA, WAXP, XLM, XPL, ZETA, ZIL`

Ambiguous/special normalization cases must remain fail-closed until explicit evidence is frozen.

## 7. Quote graph

Current proven common USDT routes (9):
- Aptos
- Arbitrum One
- Avalanche C-Chain
- Ethereum
- Optimism
- Polygon PoS
- Solana
- Tron
- TON

Additional one-sided/unresolved USDT representations must be explicitly classified before quote freeze.

No unrelated network may be forced to match solely to clear `quote_review`.

## 8. Collector gate

The 15-second B15 collector remains blocked until:

`B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE_PASS`

Do not start price/PnL research before this identity/route gate is closed.

## 9. Runner state

Production Research Runner v1.0.5 remains the required execution path.

In the current conversation, the custom Runner app is installed and has app permission `Allow all actions`, but Runner calls currently return:

`FORBIDDEN: This conversation does not support developer MCPs`

Treat this as a conversation/tool-routing limitation, not as a failed VPS isolation or research result.

Do not fall back to manual Termux execution.

GitHub control-plane fallback must not be used to bypass the Runner approval gate without explicit user authorization.
