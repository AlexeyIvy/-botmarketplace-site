# SC001-DATA-A002-B04B05 Confirmation Acquisition v0.1

Status: **FROZEN BEFORE DOWNLOAD**  
Purpose: acquire and qualify all 10 reserved DEV-CONFIRMATION Binance BTCUSDT USD-M `aggTrades` days before any E002 confirmation feature is calculated.

## Scope

Dataset: Binance USD-M Futures `BTCUSDT` daily `aggTrades` archives.

Frozen source: local `SC001-DATA-A002-PREFLIGHT` report tied to calendar SHA256:

`e6bd2ddfee7d1ea8fbac89f9ae1aa3e038bbac83e0d624c98af14588bf0cbb7b`

### B04 / 2024-Q1
- 2024-01-05 — NFP — 20,807,819 bytes — SHA256 `54cfc506daff386c40ac923d161cac31f7c53d55c412165c7daefdca1d428416`
- 2024-01-14 — ordinary weekend — 10,575,353 bytes — SHA256 `60aef45bc81962b230f41fd41c1ff1bddaa69893a3d93f61b77c85b0cca29c32`
- 2024-01-31 — FOMC — 15,284,170 bytes — SHA256 `b4748dc7abaaf3cd3b4f2c6c22ca68e32273760e47a85d0ef81cda9272e8b4f9`
- 2024-02-12 — ordinary weekday — 22,088,730 bytes — SHA256 `79fcbd8c45cb95fc966234d856579174b89002c7e6105fa191333c50b7aa35ae`
- 2024-02-13 — CPI — 19,099,037 bytes — SHA256 `625d14e8a257fd9af2ff20cb81a4583191817bceb601133e04740d1ecaafb0fc`

B04 expected compressed total: `87,855,109` bytes.

### B05 / 2024-Q2
- 2024-04-10 — CPI — 23,733,631 bytes — SHA256 `d07810250019fec4f9201eddb9fbc68a1ec4e9b1854af9921e0e5b0154e8c388`
- 2024-04-20 — ordinary weekend — 16,313,893 bytes — SHA256 `f00b085f8262e0a4d5fd97d4c751344877d4194ac0704724c7d21f15024764ba`
- 2024-05-01 — FOMC — 38,513,458 bytes — SHA256 `f41f292348137f14cfc888ba458fabbaa7db95a871c45191c42c74993cce8c4a`
- 2024-06-07 — NFP — 17,788,758 bytes — SHA256 `7ab0dbb225de014133a92b4cadefdba25f35faf7639fa54b26495b22fb4581ab`
- 2024-06-27 — ordinary weekday — 9,941,100 bytes — SHA256 `5be30ff49a4f6f5e52b971fdb5cf705ad963831b787f4d42aa5224fe6e33aa79`

B05 expected compressed total: `106,290,840` bytes.

Combined expected compressed total: `194,145,949` bytes.

## Safety freeze

- session network cap: 300,000,000 bytes;
- workspace cap: 300,000,000 bytes;
- single archive cap: 256,000,000 bytes;
- minimum free-space reserve: 4,000,000,000 bytes;
- max uncompressed ZIP member: 2,000,000,000 bytes.

No cap may be raised after seeing the run.

## Identity checks

Before each archive body is used:
1. local preflight report must be `PASS`, 25/25 days, DEV-only, and tied to the frozen calendar SHA;
2. frozen date, expected SHA256, and expected Content-Length must exactly match the preflight record;
3. live `.CHECKSUM` SHA256 must still match the frozen SHA;
4. live HEAD Content-Length must still match the frozen byte count;
5. downloaded/reused ZIP byte size and SHA256 must match exactly.

Any mismatch stops the stage.

## Content integrity gates

For every day:
- ZIP CRC valid;
- exactly one expected CSV data member;
- 7-column aggTrades schema;
- price and quantity positive finite decimals;
- `first_trade_id <= last_trade_id`;
- `is_buyer_maker` valid boolean;
- all rows inside requested UTC day;
- timestamps monotonic nondecreasing;
- aggregate trade IDs strictly contiguous with no duplicate/backward event;
- underlying trade-ID ranges non-overlapping/non-backward;
- all 1,440 UTC minute buckets observed;
- both maker-flag values observed.

Underlying raw-trade-ID gaps remain diagnostic only and are not a FAIL gate.

## Firewall

This acquisition stage calculates:
- no TFI feature;
- no future-return label;
- no Spearman;
- no decile statistic;
- no strategy P&L.

The 10 days are qualified as a single confirmation acquisition set. No B04-only feature result may be computed before B05 also passes.

Formal Validation and Final remain unopened.

## PASS rule

`PASS` requires 10/10 days PASS and zero cross-selected-day ID ordering violations.

PASS authorizes exactly one later combined E002 DEV-CONFIRMATION screen under `sc001-e002-confirmation-freeze-v0.1.md`. It does not authorize tuning or executable-profit claims.