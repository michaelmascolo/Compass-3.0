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
The LLM's UNIQUE contribution: interpret THIS student's writing and decide. Stage B owns judgments
that depend on the specific draft: interpretation (frameworks M6–M14, structural elements
present/absent), the developmental bottleneck, selection of the instructional object, selection of
the strategy/resources (from the KB menu), the dependency decision, instructional sequencing,
sufficiency, evidence, calibration.

Stage B does NOT need to output canonical knowledge whose ONLY role is to communicate a decision
(cross-references, criteria) — those are hydrated from Layer 1. HOWEVER, some canonical content is
**epistemically active** during reasoning (see the refined Mixed definition below): the model
articulating it demonstrably stabilizes its judgment. Such content REMAINS in the Stage B reasoning
process even though it is also hydrated downstream for consistency.

### Field roles (refined 2026-06-29 after the Group 1 ablation)
- **Judgment** — depends on this student's paper. Lives in Stage B.
- **Deterministic-communicative** — student-independent AND its only role is to communicate/express
  a decision downstream. Safe to remove from Stage B output; hydrated from Layer 1.
- **Mixed (deterministic-but-epistemically-active)** — deterministic in CONTENT, but the act of the
  model producing it during reasoning helps CONSTRUCT the decision. Must remain in Stage B reasoning;
  also hydrated downstream. Removing it changes the judgment even though the content is fixed.
  *Empirically established members:* `element_communicative_purpose`, `canonical_performance_structure`
  (Group 1 ablation: removing them shifted `object` above its noise floor → reasoning scaffold).

## Layer 3 — Instructional Communication (Stage C)
Expresses the plan as supportive, developmentally appropriate coaching while preserving learner
agency. Stage C chooses WORDING, not instructional architecture:
- renders the six-function Orientation Plan (recognition → object → canonical explanation →
  architecture fit → transferable strategy → transition into ONE learner operation),
- constrained by the deterministic validator: names the target, no disciplinary overreach, no
  prompt leakage, no ready-made student answer, all six orientation functions present.

## The permanent boundary (Stage B contract)
Stage B is REQUIRED to output judgment fields + Mixed (epistemically-active) fields. It need NOT
output deterministic-communicative fields (pure cross-references/criteria), which are hydrated.
- **KEEP in Stage B (Mixed, reasoning-critical):** `element_communicative_purpose`,
  `canonical_performance_structure` — deterministic content, but reasoning scaffold (Group 1
  ablation proved removal shifts the object). Also `selected_developmental_resources`,
  `dependency_rationale`, `next_developmental_step` (mixed, pending isolation).
- **Migration candidates (Deterministic-communicative, pending single-field ablation):**
  `element_relationships`, `developmental_dependencies`, `active_exit_criterion` — tested ONE at a
  time against the noise floor (Group 2). Removed only if `object` stays at its noise floor.

## Certification rule for any change touching this boundary
A change is acceptable ONLY if instructional JUDGMENT remains equivalent on the 66-case benchmark:
instructional object, developmental bottleneck, supporting evidence, instructional strategy,
dependency decision, instructional sequence, exit criterion, next step, student coaching, Teacher
Review. Textual similarity is NOT the criterion — instructional judgment is.
