# SC001 Current Roadmap and Stop Rules v5.165

Date: 2026-09-27
Status: **B15-P2 EXACT 94-EVENT SOURCE SET FROZEN / ANNOUNCEMENT-BODY SEMANTIC AUDIT NEXT**

Supersedes:
`sc001-current-roadmap-and-stop-rules-v5.164.md`

## Exact event-set freeze complete

The B15-P2 Bybit source-only census result has been promoted byte-for-byte from the VPS host result into GitHub.

Promoted source result:

`docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_result.v0.1.1.json`

SHA256:

`c28aeb2b1ac0a23fb0e4420ced943fd619dd0a60e3fdcf5820299579cb94206c`

Freeze manifest:

`docs/research/artifacts/b15-p2-source-census-v0.1.1/20260927T193110Z/source_census_event_set_freeze.v0.1.json`

Freeze-manifest SHA256:

`81952c83e7397481035cc00354388dfe3470ad17993c6e80665a7d376be907ed`

Deterministic frozen event-set digest:

`1063695ec003a0d6789270659822f50577e6a0f07059d88ac03a5be4288ed1a2`

## Frozen evidence identity

- venue: BYBIT
- exact in-scope events: **94**
- event identity:
  `BYBIT x EXACT_USDT_PERPETUAL_SYMBOL x DELIVERY_TIME`
- announcement coverage: **100%**
- represented delivery months: **9**
- source-integrity issues: **0**

Each event preserves:
- exact USDT perpetual symbol;
- deliveryTime;
- first causal notice timestamp;
- last causal pre-event notice timestamp;
- notice count;
- lead hours;
- official announcement URL identities.

## Research firewalls

The frozen artifact confirms:

- price accessed: false;
- basis calculated: false;
- PnL calculated: false;
- event ranked by outcome: false.

No price outcome is authorized by this freeze.

## Promotion-wrapper diagnostic

During the no-network freeze wrapper, root-owned execution of:

`git -C /var/lib/botmarket-github-control/repo status`

printed Git's `detected dubious ownership` protection because the dedicated control clone is owned by `botmarket-github`.

Due to the command being evaluated inside command substitution, that diagnostic did not abort the wrapper.

This did NOT corrupt promotion:
- the source preflight passed;
- the promoted result SHA matches the host source SHA;
- the freeze manifest references that exact SHA;
- GitHub Control independently sees both promoted files.

The lesson is prospective: future host wrappers must perform repository-cleanliness checks as the repository owner or use a non-git filesystem safety check; they must not rely on a root `git status` command substitution that can fail open.

No `safe.directory` global exception is required for this completed promotion.

## Strategy-manager consequence

The exact-event freeze is evidence-preservation work and does not itself change the research strategy.

Therefore:

`NO STRATEGY REVIEW TRIGGER`

The next mandatory Strategy Manager gate remains before any B15-P2 price outcome.

## Next allowed stage

`ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_ONLY`

Purpose:
classify the frozen event set using official announcement wording only.

The semantic audit may inspect:
- forced-close / automatic-closure wording;
- settlement / index-window wording;
- funding treatment;
- postponements / revisions;
- explicit delisting/settlement timestamps;
- exceptions or event-specific rule variants.

Still forbidden:
- affected-contract price;
- external-reference price;
- index values;
- basis/spread;
- returns;
- PnL;
- event ranking by outcome;
- horizon selection from price outcomes.

Before any later price outcome stage, the binding governance still requires:
- structured mechanism fingerprint;
- mechanism-timescale;
- Edge-to-Fill;
- two-mode Minimum Viable Horizon;
- capital-time economics.

## Other branch states

B15-P1:
W1 accumulation / operational freeze unchanged.

B14-A:
`B14A_P0_DEFER_DATA` retained.

B13-C:
terminal S0 / RB021 retained; no same-evidence rescue.

B14-B:
terminal / RB022 retained; no same-window rescue.

## Next state

`DESIGN_AND_FREEZE_B15P2_ANNOUNCEMENT_BODY_SEMANTIC_AUDIT_NO_PRICE`
