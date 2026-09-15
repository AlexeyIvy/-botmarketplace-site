# SC001-E006 — Implementation Preflight Specification v1.0

Date: 2026-09-15  
Status: **FROZEN PRE-ALPHA IMPLEMENTATION SPEC**  
Protocol: `docs/research/sc001-e006-spot-perp-basis-convergence-executable-protocol-v1.0.md`

## 1. Purpose

Prove that the E006 implementation reproduces the frozen protocol exactly before any real-data SPOT/SWAP price comparison, basis, convergence, return or P&L is emitted.

Only exact terminal token `E006_PREFLIGHT_PASS` authorizes DEV-DISCOVERY.

## 2. Real-data output firewall

During preflight on real March data the implementation may output only:

- file identities/hashes;
- row/timestamp counts;
- 10-second grid counts;
- paired-valid-window counts;
- six-hour-baseline eligibility counts without basis values;
- trigger-state machine transition counts on synthetic fixtures only;
- resource/invariant facts.

It must not output/persist real-data:

- SPOT or SWAP prices/VWAP;
- basis values;
- baselines;
- dislocations;
- trigger directions;
- entry/exit prices;
- returns/gross edge/P&L;
- latency performance.

## 3. Identity requirements

Record:

- Git commit;
- SHA256 of config, engine and preflight runner;
- Python/OS/timezone;
- input SPOT/SWAP manifests and exact hashes/bytes;
- protocol/preflight versions.

Discovery must later refuse to run unless exact config/engine SHA256 match this PASS report.

## 4. Synthetic tests

At minimum test:

1. `[t-10s,t)` excludes trade at t and includes trade exactly at t-10s;
2. size-weighted VWAP formula;
3. perp contract-count weighting is ordinary within-leg VWAP;
4. basis formula sign;
5. current basis excluded from prior 6h baseline;
6. 2,160 scheduled points and 2,052 minimum valid observations;
7. ordinary median semantics for even samples;
8. previous invalid grid point blocks trigger;
9. strict below-to-at/above +50 crossing only;
10. frozen baseline does not move after trigger;
11. opposite/negative sign cannot trigger primary;
12. entry target is decision +500 ms;
13. proxy trade exactly +5,000 ms tolerance is eligible, later is not;
14. pair open timestamp is max of leg entry timestamps;
15. incomplete one-leg entry yields no gross observation;
16. convergence exit at frozen-baseline dislocation <=+10;
17. time exit at first 10-second boundary >= open+30m;
18. convergence exit precedes later time exit;
19. exit proxy uses +500 ms and inclusive 5s tolerance;
20. incomplete exit locks day;
21. no overnight carry and 23:29 entry cutoff;
22. 10-minute cooldown;
23. fifth daily entry decision blocked;
24. one-pair invariant;
25. paired gross-edge formula for long spot/short perp;
26. equal scaling of all prices leaves basis/returns invariant where mathematically applicable;
27. 1,000/2,000 ms stresses reuse primary signal and exit-decision events;
28. diagnostic mode blocked before primary verdict;
29. Confirmation blocked without exact Discovery PASS token;
30. TFI/FLOW_IMPULSE/E004 features absent.

## 5. Real-data no-alpha dry run

On 2024-03-01..20:

- verify all required local SPOT/SWAP archive identities;
- reconstruct only qualified UTC days;
- parse price/size only inside a suppression boundary sufficient to verify finite/positive values and window availability;
- do not serialize or print prices;
- count scheduled 10-second boundaries;
- count valid paired 10-second windows;
- count boundaries with enough prior valid observations for six-hour baseline;
- verify first possible baseline eligibility cannot precede 06:00 UTC on March 1;
- verify no protected dates after March 21 are read;
- verify March 21 remains performance-excluded;
- verify output tree contains no forbidden price/basis/return fields.

The dry run may not compute real-data trigger crossings or any basis values. If implementation architecture cannot separate availability counting from basis calculation, preflight FAILs.

## 6. Resource gates

On qualified VPS:

- peak RSS <6 GiB;
- free disk reserve >=10 GiB after inputs;
- deterministic rerun identities;
- atomic output writes;
- nonzero exit on malformed/inconsistent data.

## 7. PASS rule

`E006_PREFLIGHT_PASS` only if:

- all synthetic tests pass;
- identity/hash checks pass;
- real-data no-alpha dry run passes;
- forbidden-output scan is clean;
- firewalls/resources/invariants pass;
- report records exact engine/config SHA256;
- no real-data basis/return/P&L/alpha is calculated.

Otherwise `E006_PREFLIGHT_FAIL`; Discovery remains blocked.

## 8. Fix boundary

Preflight failures may justify only software/data-audit corrections. They may not alter the frozen financial protocol, trigger/baseline/exit/economics gates. Any implementation correction receives a new code identity and a full preflight rerun.
