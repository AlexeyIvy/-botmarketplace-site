# SC001 / B15-P1 — dialog handoff v6.5 — 2026-09-24

Latest research state:

`B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_FREEZE_PASS`

v0.2.2 final identity/route state is frozen with zero review and zero unresolved identity rows.

## Final state

- total assets = 201
- admitted = 192
- review = 0
- excluded = 9
- canonical representations = 207
- directed identity edges = 414
- asset common representations = 52
- USDT common representations = 12
- quote_review = false
- unresolved rows = 0
- alias collisions = 0
- disposition mismatches = 0

## Exact replay

- bundle: `bundle_20260923T213214Z_c876cafb`
- SHA256: `7eaec6bf2a98a0d2ac042358c5482aab681e83c77e1471f50af35db75b360ff7`
- job: `job_20260923T214214Z_b1901454`
- status: `B15_P1_V022_EXACT_REPLAY_PASS`
- manifest SHA256: `ad842a5f7be42c7c4cae6ce13b91846de7e17e17cb06cf1152aa4f69538c1f7b`

## Final freeze-preflight

- bundle: `bundle_20260923T214432Z_1d5f1a1b`
- SHA256: `79974e03250cc36f6516e721a1a2d9a94cbccda3c17c2543458cd6213b260fe2`
- job: `job_20260924T074028Z_af838b48`
- status: `B15_P1_V022_FINAL_IDENTITY_ROUTE_FREEZE_PREFLIGHT_PASS`
- freeze candidate SHA256: `1519940e2580fc246d745e11cb06dda564b83f6b7cb689583eb2d1c386c8fabd`
- freeze file map SHA256: `ce20255a4d94464b34f3e778f723d4ebf080faaadb1fd8489790692692f769c9`

## Former quarantine

All previous holds are resolved:
- GRAM
- QTUM
- STX
- XLM
- USDT / CORN
- USDT / Tempo

CORN and Tempo are classified one-sided and do not create cross-venue routes.

## Mandatory next step

`CHECKPOINT_BACKUP_AFTER_V022_FINAL_IDENTITY_ROUTE_FREEZE`

Collector and price/PnL remain unauthorized until the new checkpoint archive and restore verification PASS are recorded.

Do not modify the frozen v0.2.2 registries or dispositions in place.
