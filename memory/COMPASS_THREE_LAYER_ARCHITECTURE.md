# Compass — Canonical Three-Layer Instructional Architecture

Status: CANONICAL DESIGN (ratified by product owner, 2026-06). Future development MUST preserve
these boundaries unless there is a strong empirical reason to revise them.

```
Layer 1 — INSTRUCTIONAL KNOWLEDGE   (Writing Knowledge Base)
        ↓  (deterministic hydrator)
Layer 2 — INSTRUCTIONAL JUDGMENT    (Stage B, the LLM reasoner)
        ↓  (deterministic Orientation Plan + hydrated plan)
Layer 3 — INSTRUCTIONAL COMMUNICATION (Stage C renderer, + validator)
```

## Layer 1 — Instructional Knowledge (Knowledge Base)
Defines writing itself, independent of any student. The permanent home of everything a skilled
writing teacher knows before seeing a paper.
- `instructional_objects.json` — 36 elements: definition, communicative_purpose, performance_structure,
  related_elements, functional_relationships, common_obstacles, next_developmental_moves,
  revision_strategies, indicators_of_control, stopping_conditions.
- `developmental_exit_criteria.json` — exit criteria, dependencies, next_operation, failure_modes,
  and the canonical_explanations.
- `canonical_writing_model.json` — domains.
Accessed only through the deterministic **hydrator** (`hydrate_element(element_key)`), the
`KB_ELEMENT_MAP`, and the six-slot **Orientation Plan** (`_build_orientation_plan`).
Versioned and corrigible; re-audited by `tests/kb_audit.py` (instructional completeness).

## Layer 2 — Instructional Judgment (Stage B)
The LLM's UNIQUE contribution: interpret THIS student's writing and decide. Stage B owns, and only
owns, judgments that depend on the specific draft:
- interpretation of the student's writing (frameworks M6–M14, structural elements present/absent),
- the developmental bottleneck (primary tension),
- selection of the instructional object (`active_instructional_element` / `primary_target`),
- selection of the instructional strategy/resources (from the KB menu),
- dependency decision (which prerequisite applies HERE),
- instructional sequencing (continue/consolidate/release/shift; next step),
- sufficiency judgment, evidence supporting the diagnosis, confidence/calibration.
Stage B does NOT define or re-state canonical knowledge (purposes, performance structures,
relationships, dependencies, exit criteria, explanations) — those are hydrated from Layer 1.

## Layer 3 — Instructional Communication (Stage C)
Expresses the plan as supportive, developmentally appropriate coaching while preserving learner
agency. Stage C chooses WORDING, not instructional architecture:
- renders the six-function Orientation Plan (recognition → object → canonical explanation →
  architecture fit → transferable strategy → transition into ONE learner operation),
- constrained by the deterministic validator: names the target, no disciplinary overreach, no
  prompt leakage, no ready-made student answer, all six orientation functions present.

## The permanent boundary (Stage B contract — post Group 1+2 migration)
Stage B is REQUIRED to output ONLY judgment (+ mixed, pending separation). It is NOT required to
output canonical, student-independent knowledge; that is hydrated. Specifically, Stage B no longer
emits: `element_communicative_purpose`, `canonical_performance_structure`,
`element_relationships`, `developmental_dependencies`, `active_exit_criterion` (all → Layer 1 via
the hydrator). Mixed fields (`selected_developmental_resources`, `dependency_rationale`,
`next_developmental_step`) remain in Stage B until their deterministic core is cleanly separated.

## Certification rule for any change touching this boundary
A change is acceptable ONLY if instructional JUDGMENT remains equivalent on the 66-case benchmark:
instructional object, developmental bottleneck, supporting evidence, instructional strategy,
dependency decision, instructional sequence, exit criterion, next step, student coaching, Teacher
Review. Textual similarity is NOT the criterion — instructional judgment is.
