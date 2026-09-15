# SC001-E004 — Volatility Compression -> Breakout/Expansion Research Plan v0.1

Date: 2026-09-15  
Status: **PLANNING DOCUMENT — NOT YET A FROZEN EXECUTABLE PROTOCOL**

## 1. Purpose

Design the next independent SC001 candidate after E001/E002/E003, using the lessons already learned while preserving all anti-overfitting and chronology firewalls.

E004 is not a rescue of E001/E002/E003.

## 2. Core hypothesis

A period of unusually compressed short-horizon price range / realized volatility may contain accumulated latent pressure. A causal breakout from that compressed state may be followed by a sufficiently large directional expansion to overcome regular-user taker costs.

The intended edge is not "predict every next tick". The candidate seeks rare state transitions with movement measured in many basis points.

## 3. Why E004 is higher priority than another flow-only candidate

Evidence to date indicates:

- E002 TFI contains real but very small predictive information;
- E003 stronger flow intensity did not amplify that information into a large 60-second continuation move;
- regular-user round-trip taker cost is approximately 10 bps, so sub-bp effects are economically irrelevant for standalone high-turnover trading;
- trade-tape data now permit causal intraday breakout timing without relying on ambiguous hourly OHLC ordering.

Therefore E004 should target a low-turnover event with a larger natural price scale.

## 4. Research data boundary

Initial stage uses only already-open March-2024 OKX BTC-USDT-SWAP trade archives.

Planned slices:

- DEV-DISCOVERY: 2024-03-01 through 2024-03-20;
- one-time DEV-CONFIRMATION: 2024-03-21 through 2024-03-30, opened only after Discovery PASS;
- 2024-Q2 raw bodies: closed;
- formal Validation: closed;
- Final: closed.

No new L2 acquisition during Discovery.

## 5. Mandatory pre-test freeze items

Before first E004 alpha output, a versioned frozen protocol must define exactly:

1. compression measure;
2. compression lookback and minimum warm-up;
3. breakout reference level / band;
4. whether breakout is based on last trade, VWAP-like tape statistic, or another frozen trade-tape price definition;
5. breakout confirmation / strict inequality rules;
6. decision timestamp;
7. entry latency;
8. exit rule and horizon;
9. maximum one open position;
10. conflict / repeated breakout handling;
11. no overnight carry;
12. turnover ceiling;
13. Discovery and Confirmation gates;
14. small predeclared diagnostic neighborhood;
15. concentration and robustness diagnostics.

No parameter may be chosen after examining E004 returns.

## 6. Economic design target

Regular-user taker round-trip cost is approximately 10 bps before spread/depth deterioration.

Unlike E003's 12 bps near-break-even coarse hurdle, E004 should require a more meaningful safety margin before L2 work.

Current planning target:

**primary pooled gross edge >= approximately 15 bps**

subject to final mathematical audit before the executable freeze.

This is not a guarantee of profitability; it is an L2-promotion plausibility hurdle.

## 7. Required robust metrics

The frozen E004 Discovery gate should not depend on pooled mean alone. At minimum consider:

- completed trade count;
- trades/day and turnover;
- pooled mean gross edge;
- trimmed mean gross edge using a predeclared trim fraction;
- pooled median gross edge;
- median daily mean gross edge;
- positive daily mean day count;
- contribution concentration by top day / top small set of days;
- proxy completion rate;
- latency stress;
- small parameter-neighbor diagnostics that cannot replace a failed primary.

The exact numerical gates must be frozen before first E004 output.

## 8. Turnover discipline

E004 must explicitly constrain turnover. The mechanism should be rare enough that realistic fees do not dominate solely because of excessive frequency.

No overlapping positions, no pyramiding, and no repeated re-entry while the same frozen breakout episode remains active unless explicitly defined before testing.

## 9. E002/E003 feature firewall

Base E004 must not use:

- E002 TFI as an entry filter;
- E003 FLOW_IMPULSE as an entry filter;
- event/day exclusions inferred from earlier failures;
- one-sided selection inferred from earlier diagnostics.

This preserves E004 as an independently testable base mechanism.

## 10. Promotion order

`E004 protocol freeze -> implementation preflight -> DEV-DISCOVERY gross-economics screen -> unchanged DEV-CONFIRMATION -> only if PASS, L2 taker execution economics -> later protected temporal validation`

No L2 if Discovery or Confirmation fail.

## 11. Future E005 only after E004 viability

If and only if E004 is independently viable, reserve E005 for an incremental-value test of E002 TFI on top of E004.

E005 should ask whether TFI improves an already-existing trade decision by filtering, ranking, or timing it. It must not create a standalone TFI strategy and must not rescue a failed E004.

## 12. Alternative family if E004 fails

Large-price-jump continuation and reversal can be tested later under separate identifiers and both directions should be frozen before either result is observed. They are lower priority because they enter after a large move and may suffer from limited residual edge.

## 13. Next action

In a clean dialog, conduct one final expert mathematical/programming review of the E004 design and convert this planning document into a fully frozen executable protocol before implementing any alpha calculation.
