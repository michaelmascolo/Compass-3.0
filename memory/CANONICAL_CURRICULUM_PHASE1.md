# Canonical Paragraph Curriculum — Phase 1 Report (BUILD + MAP + AUDIT; no behavior changed)

## 1. Where each canonical object is stored
`/app/backend/compass_curriculum.py` — authoritative internal library (structured knowledge, not
prompt fragments). Registry `CURRICULUM` keyed by the 5 primary structures; each is a nine-field
`CanonicalStructure`; every field carries provenance (`calibrated` | `source_material` | `pending`).
Query API: `get_structure`, `get_field`, `observable_decision_questions`, `is_structure_ready`,
`pending_report`. Wired to NOTHING (import changes no behavior). Nine fields = definition, function,
structural_dependencies, structural_requirements, developmental_variations, developmental_sufficiency,
discovery_instruction, rescue_instruction, observable_decision_questions.

## 2. Which components now read from it
NONE yet (Phase 1 is build+map only; "do not implement new behavior"). Confirmed: no import of
`compass_curriculum` anywhere in server.py / compass_structure_engine.py / compass_foundation.py.

## 3. Which components still rely on generic composition knowledge (dependency audit)
| Component | File / symbol | Generic-knowledge dependency |
|---|---|---|
| Instructional Decision (selector) | `compass_structure_engine._SEL_SYS` + `_priority_digest()` | Priority rules + per-object decision heuristics live in a hand-written prompt; reads `MINIMAL_OBJECTS.essence/present` — not the curriculum. |
| Canonical objects (the current CIO library) | `compass_structure_engine.MINIMAL_OBJECTS` (11 objects, 5 fields each) | The de-facto knowledge base. Only 5 were Phase-II CALIBRATED (Central Claim, Evidence, Explanation, Definition, Paragraph Main Point). Reader Orientation, Elaboration, Transition, Paragraph Closure, Conclusion, Sentence Construction were authored generically. |
| Dialogue generation | `compass_structure_engine._DLG_SYS` + `generate_dialogue` prompt | Teacher voice + DISCOVERY/RESCUE + six-function sequence are generic prompt knowledge; pulls essence/indicators/variations/teaching_strategy/exit_criterion from MINIMAL_OBJECTS. |
| Closure turn | `compass_structure_engine._CLOSURE_SYS` + `generate_closure` | Generic prompt. |
| Developmental sufficiency | `select_structure` JSON (`developmental_sufficiency`) via `_SEL_SYS` | Judged by the selector LLM (generic heuristic), only loosely guided by object `exit_criterion`. |
| Pedagogical noticing (interim cards) | `server.NOTICING_SYSTEM_MESSAGE` + `_pedagogical_noticing` | Generic prompt; does not read canonical objects. |
| Teacher Review | `server.get_teacher_review_cases` + `teacher_review_fixtures.json` (159 KB, precomputed) | Hand-authored/precomputed fixtures; no reference to canonical objects. |
| Aliases / structure names | `compass_structure_engine._ALIAS`, `PRIORITY_ORDER` | Names/labels reflect generic composition taxonomy (thesis↔central claim, topic sentence↔main point, etc.). |

## 4. Mapping of the 5 PRIMARY structures onto existing objects
| Primary | Proposed source | Calibrated? | Confidence | Note |
|---|---|---|---|---|
| Opening | Reader Orientation | NO | low | Existing object authored generically; is "Opening" == "Reader Orientation" and is it in-scope at single-paragraph level? |
| Thesis | Central Claim | YES (#1) | high | Alias already maps thesis→Central Claim. Lifted 2/9 fields (developmental_variations, developmental_sufficiency). |
| Elaboration | Explanation (#3) **or** Elaboration (not cal.) | mixed | UNRESOLVED | Directive orders it BEFORE Evidence — suggests developing/explaining the thesis. Two existing objects could match. Needs decision. |
| Evidence / Example | Evidence | YES (#2) | high | Lifted 2/9 fields. Is "Example" a subtype of Evidence or its own developmental_variation? |
| Conclusion | Conclusion | NO | low | Existing object authored generically. |

### What could be lifted authoritatively (no invention)
Only the two 1:1 fields, and only for the confirmed calibrated mappings:
- **Thesis** ← Central Claim: `developmental_variations`, `developmental_sufficiency` (=exit_criterion). Calibrated essence/indicators/teaching_strategy attached as `source_material` for definition/function/structural_requirements/discovery_instruction/observable_decision_questions (these are NOT 1:1 — authoring needed).
- **Evidence / Example** ← Evidence: same two fields lifted; same source_material attached.
- Everything else (Opening, Elaboration, Conclusion; all of structural_dependencies + rescue_instruction everywhere) = `PENDING_CANONICAL_INPUT`.

Net readiness: 0/5 structures complete; 4/45 primary-field slots calibrated; the rest pending or source-material-only.

## 5. Open questions blocking further population (do NOT invent — asked)
(see ask_human)

---

## Canonical decisions applied (A–E) — 2026-06
- **A(a):** Authority supplies each primary model verbatim. NO reconstruction from existing CIOs or generic knowledge. All primary fields reset to PENDING_CANONICAL_INPUT until supplied. Earlier 1:1 lifts (Thesis/Evidence developmental_variations & sufficiency) were REMOVED per this rule.
- **B(c):** Elaboration is a NEW object (not the calibrated Explanation). Working definition recorded in RECONCILIATION_NOTES; full model PENDING supply. Existing Explanation CIO left unchanged.
- **C(a):** Opening & Conclusion stay PENDING; existing generic Reader Orientation/Conclusion NOT lifted, even provisionally. Generic assumptions to reject recorded.
- **D:** Paragraph Main Point folds into Thesis (single-paragraph); NOT a primary; existing CIO unchanged. Definition & Explanation subordinate (unchanged in live engine); reconciliation-pending. Subordinate structures use a LIGHTER 8-field schema; no full models built this phase.
- **E:** Phase 1 = populate 5 primary models + provenance + validation + internal consistency + report; ZERO production rewiring. Confirmed.

## Infrastructure now
- `compass_curriculum.py`: all 5 primary structures = 9 fields, every field `pending`; `MODEL_SUPPLY_ORDER = [Thesis, Elaboration, Evidence/Example, Conclusion, Opening]`; `SUBORDINATE_FIELDS` (8) + `SUBORDINATE_STRUCTURES` notes; `RECONCILIATION_NOTES`; `insert_primary_model()` + `validate_model()` (verbatim insert, nine-field check); read-only query API. Wired to NOTHING.
- Awaiting model #1: **Thesis**.

---

## PHASE 1 COMPLETE — 2026-06 (all 5 primary models inserted & validated; ZERO rewiring)

### 1. Completed authoritative models (stored / provenance)
All under `/app/backend/canonical_models/*.json`, loaded verbatim into `compass_curriculum.CURRICULUM`
on import; every field provenance = `canonical_supplied`; `is_structure_ready` = True for all five.
| Structure | file | struct_reqs | dev_variations | decision_qs |
|---|---|---|---|---|
| Thesis | thesis.json | 5 | 6 | 9 |
| Elaboration | elaboration.json | 6 | 7 | 10 |
| Evidence / Example | evidence_example.json | 8 | 10 | 12 |
| Conclusion | conclusion.json | 5 | 6 | 8 |
| Opening | opening.json | 7 | 10 | 12 |
Schema validation for each: {ok:True, missing:[], extra:[], empty:[]}. Verbatim fidelity confirmed
field-by-field. No normalization toward conventional composition pedagogy. Internally consistent:
Thesis→Elaboration→(Evidence/Example subordinate)→Conclusion; Opening optional & audience-defined;
generic assumptions explicitly rejected inside the models (hook-required, conclusion=restate, etc.).

### 2. Unresolved subordinate-object reconciliation questions (for the later phase)
- Placement of existing calibrated **Explanation** CIO relative to canonical Elaboration (within
  Elaboration / as an Evidence-Example relation / distinct lower-level object).
- **Paragraph Main Point** folds into Thesis at single-paragraph level — confirm migration & retirement.
- **Definition** subordinate activation modeling (lighter 8-field schema) — when to author it.
- Naming: Thesis model's downstream lists "Evidence" & "Examples" separately vs primary name
  "Evidence / Example" — unify during reconciliation.
- Whether/when any subordinate (Transition, Qualification, Comparison, Analogy) needs a full model.

### 3. Live-engine locations still on older CIO / generic knowledge (unchanged this phase)
- `compass_structure_engine.MINIMAL_OBJECTS` (11 objects, 5-field) — the live knowledge base.
- `compass_structure_engine._SEL_SYS` + `_priority_digest` — selection heuristics (generic prompt).
- `compass_structure_engine._DLG_SYS` + `generate_dialogue` — dialogue voice/sequence (generic prompt).
- `compass_structure_engine._CLOSURE_SYS` + `generate_closure`.
- developmental sufficiency via `select_structure` (LLM heuristic).
- `server.NOTICING_SYSTEM_MESSAGE` / `_pedagogical_noticing` (interim cards).
- `server.get_teacher_review_cases` + `teacher_review_fixtures.json` (precomputed).
NONE of these import `compass_curriculum`. Wiring them is the later, separately-approved phase.

### Phase-1 exit criteria (E) status: 1✔ 2✔ 3✔ 4✔ 5✔ 6✔ ; production rewiring = 0 (as required).
