# DSL ↔ Graph Bidirectional — Feasibility Spike

**Status:** Spike complete (written note)
**Date:** 2026-04-12
**Author role:** Senior Software Engineer (research-only output)
**Gate satisfied:** `docs/24 §8.7` — "The spike produces a written feasibility note"
**Change type:** Docs-only. No code changes, no schema changes, no task pack commitment.

---

## 1. Purpose

`docs/24-lab-post-phase-5-roadmap.md §8.7` requires a written feasibility spike before any implementation of reverse compile (DSL → graph) can be scheduled. Phase 3A and Phase 6 acceptance — the two preconditions — are now both met. This document closes the third precondition.

**Scope:**
- Inventory what information flows forward (graph → DSL) and quantify what is lost
- Identify the structural constraints that make reverse compile non-trivial
- Rank feasibility and recommend whether a task pack should be created

**Out of scope:**
- Implementation design, TypeScript signatures, or migration plans
- Decision on whether to execute — this document is research input, the execution decision is the project owner's call
- Round-trip test fixtures (deferred to implementation task pack if one is created)

---

## 2. Current forward pipeline (graph → DSL)

**Entry point:** `apps/api/src/lib/compiler/index.ts` — `compileGraph(graphJson, strategyId, name, symbol, timeframe): CompileResult`

**Input shape** (`apps/api/src/lib/compiler/types.ts`):
```ts
interface GraphJson {
  nodes: Array<{ id: string; data: { blockType: string; params: Record<string, unknown> } }>;
  edges: Array<{ id: string; source: string; target: string; sourceHandle?: string|null; targetHandle?: string|null }>;
}
```

**Output shape:** `CompileResult.compiledDsl` — flat JSON object per `docs/10-strategy-dsl.md §1`:
```
{ id, name, dslVersion, enabled, market, timeframes, entry, exit, risk, execution, guards, privateData? }
```

**Algorithm** (`graphCompiler.ts:147-305`):
1. `buildContext(graph)` — index nodes by id, group by blockType, index incoming edges
2. Validate required block set (candles, entry, SL/TP) via handler-level `validate(ctx)`
3. For every block instance, run its handler's `extract(ctx)` which returns DSL fragments (`indicators | risk | side`)
4. Choose v1 vs v2 entry mode (fixed-side vs adaptive `sideCondition`)
5. Merge fragments into the declarative DSL skeleton with defaults (market, execution, guards, risk)
6. Final JSON-schema validation

**Preserved in DSL:**
- `nodeId` is carried through to indicator/signal/risk entries (verified: `blockHandlers.ts` — `nodeId: n.id` on every `extract()` return; 15+ call sites). This is important — it means forward compile is not entirely amnesic about graph identity.

**Discarded during forward compile:**
- Node coordinates (`position.x`, `position.y`) — not even present in `GraphJson`; they live in `useLabGraphStore.nodes[].position` (React Flow state), never sent to the compiler
- Edge endpoints for multi-output blocks — only consumed edges are observed; blocks with three outputs (e.g., MACD: `macd`, `signal`, `histogram`) appear in DSL as a single `{type:"macd", fastPeriod, slowPeriod, signalPeriod}` entry with no marker for which specific output port(s) downstream nodes were consuming
- Orphan nodes — any node unreachable from `candles → … → entry/exit` is silently dropped. No diagnostic, no trace in DSL
- Edge handles (`sourceHandle`, `targetHandle`) — accepted on input for validation, not written to DSL output
- Parameter aliases — e.g., `length` vs `period` are normalized at `graphCompiler.ts:92-93` to `length`; reverse compile would need to know which alias the original block used

---

## 3. Reverse direction — what a DSL→Graph pass would need

Given a DSL object, produce a `{ nodes, edges, positions }` triple suitable for the Build canvas. Four sub-problems, roughly independent:

### 3.1 Node materialization
Parse the DSL and emit one node per declared indicator, signal, risk block, and the implicit `candles` + `enter_long/short` + `stop_loss` + `take_profit` blocks. For all 33 supported `blockType`s, a handler table analogous to `blockHandlers.ts` would need an inverse: given a DSL fragment, produce a `{ id, data: { blockType, params } }` tuple.

**Difficulty:** Moderate. 1:1 mapping exists for most blocks since `nodeId` is preserved. Only real friction is parameter alias recovery — `blockDefs.ts` is the source of truth for which alias each blockType expects.

### 3.2 Edge synthesis
DSL is declarative: `entry.signal.fast` is `{ blockType: "SMA", nodeId: "n3", length: 20 }`. To rebuild the graph, the reverse compile must emit:
- Edge `candles → SMA_n3`
- Edge `SMA_n3 → cross_signal.a`
- And do the same for every indicator, risk block, and entry/exit wiring

**Difficulty:** Moderate-to-high. The pattern is canonical for the happy path (linear pipeline per indicator), but cross-references (two indicators sharing a `constant` block, a single indicator feeding both signal inputs) need unambiguous recovery rules. Without invariants, multiple valid edge topologies can satisfy the same DSL.

### 3.3 Multi-output port routing
MACD has three outputs but DSL only hints which one the signal consumes via proximity in the JSON tree. Restoring the graph requires deciding: do we wire all three outputs to phantom downstream nodes, only the used one, or mark it ambiguous? Same for Bollinger Bands (upper, middle, lower), stochastic-family blocks, and any other multi-output indicator.

**Difficulty:** Moderate. Resolvable by fiat (wire only the output the DSL proves was consumed; leave the rest dangling) but this makes round-trip non-identity: the original graph's layout with three edges collapses to one edge on reverse, and a re-compile still produces the same DSL. Acceptable if "identity" is defined as DSL-level, not canvas-level.

### 3.4 Layout reconstruction
The `position.x/y` are permanently lost. Three options:
- **Reset layout** — run dagre (or similar) over the reconstructed graph. Deterministic, ugly-but-readable, does not preserve user's mental model
- **Retrieve from history** — if the DSL came from a `StrategyGraphVersion`, the associated `GraphJson` snapshot (if persisted with positions) could supply them. Requires schema confirmation — `apps/api/prisma/schema.prisma` would need verification that `StrategyGraphVersion.graphJson` includes positions (currently unclear whether persistence strips them)
- **Accept layout loss** — mark the reconstructed graph as "imported" and force the user to re-arrange

**Difficulty:** Low if "reset layout" is acceptable. High if user expects their canvas arrangement preserved across DSL-edit → reload.

---

## 4. Round-trip invariants

A useful frame: round-trip fidelity at two levels.

| Level | Definition | Achievable? |
|---|---|---|
| **DSL identity** | `compile(decompile(dsl)) === dsl` | **Yes, with discipline** — requires canonical ordering, alias normalization, orphan exclusion rules |
| **Graph identity** | `decompile(compile(graph)) === graph` | **No** — layout, orphans, unused outputs are lost in forward direction and cannot be recovered from DSL alone |

DSL identity is the realistic target. Graph identity is not — it would require either (a) augmenting DSL with hidden metadata (violates declarativeness), or (b) a separate graph snapshot store (orthogonal to DSL).

---

## 5. Feasibility verdict

**Ranking:** **(c) Hard — 5-10 focused sessions, disciplined round-trip test coverage required.**

Justification:
- All 33 block types need inverse handlers (1-3 sessions of mechanical work)
- Edge synthesis rules for multi-output blocks and cross-references need explicit design (1-2 sessions)
- Layout strategy decision (reset vs retrieve from history) (0.5-1 session; hinges on schema confirmation)
- Round-trip test suite with golden graphs covering every canonical pattern + edge cases (1-2 sessions)
- Handler drift risk: forward-compile handlers already exist; the inverse must stay in sync. Without shared source-of-truth, additions to `blockHandlers.ts` can silently break reverse compile. This is a maintenance burden, not a one-off implementation cost.

**Not (a) or (b).** A minimal prototype that handles only linear graphs (candles → one indicator → signal → entry) is achievable in 2-3 sessions but would not cover real user strategies (which regularly combine 3-5 indicators with cross-signals).

**Not (d) outright unfeasible.** The DSL preserves enough identity via `nodeId` to make reverse compile tractable. The issue is scope, not architecture.

---

## 6. Options with trade-offs

### Option A — Full bidirectional, all 33 blocks, reset layout
- **Effort:** 5-10 sessions
- **Value:** Complete feature parity with `docs/23 §9.3` intent
- **Risk:** High maintenance cost — inverse handler table must evolve in lockstep with forward handlers
- **User story covered:** "I pasted DSL from docs, now I see it as a graph"; "I exported DSL, edited it externally, re-imported"

### Option B — Scoped reverse, canonical patterns only
- **Effort:** 2-3 sessions
- **Scope:** Linear graphs with ≤1 indicator per signal input, no orphans, no unused multi-outputs
- **Value:** Covers ~60% of user graphs in Lab templates (`apps/web/src/app/lab/templates.ts` — 5 templates, all canonical)
- **Risk:** Users hit "this DSL is not reversible" errors on any non-trivial strategy; support burden
- **User story covered:** Tutorial DSL snippets, starter templates — not user-authored strategies

### Option C — Graph snapshot retrieval (skip reverse compile entirely)
- **Effort:** 1-2 sessions
- **Scope:** When a DSL is associated with a `StrategyGraphVersion`, load its persisted `graphJson` directly. Do not reverse compile at all.
- **Value:** Zero lossiness for the persisted-version case, which is the common case (user compiled, now wants to re-open)
- **Risk:** Does not cover the "paste DSL from docs" case at all. Schema verification required (does `StrategyGraphVersion.graphJson` persist positions?)
- **User story covered:** Governance provenance flows; re-opening a compiled version. **Does not** cover external DSL import.

### Option D — No bidirectional; keep DSL preview read-only
- **Effort:** 0 sessions
- **Value:** Clean separation — graph is source of truth, DSL is compiled artifact. No drift risk.
- **User story covered:** Status quo. DSL users who want to author in text remain unserved.

---

## 7. Recommendation

**Default recommendation: Option D (no bidirectional) unless a concrete user-facing driver appears.**

Reasoning:
- No user story in roadmap (`docs/24`, `docs/23`, `docs/22`) explicitly demands reverse compile. `docs/23 §9.3` lists it as "optional … where feasible", not a requirement.
- The most valuable partial win — re-opening a persisted compiled version as a graph — is already covered by the existing `StrategyGraph` + auto-save flow. Users do not in practice open DSL and ask "make this a graph"; they open a graph, compile, and view the DSL read-only.
- External DSL import is a niche workflow (copy-paste from docs, external editor) that does not justify 5-10 sessions of work plus permanent maintenance burden on every new block type.

**Conditional recommendation: Option C if and only if** a concrete product requirement surfaces for "re-open compiled version as graph from DSL alone" (i.e., without the associated `graphJson` snapshot). Even then, Option C is cheaper than A and delivers the exact user value.

**Not recommended: Option B.** It is a "demo-grade" scope that will generate support churn the moment real users try to round-trip their own strategies. Prefer D (explicit no) over B (silent partial).

---

## 8. What this spike unblocks / blocks

| Item | Status after this spike |
|---|---|
| `docs/24 §8.7` third gate condition (written spike) | ✅ Satisfied |
| DSL↔graph task pack creation | **Not recommended at this time.** Gate conditions 1 and 2 are met; gate condition 3 is met (this document) but its verdict is "do not create task pack until a concrete user driver surfaces." |
| Future re-evaluation trigger | If ≥3 user requests surface for DSL import, or if a Stage-7+ product feature requires DSL authoring outside the canvas, revisit this spike. |

**Explicit decision required from project owner:** Accept Option D (this spike's default recommendation) OR green-light Option C with schema verification as a precondition. Option A and Option B are not recommended.

---

## 9. Evidence trail

- Forward compile algorithm: `apps/api/src/lib/compiler/graphCompiler.ts:147-305`
- Handler table: `apps/api/src/lib/compiler/blockHandlers.ts` (33 block types, all lines carrying `nodeId: n.id` — verified via grep: 15+ occurrences)
- GraphJson type (no positions): `apps/api/src/lib/compiler/types.ts:10-40`
- Block definitions (source of truth for block metadata): `apps/web/src/app/lab/build/blockDefs.ts`
- DSL block mapping table: `docs/10-strategy-dsl.md §9.2`
- Spike precondition: `docs/24-lab-post-phase-5-roadmap.md §8.7`, lines 414-429
- Forward compile tests (no round-trip coverage): `apps/api/tests/lib/graphCompiler.test.ts`
- Templates used to estimate canonical coverage: `apps/web/src/app/lab/templates.ts` (5 flagship templates, all linear)

---

## 10. Cross-references

- `docs/23-lab-v2-ide-spec.md §9.3` — original "optional … where feasible" clause
- `docs/24-lab-post-phase-5-roadmap.md §8.7` — spike gate this document closes
- `docs/10-strategy-dsl.md §9.2` — block-to-DSL mapping (forward)
- `docs/07-data-model.md` — `StrategyGraphVersion.graphJson` schema (requires verification for Option C)
