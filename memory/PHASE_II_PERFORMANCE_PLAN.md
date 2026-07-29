# Phase II — Make the Existing Pedagogy Fast (Knowledge Base as Performance Infrastructure)

Status: PLAN (awaiting approval before touching the frozen engine). 2026-06-29.
Instructional experience (student coaching + Teacher Review) is FROZEN for this phase.

## The real bottleneck (from profiling)
```
Submission     0.13 s
Acknowledgement 1.9 s (parallel)
Stage A        3.9 s
Stage B       ~47 s   ← ~70% — dominant
Teacher Review 0.14 s (off critical path)
Stage C       ~8–17 s ← one Sonnet call, doubles to ~17s on validator regeneration
Total         ~67 s
```
Not a UI problem. It is a Stage B *output-size* problem plus a Stage C *render-model / regeneration* problem.

## Core diagnosis
The Writing Knowledge Base is ALREADY built as data and ALREADY injected into Stage B:
- `instructional_objects.json` — 35 fully-enriched elements (definition, communicative_purpose,
  performance_structure, recognition_diagnostics, common_obstacles, next_developmental_moves,
  revision_strategies, related_elements, indicators_of_control, developmental_invitations, …). 0 gaps.
- `developmental_exit_criteria.json` — 15 elements (exit_criterion, dependencies, next_operation,
  failure_modes) + 16 canonical_explanations.
- `canonical_writing_model.json` — 13 domains.

But Stage B is asked to **re-emit** deterministic, KB-derivable content into its huge output JSON
every turn (performance structure, exit criterion, element relationships, dependencies, canonical
explanations, essay architecture). Regenerating that costs output tokens → the ~47 s. It also risks
inconsistency (the LLM paraphrases canonical knowledge differently each time).

## What is DETERMINISTIC (should be KB lookup, keyed on the chosen element) vs JUDGMENT (LLM keeps)

DETERMINISTIC — hydrate from KB in the backend AFTER the LLM names the element:
- `canonical_performance_structure`  → instructional_objects[el].performance_structure
- `element_communicative_purpose`    → instructional_objects[el].communicative_purpose
- `active_exit_criterion`            → developmental_exit_criteria[el].exit_criterion
- `element_relationships` / essay architecture → instructional_objects[el].related_elements + build_instructional_network()
- `developmental_dependencies` (canonical) → developmental_exit_criteria[el].dependencies
- canonical explanation (already looked up) → CANONICAL_EXPLANATIONS[el]
- instructional strategies / `next_developmental_moves` / revision_strategies → instructional_objects[el]
- `next_developmental_step` (canonical) → developmental_exit_criteria[el].next_operation

JUDGMENT — the LLM's unique contribution, KEEP in Stage B output:
- interpret the student's writing (student_current_organization, reader_construction)
- identify the developmental bottleneck (primary_developmental_tension, diagnosed_opportunities)
- select the instructional focus (primary_target / active_instructional_element)
- nuanced calls: sufficiency_for_next_step, required_dependency (which one applies HERE),
  intervention type, instructional_mode, evidence_of_developmental_movement, developmental_profile_update

Target pipeline:
```
Student writing → developmental DIAGNOSIS (LLM, small) → KB LOOKUP (deterministic) → instructional plan → Stage C render
```

## Proposed sequencing (each step independently testable; benchmark-gated)

**Step 1 — KB audit & consolidation (LOW risk, data only).**
Confirm every canonical element the engine can target has: definition, communicative_purpose,
performance_structure, canonical_explanation, exit_criterion, related_elements, next_operation,
strategies. Fill any gaps. Add a single `element_key` normalization so lookups are reliable
(reuse COACHING_SYNONYMS / `_element_key_for`). Deliverable: a KB coverage report.

**Step 2 — Deterministic "plan hydrator" (LOW/MED risk, additive).**
Backend function `hydrate_plan(element_key, dep_key)` that assembles ALL deterministic scaffolding
from the KB. Wire it into `_build_coaching_plan` so Stage C stops depending on LLM-emitted
deterministic fields (it already uses CANONICAL_EXPLANATIONS; extend to performance_structure,
exit_criterion, relationships, next_operation, strategies). No Stage B change yet → no behavior change;
verify Stage C output unchanged/improved on a spot set.

**Step 3 — Slim the Stage B OUTPUT schema (HIGHER risk, GATED by benchmark).**
Remove the deterministic fields from what Stage B is REQUIRED to emit (keep the judgment fields).
Smaller required output → fewer generated tokens → faster Stage B. The reasoning instructions stay;
only the output contract shrinks, and the removed fields are hydrated by Step 2.
VALIDATION GATE: run the 66-case benchmark, Compare-Two-Runs vs a frozen pre-change baseline; the
distribution of chosen targets / verdicts must not regress. Roll back if it does.

**Step 4 — Stage C speed (MED risk, GATED).**
(a) Trial Claude Haiku 4.5 for the render (must pass the deterministic validator + a quality spot check).
(b) Reduce regeneration rate: audit the `_READYMADE_RE` false-positive; pre-instruct the renderer
against the single most-tripped rule. Re-measure gen1/gen2/calls with the existing timers.

## Guardrails
- Do NOT make Stage B "think less" (no reasoning removed); only stop it from RE-TYPING KB facts.
- Instructional experience frozen: student coaching sequence + Teacher Review four-question mirror unchanged.
- Every engine-touching step is validated against the 66-case benchmark before it stands.
