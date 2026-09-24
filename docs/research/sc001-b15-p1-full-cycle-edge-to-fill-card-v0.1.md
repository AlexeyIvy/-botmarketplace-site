# SC001 — B15-P1 Full-Cycle Edge-to-Fill Card v0.1

Date: 2026-09-24  
Status: **NON-PRICE STRUCTURAL COST CARD / CANDIDATE FREEZE**  
Scope: `SCALPING RESEARCH / SC001 / B15-P1`

Parents:

- `docs/research/sc001-b15-p1-transferability-shock-four-role-optimization-review-v0.2.md`;
- `docs/research/sc001-edge-to-fill-structural-preflight-v0.1.md`;
- `docs/research/sc001-b15-p1-final-identity-route-v0.2.2-freeze-v1.json`;
- `docs/research/sc001-current-roadmap-and-stop-rules-v5.55.md`.

## 1. Purpose

Freeze the first conservative full-cycle economic burden for:

`B15-P1 INVENTORY-BACKED EFFECTIVE-TRANSFERABILITY SEGMENTATION`

before any B15 price/headroom outcome is opened.

This card does not claim profitability.

## 2. Economic cycle

Primary architecture requires pre-positioned base asset and USDT on both venues.

If venue R is rich and venue C is cheap:

1. sell pre-positioned base asset on R;
2. buy the same canonical base asset on C;
3. wait for an economically valid frozen base-transfer route C -> R to be active;
4. transfer base inventory C -> R;
5. wait for an economically valid frozen USDT route R -> C to be active;
6. transfer USDT R -> C;
7. restore the original inventory distribution.

Two market fills open the relative-value position.

The full economic cycle is not complete until base and quote inventories can be restored under the frozen route rules.

No free netting benefit is assumed in v0.1.

## 3. Reference notional

Primary structural reference:

`N_ref = 10,000 USDT per opening leg`

This reference is frozen before price outcomes.

Later capacity analysis may evaluate other notionals, but it may not replace the primary reference after seeing B15 price results.

## 4. Opening trade-fee floor

Primary execution assumption:

- rich-venue sell = taker;
- cheap-venue buy = taker;
- no maker rebate;
- no VIP discount is required for feasibility.

Per-fill fee floor:

`10 bps`

Two-fill opening fee floor:

`20 bps`

Applied fee for each venue later must be:

`max(10 bps, actual account/pair taker fee causally known at execution)`

A lower actual fee may not lower the frozen 10 bps floor.

An actual fee above 10 bps must increase the burden.

If the applicable account/pair fee cannot be established, event status is:

`FEE_RATE_UNKNOWN`

and no price-headroom PASS may be claimed.

Primary fee references retrieved 2026-09-24:

- Bybit Help Center — Spot / Trading Fee Structure: base VIP-0 crypto spot taker rate 0.1000%, with region/account caveat.
- OKX Help — Standard spot schedule: regular taker rate 0.1000% in the standard schedule, with jurisdiction/account caveat.

URLs:

- https://www.bybit.com/en/help-center/article/Trading-Fee-Structure
- https://www.okx.com/en-gb/help/advance-notice-spot-and-futures-trading-fee-adjustment

## 5. Executable-price treatment

The later primary price protocol must use simultaneous executable notional-aware prices for `N_ref`.

Preferred measure:

- sell-side executable VWAP for 10,000 USDT equivalent on the rich venue;
- buy-side executable VWAP for 10,000 USDT equivalent on the cheap venue.

Therefore bid/ask and visible L2 depth are embedded in the primary executable dislocation measure and must not be double-counted as a separate spread reserve.

Top-of-book-only headroom is diagnostic only and cannot produce a primary PASS.

## 6. Legging / latency / model reserve

Frozen additive reserve:

`10 bps`

This covers:

- non-simultaneous leg completion;
- short transport/API latency;
- discrete size/rounding;
- source-clock mismatch;
- minor execution-model error.

This reserve may later be increased by a new pre-price version.

It may not be reduced using observed B15 price/PnL outcomes.

## 7. Venue / counterparty / inventory reserve

Frozen additive reserve:

`10 bps`

This is not an estimate of exchange default probability.

It is a conservative economic reserve for:

- pre-positioned inventory on two venues;
- temporary inability to rebalance;
- venue/custody exposure during a transferability event;
- inventory-path uncertainty.

No realized absence of loss may be used to reduce it retroactively.

## 8. Capital-lock reserve

Frozen rate:

`3 bps per started 24-hour lock day`

Frozen prospective minimum horizon:

`7 days`

Entry/headroom minimum lock reserve:

`21 bps`

Realized full-cycle accounting later must use:

`max(21 bps, 3 bps × ceil(realized_lock_hours / 24))`

The lock clock starts at completion of both opening market fills.

It ends only when both base and quote inventory restoration obligations are complete.

Confirmation and transfer waiting time are included in this lock duration and are not given a second time reserve.

## 9. Base-asset restoration cost

Base rebalance direction:

`cheap venue -> rich venue`

Only frozen v0.2.2 common base representations may be used.

The selected restoration route must be ACTIVE in that direction when restoration is attempted.

Route-selection rule is non-price:

1. eligible frozen common routes only;
2. valid source fee/minimum metadata required;
3. satisfy withdrawal/deposit minimums and size constraints;
4. minimize withdrawal burden in base-asset units;
5. deterministic tie-break by canonical `network_uid`.

No route may be selected because it produced a better historical price outcome.

Withdrawal-cost reference must include every exchange-reported fixed and percentage withdrawal component when applicable.

Frozen uncertainty multiplier for the prospective burden:

`1.25 × source-reported withdrawal burden`

If no valid pre-event fee reference exists for at least one eligible planned restoration route:

`BASE_REBALANCE_COST_UNKNOWN`

and the event cannot produce a primary headroom PASS.

If the actual eventual restoration fee is higher than the prospective reference, realized economics must be revised upward.

## 10. Quote-asset restoration cost

Quote rebalance direction:

`rich venue -> cheap venue`

Only the frozen v0.2.2 USDT common-route graph may be used for cross-venue quote restoration.

Known one-sided USDT representations are not route-eligible.

Selection rule:

1. frozen common USDT routes only;
2. ACTIVE in the required direction;
3. valid fee/minimum metadata required;
4. satisfy minimums;
5. minimize fee burden in USDT;
6. tie-break by canonical `network_uid`.

Prospective uncertainty multiplier:

`1.25 × source-reported USDT withdrawal burden`

If no valid common quote route has a usable fee reference:

`QUOTE_REBALANCE_COST_UNKNOWN`

and the event cannot produce a primary headroom PASS.

## 11. Transfer-fee conversion rule for later price stage

No price conversion is performed in this card.

When the price-bearing sentinel is eventually opened:

`base_transfer_bps = 10,000 × (buffered_base_fee_units × causal_opening_base_reference_price) / N_ref`

`quote_transfer_bps = 10,000 × buffered_quote_fee_usdt / N_ref`

The base reference price must be defined by the later frozen price protocol before any B15 price outcome is inspected.

The route and fee amount themselves remain selected from non-price source state.

## 12. Minimum frozen structural floor before transfer fees

At the 10,000 USDT reference notional:

- two taker-fee floors = 20 bps;
- legging/latency/model reserve = 10 bps;
- venue/counterparty/inventory reserve = 10 bps;
- seven-day capital-lock reserve = 21 bps.

Minimum non-transfer structural burden:

`61 bps`

This is a floor.

Account/pair trading fees above the floor, longer lock duration, withdrawal fees and other explicitly observed costs can only increase it.

## 13. Minimum economic headroom reserve

Require an additional:

`10 bps`

above the frozen full-cycle burden before an event may proceed beyond a headroom sentinel.

Therefore the minimum raw executable-dislocation hurdle is:

`71 bps + buffered base-transfer cost in bps + buffered USDT-transfer cost in bps + any upward fee/lock adjustments`

No threshold may be lowered after B15 price outcomes are observed.

## 14. Minimum / capacity constraints

For the 10,000 USDT reference notional, a candidate event is structurally invalid if:

- either opening spot order cannot meet venue minimums;
- planned base restoration cannot meet withdrawal/deposit minimums;
- planned quote restoration cannot meet withdrawal/deposit minimums;
- required transfer amount exceeds known route/account limits;
- fee/minimum metadata is missing or schema-invalid.

Disposition:

`NOTIONAL_NOT_RESTORABLE`

## 15. Funding / borrow

Primary v0.1 architecture uses pre-positioned spot inventory.

Therefore:

- no borrow is assumed;
- no perpetual hedge is assumed;
- no funding benefit/cost is assumed.

If future implementation requires borrowing or a derivative hedge, it requires a new Edge-to-Fill card and a new preflight before price testing.

## 16. Source-only collector implications

The prospective non-price collector must retain, where available:

- deposit/withdraw state;
- withdrawal fee;
- percentage withdrawal fee;
- minimum withdrawal;
- minimum deposit;
- confirmation metadata;
- source timestamps;
- normalized route state.

These fields are economic-source metadata, not price outcomes.

Identity/universe membership remains frozen and may not depend on current ON/OFF transfer state.

## 17. Structural classification

Current classification:

`UNKNOWN_NEEDS_NON_ALPHA_DATA / SOURCE_COLLECTOR_ELIGIBLE_IF_PREFLIGHT_PASS`

Reason:

- independent economic mechanism = PASS;
- initial market fills = only 2;
- explicit minimum cost floor is now frozen;
- full restoration is modeled;
- price scale remains unopened;
- outage frequency/duration remains unknown;
- route fee distributions remain to be collected prospectively.

## 18. Hard stop

Do not open B15 prices yet.

Required next order:

1. run Full-cycle Edge-to-Fill structural preflight;
2. if PASS, freeze the B15 15-second non-price collector design;
3. launch prospective source collector only after a separate collector implementation/self-test gate;
4. collect source-only opportunity-rate evidence;
5. only then freeze the first price/headroom protocol.

No rescue tuning.
