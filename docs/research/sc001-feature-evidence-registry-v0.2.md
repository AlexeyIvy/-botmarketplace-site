# SC001 — Feature Evidence Registry v0.2

Date: 2026-09-18  
Status: **APPEND-ONLY CONTINUATION AFTER C1-C6 SELECTION BATCH**  
Parent: `sc001-feature-evidence-registry-v0.1.md`

## 1. Inheritance rule

Records F001-F008 in v0.1 remain unchanged and binding.

This version appends new scoped Selection/Calibration-only records. It does not convert any sentinel result into promotional evidence.

All new records have contamination/evidence role:

`SELECTION_CALIBRATION_ONLY`

## 2. New records

### F009 — multi-asset same-venue spot/perp basis dislocation under strict E006 rule

- primitive family: P8 relative value / derivative state;
- role: R1 core signal + R6 ordinary-basis reference;
- candidate: C1;
- market/universe: OKX BTC/ETH/DOGE/ORDI/UNI/XRP/OP/BCH spot-perpetual pairs;
- horizon: 10-second observations, 6-hour baseline, <=30-minute resolution;
- evidence: frozen sentinel produced zero measured +50 bps triggers;
- classification: `MULTIASSET_STRICT_RULE_EVENT_SCARCITY`;
- allowed reusable conclusion: the strict E006-style +50 bps dislocation mechanism was too scarce in the tested contaminated July/September multi-asset sandbox;
- forbidden overclaim: spot/perp relative value or basis features are globally useless;
- future rule: no lower-threshold rescue under C1.

### F010 — multi-minute local-reference deviation

- primitive family: P1 price/location + P7 reference price;
- role: R1 deviation signal + R6 reference;
- candidate: C2;
- variants: trailing 5-minute aggregate VWAP reference and median of five completed 1-minute VWAPs;
- evidence: 2032 and 4730 non-overlapping opportunities respectively, full 28-day coverage, but equal-weight signed reversion means about -3.96 and -4.28 bps;
- classification: `ABUNDANT_SAMPLE_NEGATIVE_REVERSION_EFFECT`;
- allowed reusable conclusion: simple multi-minute deviation from these two causal local references did not support the frozen mean-reversion hypothesis;
- forbidden overclaim: VWAP or robust local centers are ineffective in all roles;
- future rule: any trend/volatility veto becomes a new pre-registered question, not a rescue.

### F011 — completed-bar breakout + volatility expansion state

- primitive family: P2 trend/persistence + P3 volatility/range;
- role: R1 breakout state + R2/R1 expansion state;
- candidate: C3;
- variants: 5m->10m and 10m->20m;
- evidence: 4871 and 2375 non-overlapping events, all 8 assets and 28 days active, but equal-weight continuation means about -0.52 and -0.49 bps;
- classification: `ABUNDANT_SAMPLE_NO_CONTINUATION_HEADROOM`;
- allowed reusable conclusion: the tested simple expansion/breakout construction had essentially no portable gross continuation edge;
- forbidden overclaim: volatility expansion as a state feature is globally useless;
- future rule: no post-hoc ADX/MACD/volume/flow bundle.

### F012 — BTC/ETH leader impulse and common-factor-adjusted alt residual response

- primitive family: P9 cross-asset information transfer;
- role: R1 leader impulse + R6 common-factor adjustment;
- candidate: C4;
- evidence: all four variants had 28 active days, six targets and thousands of event-target observations; residual means were broadly positive but only about +0.38 to +0.67 bps equal-weight, with median target means about +0.41 to +0.77 bps;
- classification: `BROAD_POSITIVE_SIGN_BUT_SUB_BPS_RESIDUAL_EFFECT`;
- allowed reusable conclusion: simple same-venue BTC/ETH short-lag residual responses were too small to justify directional taker economics;
- forbidden overclaim: all cross-asset information transfer is absent;
- future rule: no lag grid or historical target selection under C4.

### F013 — 30-second signed aggressive-notional exhaustion state

- primitive family: P5 aggressive flow + P10 forced-flow/event state;
- role: R1 event trigger;
- candidate: C5;
- evidence: 10033 pooled events, all assets active, 6/8 positive asset means, median active-asset mean about +0.505 bps and per-asset means roughly -0.36 to +1.10 bps;
- classification: `ABUNDANT_BROAD_SIGN_BUT_SUB_BPS_EFFECT`;
- allowed reusable conclusion: the tested trade-only exhaustion response was far too small for the frozen 15 bps two-fill screen;
- forbidden overclaim: aggressive-flow state contains no information;
- future rule: L2 depth/replenishment is not justified as a rescue of C5.

### F014 — cross-sectional equal-weight residual dispersion/reversion

- primitive family: P9/P1 cross-sectional/common-factor residual;
- role: R1 relative dislocation + R6 common-market normalization;
- candidate: C6;
- evidence: 2688 opportunities on all 28 days; positive-day share about 71.4%; concentration within frozen limits; trimmed spread about +3.00 bps, median about +3.84 bps, equal-weight day mean about +1.93 bps;
- classification: `POSITIVE_TENDENCY_BUT_INSUFFICIENT_FOUR_FILL_HEADROOM`;
- allowed reusable conclusion: a weak positive relative-reversion pattern existed in the tested simple construction, but magnitude was far below the 30 bps paired screen;
- forbidden overclaim: cross-sectional relative value cannot work;
- future rule: no factor/volatility/asset-selection rescue under C6.

## 3. Cross-record lesson

C2-C6 demonstrate that statistical abundance, positive breadth, or a consistent sign are not enough.

Feature evidence must remain distinct from strategy economics:

- C4/C5/C6 contain weak directional structure worth retaining as scoped feature knowledge;
- none established standalone executable alpha under the tested strategy architecture;
- future reuse must be prospective and role-specific.

No new classical-indicator claim is created by this batch.
