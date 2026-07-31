# Canonical Migration & Legacy Pruning Plan
**Experience Compass — Stage 1 (Guided Composition / Organizing Thought)**
Status: READ-ONLY ENGINEERING ROADMAP. No production code is changed by this document.
Date: 2026-06. Author: engine-migration planning pass.
Scope: FULL migration to the Canonical Paragraph Curriculum, phased so that **Phase P0 is
independently executable now**, later phases gated on additional canonical authoring.

---

## 0. How to read this document

This document has two audiences.

- **Strategic reader** (product / new engineer): read §1–§5. These explain, from zero, what
  Compass does, what is being replaced, the target end-state, the order of migration, and *why*
  that order is forced by dependencies. No code knowledge required.
- **Execution agent** (implements the migration): read §6 (Deliverable A — disposition table),
  §7 (Deliverable B — file/symbol pruning map), §8 (Deliverable C — staged plan), §9
  (Deliverable D — missing canonical authoring that blocks later phases), §10 (Deliverable E —
  validation corpus), §11 (risks/rollback), and the **Appendix** (exact symbol names + sequence).

The five requested deliverables are §6 (A), §7 (B), §8 (C), §9 (D), §10 (E). The dependency graph
is §4. Everything else is framing so the plan is self-contained.

---

## 1. Strategic Overview — what Compass is and why we are migrating

### 1.1 What Compass does (one pass, no prior knowledge assumed)
Compass is an instructional system, not a writing assistant. A student submits a piece of writing
(currently a single paragraph). Each turn, Compass does exactly two LLM calls:

1. **SELECT** — an internal analysis (never shown to the student) that chooses the ONE writing
   *structure* with the greatest developmental leverage right now (the "One Thing Rule"). It never
   lists errors; it identifies the single highest-leverage thing to teach next, or `null` if the
   writing is already solid.
2. **TEACH** — a student-facing dialogue turn that teaches THAT one structure and invites the
   student to build it themselves. Compass never rewrites, drafts, or supplies the answer
   (anti-coauthoring is absolute).

This is the FROZEN **Decision Engine V2** flow. The migration must NOT change this two-step shape,
the one-target rule, the anti-coauthoring boundary, or the durable background-processing transport.

### 1.2 Where the knowledge lives today (the "hybrid state")
There are two competing sources of writing knowledge in the engine:

- **LEGACY knowledge** — `MINIMAL_OBJECTS` in `compass_structure_engine.py`: 11 hand-written
  instructional objects (Reader Orientation, Central Claim, Paragraph Main Point, Definition,
  Evidence, Explanation, Elaboration, Transition, Paragraph Closure, Conclusion, Sentence
  Construction), each with 5 generic fields. A fixed `PRIORITY_ORDER` list ranks them, and a large
  hand-authored selector prompt (`_SEL_SYS`) encodes generic composition heuristics
  ("a thesis must be contestable", "teach evidence only after the claim", etc.).

- **CANONICAL knowledge** — `compass_curriculum.py` + `canonical_models/*.json`: 5 rigorously
  authored PRIMARY structures (Opening, Thesis, Elaboration, Evidence / Example, Conclusion), each
  with 9 authoritative fields (definition, function, structural_dependencies,
  structural_requirements, developmental_variations, developmental_sufficiency,
  discovery_instruction, rescue_instruction, observable_decision_questions). These are inserted
  verbatim, never invented, and explicitly REJECT the generic rules the legacy layer assumes.

Today the two are wired in a deliberately partial way:

| Concern | Current source |
|---|---|
| WHICH structure to teach (selection) | **100% LEGACY** — `PRIORITY_ORDER` + `_SEL_SYS` + `MINIMAL_OBJECTS` digest |
| Learner-STATE judgment (missing/partial/misleading/present) | **LEGACY** — the selector LLM decides |
| Developmental SUFFICIENCY (reached / continue) | **LEGACY** — the selector LLM decides |
| WHAT to teach (dialogue CONTENT) | **CANONICAL** for structures mapped to a ready model, else LEGACY (`_resolve_teaching_source`) |
| Dialogue FORM (first-turn / continuation / discovery / rescue voice) | GENERIC prompt `_DLG_SYS` (structure-agnostic) |
| Closure (no-target turn) | GENERIC prompt `_CLOSURE_SYS` |
| Teacher Review fixtures | LEGACY / generic composition terms (`teacher_review_fixtures.json`) |
| Interim "noticing" cards | GENERIC composition terms (`NOTICING_SYSTEM_MESSAGE` in server.py) |

The mapping used by `_resolve_teaching_source` (`_LEGACY_TO_CANONICAL`):
`Central Claim→Thesis`, `Paragraph Main Point→Thesis`, `Reader Orientation→Opening`,
`Evidence→Evidence / Example`, `Elaboration→Elaboration`, `Paragraph Closure→Conclusion`,
`Conclusion→Conclusion`. **`Explanation` is intentionally NOT mapped** (falls back to legacy).
`Definition`, `Transition`, `Sentence Construction` have no canonical model at all.

### 1.3 Why the hybrid state is unstable (the core problem)
The selector picks a target using the LEGACY priority order and LEGACY definitions, but the
dialogue then teaches from a CANONICAL model whose theory **contradicts** the basis on which the
target was selected. The two most dangerous contradictions:

1. **Priority inversion.** Legacy ranks `Evidence (5) > Explanation (6) > Elaboration (7)`.
   The canonical curriculum makes **Elaboration the PRINCIPAL developmental work of the paragraph**,
   with Evidence *subordinate to* Elaboration. So the selector can pick "Evidence" as highest-
   leverage while the canonical theory says Elaboration should have come first. The student is
   taught canonical Elaboration-flavored content under a target chosen by an inverted priority.

2. **Rejected generic rules re-entering through selection.** `_SEL_SYS` still tells the selector a
   Central Claim "counts as PRESENT only when it takes a **contestable** position." The canonical
   Thesis model explicitly PROHIBITS the universal "must be contestable" rule. So selection can
   mis-judge sufficiency on grounds the canonical curriculum forbids.

Until selection, state-judgment, and sufficiency are also sourced from canonical structures, the
engine's *decision* and its *teaching* rest on different, conflicting theories. **That is the
reason for this migration.** The goal is a single authoritative source of truth.

---

## 2. Final Target Architecture (the end-state we are migrating toward)

At completion, the engine's instructional knowledge is sourced **entirely** from the Canonical
Curriculum for everything it can cover, with an explicit, authored home for everything it cannot
yet cover. Concretely:

- **SELECT** operates over the **5 canonical PRIMARY structures** (+ authored SUBORDINATE
  structures once modeled). The priority/leverage decision is driven by a **canonical
  cross-structure leverage procedure** (see §9, Gap-4) rather than the hand-written `PRIORITY_ORDER`
  and `_SEL_SYS` heuristics. Selection uses each structure's `structural_dependencies`,
  `observable_decision_questions`, and `developmental_variations` as its evidence.
- **STATE + SUFFICIENCY** judgments come from each structure's `developmental_variations` and
  `developmental_sufficiency` fields, not from generic selector heuristics.
- **TEACH** content is 100% canonical (already true for mapped structures). Discovery/rescue voice
  is anchored to each structure's `discovery_instruction` / `rescue_instruction`. `_DLG_SYS` keeps
  only delivery *mechanics* (first-turn shape, tone, anti-coauthoring, stop rule).
- **CLOSURE** derives from canonical Conclusion + `developmental_sufficiency`.
- **TEACHER REVIEW** fixtures + **NOTICING** cards are re-anchored to canonical terminology.
- **LEGACY `MINIMAL_OBJECTS`, `PRIORITY_ORDER`, `_SEL_SYS` heuristics, `_LEGACY_TO_CANONICAL`
  bridge, and `_priority_digest`** are pruned once parity is proven.
- **Explanation**, **Definition**, **Transition**, **Sentence-level** instruction each have a
  *decided* canonical home (either an authored subordinate model, a placement within a primary, or
  an explicit out-of-scope declaration) — no silent legacy fallback remains.

Preserved unchanged end-to-end: the two-call SELECT→TEACH shape, the One-Thing Rule, the
authoritative-decision-then-fixed-target contract, anti-coauthoring, DISCOVERY/RESCUE modes,
FIRST-TURN vs CONTINUATION logic, the durable background transport, teacher override, audit/state
persistence, and the `COMPASS_REASONING_MODE=exhaustive` rollback path.

---

## 3. Design principles that govern every phase

1. **The FROZEN flow is inviolable.** No phase changes the SELECT→TEACH two-call shape, the
   one-target contract, or anti-coauthoring. Migration replaces *knowledge sources*, not the flow.
2. **Never invent canonical theory.** If a decision requires knowledge not present in a supplied
   canonical model, that is an *authoring task for the curriculum authority* (a Gap in §9), not
   something the engine or the execution agent may fabricate.
3. **Parity before pruning.** Legacy code is DELETED only after a validation run proves the
   canonical path produces equivalent-or-better instructional decisions (see §10).
4. **One reversible change at a time.** Every phase has an explicit rollback (feature flag, kept
   legacy symbol, or env switch) and is validated before the next phase begins.
5. **No orphaned fallbacks.** A structure is only removed from the legacy layer once it has a
   decided canonical home. "Falls back to legacy" is never an acceptable end-state.

---

## 4. Dependency Graph — why the phases are ordered as they are

```
                 ┌─────────────────────────────────────────────┐
                 │  Canonical Curriculum (5 primaries authored)  │  ← DONE (Phase 1)
                 └───────────────────────┬─────────────────────┘
                                         │  provides the vocabulary,
                                         │  requirements & dependencies
                                         ▼
        ┌────────────────────────────────────────────────────────┐
        │  P0  CANONICAL SELECTION (primaries)                     │  ← EXECUTABLE NOW
        │  select_structure ranks the 5 canonical primaries        │
        │  using structural_dependencies + decision questions      │
        └───────────────────────┬────────────────────────────────┘
                                 │  a canonically-chosen target is the
                                 │  precondition for canonical judgement
                                 ▼
        ┌────────────────────────────────────────────────────────┐
        │  P1  CANONICAL SUFFICIENCY & STATE JUDGEMENT             │
        │  status + developmental_sufficiency sourced from the     │
        │  chosen structure's canonical fields, not _SEL_SYS       │
        └───────────────────────┬────────────────────────────────┘
                                 │  dialogue must teach to the SAME
                                 │  canonical basis the decision used
                                 ▼
        ┌────────────────────────────────────────────────────────┐
        │  P2  CANONICAL DIALOGUE FORM                             │
        │  discovery/rescue voice anchored to canonical            │
        │  instructions; _DLG_SYS keeps mechanics only             │
        └───────────────────────┬────────────────────────────────┘
                                 │  teacher-facing artifacts must reflect
                                 │  the now-canonical reasoning
                                 ▼
        ┌────────────────────────────────────────────────────────┐
        │  P3  TEACHER REVIEW + NOTICING RE-ANCHORING             │
        │  fixtures & interim cards use canonical terms            │
        └───────────────────────┬────────────────────────────────┘
                                 │  legacy is now unreferenced for the
                                 │  five primaries → safe to delete
                                 ▼
        ┌────────────────────────────────────────────────────────┐
        │  P4  LEGACY PRUNING (primaries)                         │
        │  delete MINIMAL_OBJECTS primaries, PRIORITY_ORDER,       │
        │  _SEL_SYS heuristics, _LEGACY_TO_CANONICAL bridge        │
        └───────────────────────┬────────────────────────────────┘
                                 │  requires NEW canonical authoring
                                 │  (blocked — see §9 Gaps 1,2,3,5)
                                 ▼
        ┌────────────────────────────────────────────────────────┐
        │  P5  SUBORDINATE & SCOPE RESOLUTION                     │
        │  author Definition/Transition/Qualification models,      │
        │  decide Explanation placement, decide sentence-level     │
        │  scope, resolve Paragraph-Main-Point→Thesis unity        │
        └────────────────────────────────────────────────────────┘
```

### 4.1 Why each edge exists (the causal justification)

- **Curriculum → P0.** Selection can only rank canonical structures once those structures exist
  and expose the fields selection needs (`structural_dependencies`, `observable_decision_questions`,
  `developmental_variations`). They do (Phase 1 complete), so P0 is unblocked.
- **P0 → P1.** Sufficiency and state ("has the Thesis reached developmental sufficiency?") are
  defined *per structure* in canonical fields. You cannot source a canonical sufficiency judgment
  until the *target* is chosen canonically; otherwise you'd be judging a legacy-chosen target
  against canonical criteria — the very contradiction we are removing. So sufficiency migration
  must follow selection migration.
- **P1 → P2.** The dialogue must teach to the same canonical basis the decision was made on. If the
  decision layer already judges canonically but the dialogue voice is still generic, the two can
  drift (e.g. the decision says "Elaboration is principal here" but the generic voice reaches for
  evidence-first framing). Aligning the dialogue voice AFTER the decision is canonical keeps them
  coherent. (Note: dialogue CONTENT is already canonical; P2 only migrates the discovery/rescue
  *voice anchoring*.)
- **P2 → P3.** Teacher Review and the noticing cards are *descriptions of the engine's reasoning*.
  Re-anchoring them to canonical terms is only meaningful once the reasoning they describe is
  itself canonical (P0–P2). Doing it earlier would describe a hybrid reasoning that is about to
  change.
- **P3 → P4.** Legacy symbols can only be deleted once **nothing** references them for the five
  primaries: not selection (P0), not sufficiency (P1), not dialogue (P2), not teacher artifacts
  (P3). P4 is pure removal; it must come last among the primary-facing phases.
- **P4 → P5 (blocked edge).** Full pruning of the legacy layer cannot complete while
  `Explanation`, `Definition`, `Transition`, and `Sentence Construction` still have *only* a legacy
  home. Deleting them before a canonical decision exists would drop live instruction. P5 therefore
  requires NEW canonical authoring (Gaps 1,2,3,5 in §9) and is **not executable until the
  curriculum authority supplies those decisions.** P4 can delete the FIVE PRIMARIES' legacy
  objects; it cannot delete the subordinate/sentence-level legacy objects — those wait for P5.

### 4.2 Unresolved canonical authoring that BLOCKS later phases
- **Blocks P0's completeness (not its start) — NOW RESOLVED:** Gap-4 — the canonical
  *cross-structure leverage / arbitration procedure* has been AUTHORED (Instructional Decision
  Making v1.0, stored verbatim, wired to nothing). P0-a may run with an interim dependency-derived
  ranking; **P0-b (canonically authoritative selection) is now technically UNBLOCKED but NOT
  authorized** — it awaits separate approval after review of the stored model.
- **Blocks P4 completion:** Gaps 1, 2, 3, 5 — subordinate models (Definition/Transition/…),
  Explanation placement, sentence-level scope decision, and Paragraph-Main-Point→Thesis unity
  handling. Until these are authored/decided, the corresponding legacy objects must remain.
- **Blocks P5 entirely:** all of Gaps 1, 2, 3, 5 are pure authoring/decision tasks owned by the
  curriculum authority, not the execution agent.

---

## 5. Phased Migration Plan (strategic; per-phase contract)

Each phase specifies: **Objective · Affected files/symbols · Expected behavioral change ·
Validation corpus · Rollback · Prunable legacy after validation · Why this order.**

### Phase P0 — Canonical Selection (primaries)  ← IMMEDIATE, EXECUTABLE NOW
Split into **P0-a (interim, executable immediately)** and **P0-b (authoritative, gated on Gap-4)**.

- **Objective.** Move `select_structure` from ranking the 11 legacy `MINIMAL_OBJECTS` via
  `PRIORITY_ORDER`/`_SEL_SYS` to ranking the **5 canonical PRIMARY structures** using their
  canonical fields. The selector chooses among {Opening, Thesis, Elaboration, Evidence / Example,
  Conclusion} and reports the target by its canonical name.
- **Affected files/symbols.**
  - `compass_structure_engine.py`: `select_structure()`, `_SEL_SYS`, `_priority_digest()`,
    `PRIORITY_ORDER`, `resolve_structure()`/`_ALIAS`. New canonical digest built from
    `compass_curriculum` (`get_structure`, `observable_decision_questions`,
    `structural_requirements`, `structural_dependencies`).
  - `compass_curriculum.py`: read-only consumers; possibly add a `primary_structures_digest()`
    helper (additive, no behavior change to existing API).
- **Expected behavioral change.** The engine's *chosen target* for a paragraph now aligns with
  canonical theory: e.g. Elaboration can be selected as principal even when legacy would have
  chosen Evidence; "must be contestable" no longer gates Thesis sufficiency. Student-facing content
  was already canonical for these structures, so the visible change is **which** structure is
  taught, in cases where legacy and canonical priorities diverge.
- **Validation corpus.** Corpus C-SELECT (see §10): the 6 Teacher-Review paragraphs + ~20 targeted
  cases probing the Evidence↔Elaboration inversion and the contestability rule. Compare P0 target
  choices against a documented expected-target key; require ≥ parity with the hybrid baseline on
  "reasonable target" and improvement on the inversion cases.
- **Rollback.** Keep `COMPASS_REASONING_MODE=exhaustive` env switch (already the global rollback).
  Additionally gate P0 behind an internal flag (e.g. `CANONICAL_SELECTION`) defaulting off until
  validated; flipping it off restores legacy selection with zero code churn.
- **Prunable legacy after validation (deferred to P4, NOT here).** `PRIORITY_ORDER`,
  `_priority_digest`, the legacy heuristics inside `_SEL_SYS`, and the five primaries' entries in
  `MINIMAL_OBJECTS`. **Do not delete in P0** — leave them behind the flag for rollback.
- **Why first.** Selection is the root of the contradiction (§1.3). Every downstream judgment
  (sufficiency, dialogue voice, teacher artifacts) is only coherent once the *target* is chosen on
  canonical grounds. Nothing downstream can be trusted while selection is legacy.
- **P0-a vs P0-b.** P0-a ships an interim leverage ranking derived from canonical
  `structural_dependencies` (upstream-before-downstream) documented in-code as provisional. P0-b
  replaces that with the **authored canonical leverage procedure — Instructional Decision Making
  v1.0 (Gap-4, now RESOLVED / stored verbatim, wired to nothing).** P0-a is safe to ship now because
  it changes only *ordering heuristics already under a flag*; P0-b is the point at which selection
  becomes *canonically authoritative*. **P0-b is technically unblocked but NOT authorized —**
  it awaits separate approval after the stored decision model is reviewed.

### Phase P1 — Canonical Sufficiency & State Judgement
- **Objective.** Source `status` (missing/partial/misleading/present ↔ canonical
  `developmental_variations`) and `developmental_sufficiency` (continue/reached ↔ canonical
  `developmental_sufficiency`) from the chosen structure's canonical model instead of the generic
  selector heuristics.
- **Affected files/symbols.** `compass_structure_engine.py`: the sufficiency/state fields produced
  in `select_structure()` and consumed in `run()` (`status`, `developmental_sufficiency`,
  `sufficiency_reasoning`, `developmental_variation`, `exit_criterion_*`). Feed the canonical
  `developmental_variations`/`developmental_sufficiency`/`observable_decision_questions` into the
  selector prompt and map the model's answer back to the four status buckets.
- **Expected behavioral change.** Sufficiency verdicts stop using forbidden generic tests (e.g.
  contestability) and start using canonical criteria (e.g. Thesis "possesses enough conceptual
  organization to support progressively integrated elaboration"). DISCOVERY→RESCUE escalation
  (driven by `current_target_attempts`) is unaffected in mechanism.
- **Validation corpus.** Corpus C-SUFFICIENCY (§10): revision sequences per structure that should
  flip `reached` at the canonically-correct point; assert no premature/late advancement vs the key.
- **Rollback.** Same `CANONICAL_SELECTION`-style flag extended to sufficiency, or a sibling flag
  `CANONICAL_SUFFICIENCY`; off restores selector-LLM judgment.
- **Prunable after validation (deferred to P4).** The sufficiency/contestability language embedded
  in `_SEL_SYS`.
- **Why after P0.** Sufficiency is *per target*; a canonical sufficiency judgment is meaningless
  until the target itself is canonical (§4.1).

### Phase P2 — Canonical Dialogue Form (voice anchoring)
- **Objective.** Anchor the DISCOVERY and RESCUE voice to each structure's canonical
  `discovery_instruction` / `rescue_instruction` (already partly done — `_resolve_teaching_source`
  passes `discovery`/`rescue` text). Strip any residual generic composition assumptions from
  `_DLG_SYS`, leaving only delivery mechanics (first-turn six-function shape, continuation shape,
  tone, anti-coauthoring, stop rule, curriculum-boundary guard).
- **Affected files/symbols.** `compass_structure_engine.py`: `_DLG_SYS`, `generate_dialogue()`,
  `_resolve_teaching_source()`. (Content already canonical; this phase is about the *form/voice*
  layer and removing the last generic-rule prohibitions now redundant with canonical fields.)
- **Expected behavioral change.** Minimal visible change; the dialogue voice is now guaranteed to
  never introduce a rule absent from the canonical model. The `_DLG_SYS` CURRICULUM BOUNDARY guard
  becomes fully load-bearing (it already prohibits generic rules; P2 removes the belt-and-suspenders
  generic phrasings so canonical is the sole source).
- **Validation corpus.** Corpus C-DIALOGUE (§10): assert zero occurrences of the rejected generic
  rules (hook-required, contestable-required, conclusion-restates-thesis) across a sweep of turns,
  and that discovery vs rescue behavior matches `current_target_attempts` escalation.
- **Rollback.** Keep the pre-P2 `_DLG_SYS` string under a flag; revert flag to restore.
- **Prunable after validation.** Generic-rule prohibition phrasings in `_DLG_SYS` that duplicate
  canonical guarantees (kept as comments if useful).
- **Why after P1.** The dialogue should teach to the same canonical basis the decision used;
  aligning voice before the decision layer is canonical risks decision/voice drift (§4.1).

### Phase P3 — Teacher Review + Noticing Re-anchoring
- **Objective.** Regenerate `teacher_review_fixtures.json` from the now-canonical engine, and
  re-anchor `NOTICING_SYSTEM_MESSAGE` to canonical terminology ("integrated message" vs "central
  idea/claim", "differentiation/integration" vs generic "development").
- **Affected files/symbols.** `server.py`: `NOTICING_SYSTEM_MESSAGE`, `_curate_case()`,
  `_TEACHER_REVIEW_PATH`. `gen_teacher_review_fixtures.py` (regeneration script) + regenerated
  `teacher_review_fixtures.json`.
- **Expected behavioral change.** Teacher-facing explanations and interim cards speak the canonical
  vocabulary consistent with the reasoning; no student-facing change.
- **Validation corpus.** Corpus C-TEACHER (§10): re-run the 6 sample paragraphs through the
  canonical engine; assert fixtures contain canonical field names and no legacy-only terms; spot-
  check teacher legibility.
- **Rollback.** Keep the previous fixtures file + previous noticing string; revert file/flag.
- **Prunable after validation.** Legacy composition terminology in the noticing prompt and any
  fixture generator references to legacy object names.
- **Why after P2.** These artifacts *describe* the engine's reasoning; re-anchoring them is only
  meaningful once that reasoning is canonical (§4.1).

### Phase P4 — Legacy Pruning (primaries)
- **Objective.** DELETE the now-unreferenced legacy machinery **for the five primary structures**:
  the primaries' entries in `MINIMAL_OBJECTS`, `PRIORITY_ORDER`, `_priority_digest`, the
  `_LEGACY_TO_CANONICAL` bridge, and the legacy heuristics in `_SEL_SYS`. Collapse
  `_resolve_teaching_source` to read canonical directly.
- **Affected files/symbols.** `compass_structure_engine.py`: `MINIMAL_OBJECTS` (remove primary
  entries), `PRIORITY_ORDER`, `_priority_digest`, `_LEGACY_TO_CANONICAL`, `_resolve_teaching_source`,
  `_ALIAS`/`resolve_structure` (canonicalize), `retrieve_object` (repoint to canonical). Remove the
  now-dead rollback flags introduced in P0–P2 once confidence is high (keep the env-level
  `COMPASS_REASONING_MODE=exhaustive` global rollback).
- **Expected behavioral change.** None (parity already proven in P0–P3). This is dead-code removal.
- **Validation corpus.** Re-run C-SELECT + C-SUFFICIENCY + C-DIALOGUE + C-TEACHER; require identical
  verdicts to the immediately-preceding validated run (regression gate).
- **Rollback.** Git revert of the deletion commit; the `exhaustive` env path remains as the
  ultimate safety net. This is why P4 is a *separate, isolated* commit.
- **Prunable after validation.** This phase IS the pruning.
- **Why last among primary phases.** Deletion is only safe once no phase references the symbols
  (§4.1). **Subordinate/sentence-level legacy objects are NOT pruned here** — they wait for P5.

### Phase P5 — Subordinate & Scope Resolution (BLOCKED on canonical authoring)
- **Objective.** Give `Explanation`, `Definition`, `Transition` (and notes-only Qualification /
  Comparison / Analogy) a *decided* canonical home; decide sentence-level scope; resolve
  Paragraph-Main-Point unity handling under canonical Thesis. THEN prune their legacy objects.
- **Affected files/symbols.** `compass_curriculum.py` (`SUBORDINATE_STRUCTURES`,
  `SUBORDINATE_FIELDS`, new subordinate models + loader), new `canonical_models/*` subordinate
  files, `compass_structure_engine.py` (subordinate retrieval + activation-condition selection),
  and the remaining `MINIMAL_OBJECTS` entries (Definition, Explanation, Transition, Sentence
  Construction, Paragraph Main Point) for final pruning.
- **Expected behavioral change.** Subordinate instruction (currently legacy) becomes canonical or
  is explicitly declared out-of-scope; no silent legacy fallback remains anywhere.
- **Validation corpus.** Corpus C-SUBORDINATE (§10) — authored *after* the subordinate models exist,
  because you cannot validate against theory that has not been supplied.
- **Rollback.** Per-subordinate flags; keep the legacy object until its canonical replacement is
  validated.
- **Prunable after validation.** The remaining `MINIMAL_OBJECTS` entries and their aliases.
- **Why last / blocked.** Every input to P5 is an authoring/decision owned by the curriculum
  authority (Gaps 1,2,3,5 in §9). The execution agent MUST NOT invent these models. P5 cannot start
  until they are supplied.

---

## 6. DELIVERABLE A — Legacy-Disposition Table

Disposition legend: **MIGRATE** = re-source from canonical; **PRUNE** = delete after parity;
**RECONCILE** = needs a canonical authoring decision first; **KEEP** = retain (flow/mechanics, not
knowledge).

### A.1 `MINIMAL_OBJECTS` (11 legacy instructional objects)
| Legacy object | Canonical target | Disposition | Phase | Blocking gap |
|---|---|---|---|---|
| Reader Orientation | Opening | MIGRATE → PRUNE | P0→P4 | — (mapped, ready) |
| Central Claim | Thesis | MIGRATE → PRUNE | P0→P4 | — (mapped, ready) |
| Paragraph Main Point | Thesis (unity requirement) | RECONCILE → MIGRATE → PRUNE | P5 | Gap-5 (unity handling not modeled) |
| Definition | Subordinate "Definition" (unmodeled) | RECONCILE | P5 | Gap-1 (subordinate model absent) |
| Evidence | Evidence / Example | MIGRATE → PRUNE | P0→P4 | — (mapped; priority inversion resolved by canonical leverage) |
| Explanation | **no canonical home** | RECONCILE | P5 | Gap-2 (placement undecided) |
| Elaboration | Elaboration (PRINCIPAL) | MIGRATE → PRUNE | P0→P4 | — (mapped; re-rank as principal) |
| Transition | Subordinate "Transition" (unmodeled) | RECONCILE | P5 | Gap-1 |
| Paragraph Closure | Conclusion | MIGRATE → PRUNE | P0→P4 | — (merge into Conclusion) |
| Conclusion | Conclusion | MIGRATE → PRUNE | P0→P4 | — (mapped, largely consistent) |
| Sentence Construction | **no canonical home** | RECONCILE | P5 | Gap-3 (scope decision) |

### A.2 Selection / judgement machinery
| Legacy symbol | Role | Canonical replacement | Disposition | Phase |
|---|---|---|---|---|
| `PRIORITY_ORDER` (11-item list) | fixed priority ranking | canonical leverage procedure over `structural_dependencies` (Gap-4) | MIGRATE → PRUNE | P0 (interim) / P0-b / P4 |
| `_SEL_SYS` (selector system prompt) | generic composition heuristics (contestability, claim-before-evidence, etc.) | canonical `observable_decision_questions` + `developmental_variations` + leverage procedure | MIGRATE (rewrite) → PRUNE heuristics | P0/P1 → P4 |
| `_priority_digest()` | builds priority list text from `MINIMAL_OBJECTS` | canonical primary digest from `compass_curriculum` | MIGRATE → PRUNE | P0 → P4 |
| `_ALIAS` / `resolve_structure()` | name normalization to legacy names | canonicalize to canonical names | MIGRATE (repoint) | P0/P4 |
| `retrieve_object()` | returns `MINIMAL_OBJECTS[target]` | canonical `get_structure` fields | MIGRATE (repoint) → PRUNE | P2/P4 |
| `_LEGACY_TO_CANONICAL` (bridge map) | legacy→canonical name remap | unnecessary once selection is canonical | PRUNE | P4 |
| `_resolve_teaching_source()` | hybrid canonical/legacy content resolver | collapse to canonical-only | MIGRATE (simplify) → partial PRUNE | P2/P4 (subordinate branch remains until P5) |

### A.3 Dialogue / closure / teacher-facing
| Legacy symbol / asset | Role | Disposition | Phase |
|---|---|---|---|
| `_DLG_SYS` | dialogue system prompt (mechanics + residual generic rules) | KEEP mechanics; PRUNE residual generic-rule phrasings | P2 |
| `generate_dialogue()` | dialogue turn builder | KEEP (flow); repoint sources | P2 |
| `_CLOSURE_SYS` / `generate_closure()` | no-target closure | MIGRATE (derive from canonical Conclusion + sufficiency) | P1/P3 |
| `NOTICING_SYSTEM_MESSAGE` (server.py) | interim cards, generic terms | MIGRATE (re-anchor to canonical terms) | P3 |
| `teacher_review_fixtures.json` + `_curate_case()` | teacher-facing precomputed cases | MIGRATE (regenerate from canonical engine) | P3 |
| `_RESCUE_SIGNAL` / `_wants_help()` | rescue trigger detection | KEEP (mechanic, structure-agnostic) | — |
| `_DOES_WORK` ownership guard | anti-coauthoring guard | KEEP | — |
| DISCOVERY/RESCUE + FIRST-TURN/CONTINUATION logic in `run()` | flow mechanics | KEEP | — |
| durable transport (`_finalize_structure_v5`, `_run_reasoning`, RP5_MODES) | flow/transport | KEEP | — |

### A.4 Explicitly KEEP (flow, not knowledge — never pruned)
Two-call SELECT→TEACH shape; One-Thing-Rule contract; authoritative-decision-then-fixed-target;
`current_target_attempts` DISCOVERY/RESCUE gating; teacher override handling; audit + state
persistence (`compass_foundation`); `COMPASS_REASONING_MODE=exhaustive` global rollback.

---

## 7. DELIVERABLE B — File-by-File Pruning Map (dependency order)

Order within each file follows the phase order (P0→P5). Symbols are exact.

### B.1 `compass_structure_engine.py`  (primary migration surface)
| Symbol | P0 | P1 | P2 | P4 | Final state |
|---|---|---|---|---|---|
| `PRIORITY_ORDER` | replace usage w/ canonical digest (behind flag) | — | — | **DELETE** | gone |
| `MINIMAL_OBJECTS` (5 primaries) | keep for rollback | — | — | **DELETE primary entries** | subordinate entries remain until P5 |
| `MINIMAL_OBJECTS` (Definition, Explanation, Transition, Sentence Construction, Paragraph Main Point) | keep | keep | keep | **KEEP** | pruned in P5 |
| `_SEL_SYS` | rewrite to canonical questions/leverage (flagged) | fold in canonical sufficiency | — | **DELETE legacy heuristics** | canonical-only prompt |
| `_priority_digest()` | replace w/ canonical digest helper | — | — | **DELETE** | replaced by canonical digest |
| `select_structure()` | rank canonical primaries | source status+sufficiency canonically | — | remove legacy branches | canonical-only |
| `resolve_structure()` / `_ALIAS` | add canonical names | — | — | drop legacy-only aliases | canonical names |
| `retrieve_object()` | — | — | repoint to canonical | **DELETE** or repoint | canonical `get_structure` |
| `_LEGACY_TO_CANONICAL` | keep (bridge still needed) | — | — | **DELETE** | gone |
| `_resolve_teaching_source()` | keep | keep | simplify (canonical primary path) | collapse primary branch | subordinate branch remains until P5 |
| `_DLG_SYS` | — | — | strip residual generic rules; keep mechanics | — | mechanics-only |
| `generate_dialogue()` | — | — | canonical voice anchoring | — | canonical-sourced |
| `_CLOSURE_SYS` / `generate_closure()` | — | derive sufficiency from canonical | — | — | canonical-derived closure |
| `run()` orchestration | pass canonical target through | pass canonical status/sufficiency | — | remove dead fallbacks | unchanged flow, canonical inputs |
| `_RESCUE_SIGNAL`, `_wants_help`, `_DOES_WORK`, DISCOVERY/RESCUE gating | KEEP | KEEP | KEEP | KEEP | unchanged |

### B.2 `compass_curriculum.py`  (canonical source — mostly additive)
| Symbol | Change | Phase |
|---|---|---|
| `get_structure`, `get_field`, `observable_decision_questions`, `is_structure_ready` | consumed read-only by selection | P0 |
| NEW `primary_structures_digest()` (proposed helper) | additive; builds selector digest from canonical fields | P0 |
| NEW canonical leverage procedure hook (proposed) | additive; encodes Gap-4 once authored | P0-b |
| `SUBORDINATE_STRUCTURES` / `SUBORDINATE_FIELDS` | populate with authored subordinate models | P5 |
| `_MODEL_FILES` / `_load_supplied_models` | extend for subordinate model files | P5 |

### B.3 `server.py`  (transport + teacher-facing; flow KEEP)
| Symbol | Change | Phase |
|---|---|---|
| `NOTICING_SYSTEM_MESSAGE` | re-anchor to canonical terms | P3 |
| `_curate_case()` | map canonical fields for teacher view | P3 |
| `_TEACHER_REVIEW_PATH` / `teacher_review_fixtures.json` | regenerate from canonical engine | P3 |
| `_finalize_structure_v5`, `_run_reasoning`, `RP5_MODES`, `DEFAULT_REASONING_MODE` | **KEEP unchanged** (transport) | — |
| `set_reasoning_mode` valid modes | **KEEP** (`exhaustive` rollback retained) | — |

### B.4 `gen_teacher_review_fixtures.py`  (regeneration script)
Re-run after P0–P2 land to regenerate fixtures against the canonical engine (P3). Update any
legacy object-name references. No student-facing impact.

### B.5 Assets
| File | Change | Phase |
|---|---|---|
| `canonical_models/{thesis,elaboration,evidence_example,conclusion,opening}.json` | source of truth (unchanged) | — |
| NEW `canonical_models/{definition,transition,...}.json` | authored subordinate models | P5 (blocked) |
| `teacher_review_fixtures.json` | regenerated | P3 |

### B.6 Files NOT touched (confirm no coupling before pruning)
`compass_foundation.py` (state/audit — KEEP; `current_target_attempts` stays), `governance_v2.py`
(behind feature flag, separate TC10 track), `organizing_thought.py`, `feedback.py`,
`compass_decision_engine.py` / `compass_coaching_controller.py` (legacy `exhaustive`/RP4 path,
retained only as the env-level rollback — do NOT delete during this migration).

---

## 8. DELIVERABLE C — Staged Migration Plan (condensed cross-reference)

| Stage | Gate to start | Ships behind flag | Validated by | Rollback | Unblocks |
|---|---|---|---|---|---|
| **P0-a** Canonical selection (interim leverage) | Curriculum ready (DONE) | `CANONICAL_SELECTION` | C-SELECT | flag off / `exhaustive` env | P1 |
| **P0-b** Authoritative leverage procedure | Gap-4 authored | same flag | C-SELECT (leverage cases) | flag off | full P0 authority |
| **P1** Canonical sufficiency/state | P0-a validated | `CANONICAL_SUFFICIENCY` | C-SUFFICIENCY | flag off | P2 |
| **P2** Canonical dialogue voice | P1 validated | `CANONICAL_DIALOGUE` | C-DIALOGUE | keep old `_DLG_SYS` | P3 |
| **P3** Teacher Review + noticing | P2 validated | fixture/file swap | C-TEACHER | keep old fixtures/string | P4 |
| **P4** Legacy pruning (primaries) | P3 validated | isolated commit | full regression (C-ALL) | git revert + `exhaustive` env | P5 |
| **P5** Subordinate + scope | Gaps 1,2,3,5 authored | per-subordinate flags | C-SUBORDINATE (authored w/ models) | keep legacy object per item | end-state |

Sequencing rationale is the dependency graph in §4. The single most important rule: **P0 first
because selection is the root contradiction; P4 (deletion) only after P0–P3 remove every reference;
P5 blocked on curriculum authoring and therefore last.**

---

## 9. DELIVERABLE D — Missing Canonical Decision Questions (authoring gaps that block phases)

These are decisions ONLY the curriculum authority can make. The execution agent must not invent
them. Each is phrased as the concrete question that must be answered before the dependent phase can
complete.

- **Gap-1 — Subordinate structure models (blocks P5).**
  For each of Definition, Transition, Qualification, Comparison, Analogy:
  (a) What are its `activation_conditions` (when does it become the highest-leverage target)?
  (b) What are its `structural_requirements` and `developmental_sufficiency` on the lighter
  `SUBORDINATE_FIELDS` schema? (c) What is its `relationship_to_primary`? Definition currently maps
  to {Thesis, Elaboration}; must confirm.

- **Gap-2 — Explanation placement (blocks P5; smallest hybrid landmine now).**
  Is "Explanation" (reasoning linking evidence→claim) (i) a facet WITHIN canonical Elaboration,
  (ii) a relation within Evidence / Example, or (iii) a distinct subordinate object? Until decided,
  Explanation has NO canonical home and must keep its legacy object. **Note:** the canonical
  Elaboration model already treats reader-driven development as principal; the authority must state
  whether evidence→claim reasoning is subsumed there or separated.

- **Gap-3 — Sentence-level scope (blocks P5).**
  Is sentence-level instruction ("Sentence Construction") IN SCOPE for the paragraph curriculum at
  all? If yes, author a home (subordinate model or note within a primary); if no, declare it
  explicitly out-of-scope so the legacy object can be removed rather than orphaned.

- **Gap-4 — Cross-structure leverage / arbitration procedure — ✅ AUTHORED / CANONICALLY RESOLVED (2026-06).**
  RESOLVED by the supplied **Canonical Model: Instructional Decision Making v1.0**, stored verbatim
  at `backend/canonical_models/instructional_decision_making.json` and loaded read-only via
  `compass_curriculum.py` (`get_decision_model`, `get_decision_section`,
  `decision_foundational_principles`, `decision_order`, `canonical_decision_questions`,
  `is_decision_model_ready`, `decision_model_report`). WIRED TO NOTHING — no change to
  `select_structure`, priority order, sufficiency, dialogue, Teacher Review, UI, DB, audit, or OT.
  The model supplies: 7 Foundational Principles (One Thing, Development-Before-Correction,
  Highest-Leverage, Dependency, Generative, Developmental Sufficiency, Recursive), the Unit of
  Decision (the learner's present developmental organization), Sources of Evidence, a 6-step Order
  of Decision, When-Not-to-Teach and When-to-Recurse rules, and 9 Canonical Decision Questions.
  This is the authoritative *procedure + principles* that P0-b must implement.
  **P0-b is now technically UNBLOCKED but NOT authorized for execution** — it awaits separate
  approval after review of the stored model.
  - *Original (superseded) statement of the gap, kept for history:* the canonical models supplied
    per-structure decision questions and a dependency-implied order but NOT an explicit
    "which primary is highest-leverage now" procedure; the legacy `PRIORITY_ORDER` was a
    contradicting stand-in.
  - *Residual implementation note (NOT a new authoring gap — resolve during P0-b, do not resolve
    now):* the model specifies leverage/dependency at the level of PRINCIPLES + PROCEDURE + DECISION
    QUESTIONS; it does not itself enumerate the concrete ordering among the five primaries
    (e.g. it does not literally state "Elaboration outranks Evidence"). That concrete ranking is to
    be DERIVED mechanically in P0-b by applying the model's Highest-Leverage + Dependency principles
    to each structure's canonical `structural_dependencies` — an implementation task, not further
    curriculum authoring. See also the taxonomy note below.

- **Gap-5 — Paragraph Main Point → Thesis unity (blocks P5 pruning of that object).**
  Reconciliation notes say Paragraph Main Point "folds into Thesis" via the Thesis model's
  Organizing Relevance requirement. Required: confirm that single-paragraph *unity* diagnosis
  (drift/tangents/competing topics) is fully covered by Thesis's `Organizing Relevance` +
  `developmental_variations`, or specify what additional canonical content is needed before the
  legacy Paragraph Main Point object can be pruned.

**Summary of blocking relationships:** Gap-4 blocks P0 *authority* (not its start). Gaps 1,2,3,5
block P4 *completion* and all of P5. None block P0-a, P1, P2, P3 from shipping for the five primary
structures.

### 9.1 Reported contradictions / implementation ambiguities (NOT resolved here — per directive)
Per the store-verbatim directive (report, do not resolve), one implementation ambiguity was found
while ingesting the Instructional Decision Making model; it is recorded for the P0-b execution phase
and must be resolved by the executor/authority then, not now:

- **Instructional-level taxonomy mismatch (P0-b).** The model's Order of Decision **Step 6** names
  four instructional levels — **Discovery, Scaffold, Rescue, Closure**. The current engine implements
  a DISCOVERY-vs-RESCUE *binary* (gated by `current_target_attempts` / `_wants_help`), a separate
  CLOSURE path (`generate_closure`, CASE_2 no-target), and an independent `instructional_action`
  field with five values (`teach|scaffold|ask_question|model|encourage_revision`). So "Scaffold" as
  a *peer level* alongside Discovery/Rescue/Closure does not map 1:1 onto the engine's current
  DISCOVERY/RESCUE modes + action list. This is an alignment decision for P0-b (how the model's
  four levels map onto the engine's mode/action machinery). No literal contradiction with the FROZEN
  flow; flagged only so P0-b does not silently pick a mapping. **Not resolved in this pass.**

No other literal contradictions were found between the supplied model and the existing plan; the
model's principles (Highest-Leverage, Dependency, Developmental Sufficiency, Recursive) are
consistent with, and now supersede, the interim dependency-derived leverage described for P0-a.

---

## 10. DELIVERABLE E — Validation Corpus Proposal (parity before pruning)

Principle: **no legacy symbol is deleted until a corpus proves the canonical path is at least as
good.** Each corpus is a JSON case set + an expected-decision key + an LLM-graded rubric, run
through the REAL engine via the existing harness pattern (`_harness_run_turn`), NOT mocked.

### C-SELECT (gates P0)
- **Composition (~30 cases).** The 6 Teacher-Review paragraphs (Students A–F) + ~24 targeted cases:
  8 Evidence-vs-Elaboration inversion probes (paragraphs where canonical says Elaboration is
  principal but legacy would pick Evidence), 6 contestability probes (valid non-contestable theses
  legacy would mark "not present"), 4 Opening/Conclusion-optionality probes (single paragraphs
  where whole-piece structures should NOT be selected), 6 clear-target controls.
- **Metric.** For each case, expected canonical target (authored key). Pass = canonical selection
  matches the key OR is a defensible alternative; require **improvement** on the inversion +
  contestability probes vs the hybrid baseline (documented current behavior), and **≥ parity** on
  controls. Zero regressions on the 6 sample paragraphs.

### C-SUFFICIENCY (gates P1)
- **Composition (~20 cases).** Per primary structure, a 2–3 draft revision sequence that should flip
  `developmental_sufficiency` from `continue` to `reached` at the canonically-correct draft.
- **Metric.** `reached` fires at the keyed draft (no premature advancement, no failure to advance);
  status buckets (missing/partial/misleading/present) match the canonical
  `developmental_variations` reading. Assert the contestability test is NOT used.

### C-DIALOGUE (gates P2)
- **Composition (~20 turns across structures).** First-turn + continuation + rescue-triggered turns.
- **Metric (automated string + LLM rubric).** ZERO occurrences of rejected generic rules
  ("must be contestable", "needs a hook", "restate the thesis", "add transition words"); DISCOVERY
  withholds strategies; RESCUE (after `current_target_attempts>=2` or `_wants_help`) offers
  possibilities not recommendations; anti-coauthoring (`_DOES_WORK`) clean on 100%.

### C-TEACHER (gates P3)
- **Composition.** Re-run Students A–F through the canonical engine; regenerate fixtures.
- **Metric.** Fixtures use canonical vocabulary; noticing cards reference canonical terms; teacher
  legibility spot-check; no student-facing change.

### C-ALL (gates P4)
- **Composition.** Union of C-SELECT + C-SUFFICIENCY + C-DIALOGUE + C-TEACHER.
- **Metric.** IDENTICAL verdicts to the last validated pre-deletion run (pure regression gate).

### C-SUBORDINATE (gates P5 — authored AFTER the subordinate models exist)
- Cannot be specified now: its expected-decision key depends on canonical theory that has not been
  supplied (Gaps 1,2,3,5). Placeholder only; author alongside the subordinate models.

**Corpus artifacts land under** `backend/test_cases/` (case JSON) and `test_reports/` (run exports),
matching the existing harness conventions. Runs use the durable background path, not localhost SSE.

---

## 11. Risks & Rollback Points (consolidated)

| Risk | Phase | Mitigation | Rollback |
|---|---|---|---|
| Priority inversion changes many targets unexpectedly | P0 | C-SELECT parity gate + interim leverage documented | `CANONICAL_SELECTION` flag off / `COMPASS_REASONING_MODE=exhaustive` |
| Sufficiency fires too early/late under canonical criteria | P1 | C-SUFFICIENCY revision-sequence key | `CANONICAL_SUFFICIENCY` flag off |
| Dialogue voice drift after removing generic guards | P2 | C-DIALOGUE zero-generic-rule assertion | keep old `_DLG_SYS` behind flag |
| Teacher artifacts describe stale reasoning | P3 | regenerate after P0–P2; keep old fixtures | file/string revert |
| Deleting a symbol still referenced elsewhere | P4 | grep sweep + C-ALL regression before delete | git revert deletion commit |
| Pruning a subordinate before it has a canonical home | P5 | never prune until model authored + validated | per-subordinate flag; keep legacy object |
| Curriculum authority unavailable for Gaps 1–5 | P0-b/P5 | P0-a/P1/P2/P3/P4-primaries proceed independently | phases are decoupled by the flags above |
| Foothold definition leak (known parked issue) | any | out of scope for this migration; separate engine-boundary sprint | n/a |

**Ultimate rollback (all phases):** `COMPASS_REASONING_MODE=exhaustive` routes the learner path
back to the pre-RP5 engine entirely. This env switch must remain functional through P4; it may only
be retired after the canonical path has soaked in production.

---

## Appendix — Exact symbols, files, and implementation sequence (for the execution agent)

### AP.1 Learner-path call chain (do not alter the shape)
```
POST /api/sessions/{id}/interact            (server.py)
  → append student turn + placeholder AI turn (status=processing)  [<0.2s return]
  → asyncio.create_task(_run_reasoning(session_id, ai_turn_id, req))   (server.py:3441)
      → if reasoning_mode in RP5_MODES ("consolidated_v2","structure_v5"):   (server.py:3463)
          → _finalize_structure_v5(...)                                (server.py:3393)
              → compass_structure_engine.run(session_dict, content, kind)  (structure_engine:616)
                  → select_structure(...)      STEP 1  (structure_engine:299)   [MIGRATE P0/P1]
                  → retrieve_object(target)     STEP 2  (structure_engine:232)   [REPOINT P2/P4]
                  → (authoritative decision written to InstructionalState)      [KEEP]
                  → generate_dialogue(...) | generate_closure(...)  STEP 4       [P2/P1]
```

### AP.2 Exact symbols by file
`compass_structure_engine.py`:
- Lines 46–58 `PRIORITY_ORDER` — MIGRATE(P0)→DELETE(P4)
- Lines 69–202 `MINIMAL_OBJECTS` — primaries DELETE(P4); subordinates KEEP→P5
- Lines 205–229 `_ALIAS`, `resolve_structure()` — repoint to canonical
- Lines 232–234 `retrieve_object()` — repoint(P2)/DELETE(P4)
- Lines 240–278 `_SEL_SYS` — rewrite canonical(P0/P1); delete heuristics(P4)
- Lines 281–286 `_priority_digest()` — replace with canonical digest(P0)→DELETE(P4)
- Lines 299–338 `select_structure()` — canonical ranking(P0) + canonical status/sufficiency(P1)
- Lines 345–419 `_DLG_SYS` — strip residual generic rules(P2); keep mechanics
- Lines 422–430 `_RESCUE_SIGNAL`, `_wants_help()` — KEEP
- Lines 435–449 `_LEGACY_TO_CANONICAL` — DELETE(P4)
- Lines 452–480 `_resolve_teaching_source()` — simplify(P2); collapse primary branch(P4); subordinate branch→P5
- Lines 483–571 `generate_dialogue()` — canonical voice(P2)
- Lines 574–595 `_CLOSURE_SYS`, `generate_closure()` — canonical-derive(P1/P3)
- Lines 599–604 `_DOES_WORK` — KEEP
- Lines 616–893 `run()` — pass canonical inputs; remove dead fallbacks(P4); KEEP flow, DISCOVERY/RESCUE (`current_target_attempts` at 745–749), teacher override, audit

`compass_curriculum.py`:
- `get_structure`, `get_field`, `observable_decision_questions`, `is_structure_ready`,
  `pending_report` — read-only consumers for P0/P1
- Proposed additive helpers: `primary_structures_digest()`, canonical leverage hook (P0/P0-b)
- `SUBORDINATE_STRUCTURES`, `SUBORDINATE_FIELDS`, `_MODEL_FILES`, `_load_supplied_models` — P5

`server.py`:
- `NOTICING_SYSTEM_MESSAGE` (1984), `_pedagogical_noticing` (2006) — re-anchor(P3)
- `_TEACHER_REVIEW_PATH` (1846), `_curate_case` (1858) — canonical mapping(P3)
- `_finalize_structure_v5` (3393), `_run_reasoning` (3441), `RP5_MODES`/`DEFAULT_REASONING_MODE`
  (33–34) — KEEP (transport)
- `set_reasoning_mode` (2077) — KEEP the `exhaustive` rollback mode

`compass_foundation.py`: `InstructionalState` (117), `current_target_attempts` (183),
`selected_instructional_object` (162) — KEEP; no schema change required by P0–P4.

### AP.3 Canonical model field contract (per primary, 9 fields)
`definition · function · structural_dependencies{upstream,downstream} · structural_requirements[]
{name,requirement,observable_questions[],decision_rule?} · developmental_variations[]{name,
description} · developmental_sufficiency · discovery_instruction · rescue_instruction ·
observable_decision_questions[]`.
Selection (P0) reads `structural_dependencies` + `observable_decision_questions` +
`developmental_variations`. Sufficiency (P1) reads `developmental_variations` +
`developmental_sufficiency`. Dialogue (P2) reads `discovery_instruction` / `rescue_instruction` +
`structural_requirements` (already wired via `_resolve_teaching_source`).

### AP.4 Implementation sequence (mechanical, per phase)
1. **P0-a:** add `primary_structures_digest()` to `compass_curriculum`; behind `CANONICAL_SELECTION`
   flag, rewrite `select_structure`/`_SEL_SYS`/`_priority_digest` to rank the 5 canonical primaries
   using an interim dependency-derived leverage order; keep legacy path when flag off. Run C-SELECT.
2. **P0-b:** replace interim leverage with the authored Gap-4 procedure. Re-run C-SELECT leverage
   cases.
3. **P1:** behind `CANONICAL_SUFFICIENCY`, source `status` + `developmental_sufficiency` from the
   chosen structure's canonical fields. Run C-SUFFICIENCY.
4. **P2:** behind `CANONICAL_DIALOGUE`, strip residual generic-rule phrasings from `_DLG_SYS`; ensure
   discovery/rescue text flows from canonical fields only. Run C-DIALOGUE.
5. **P3:** re-anchor `NOTICING_SYSTEM_MESSAGE`; regenerate `teacher_review_fixtures.json` via
   `gen_teacher_review_fixtures.py`; update `_curate_case`. Run C-TEACHER.
6. **P4 (isolated commit):** delete `PRIORITY_ORDER`, `_priority_digest`, `_LEGACY_TO_CANONICAL`,
   primary entries of `MINIMAL_OBJECTS`, legacy heuristics in `_SEL_SYS`; collapse
   `_resolve_teaching_source` primary branch; retire P0–P2 flags. Run C-ALL regression; require
   identical verdicts. Keep `COMPASS_REASONING_MODE=exhaustive`.
7. **P5 (blocked):** only after the authority supplies Gaps 1,2,3,5 — author subordinate models,
   decide Explanation/sentence scope, resolve unity handling; then prune remaining `MINIMAL_OBJECTS`
   entries and aliases. Run C-SUBORDINATE.

### AP.5 Pre-deletion safety checklist (before every PRUNE)
- `grep -rn "<symbol>" backend/ --include=*.py` returns only the definition + (dead) rollback refs.
- The corpus gating that phase is green with no regressions vs the last validated run.
- The `exhaustive` env rollback still routes and passes a smoke turn.
- Deletion is a standalone commit (clean revert boundary).

---

*End of plan. This document changed no production code. Phases P0-a, P1, P2, P3, and the
primary-facing part of P4 are executable without further canonical authoring; P0-b and P5 are
gated on curriculum-authority decisions enumerated in §9 (Deliverable D).*
