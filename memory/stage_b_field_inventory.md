# Step 3 — Phase B: Stage B Field-by-Field Inventory

Classification principle (user): *If an experienced writing teacher would give the SAME answer
regardless of this student's paper → Deterministic (belongs in the Knowledge Base). If the answer
depends on THIS student's writing → Judgment (belongs in Stage B). Mixed = a deterministic core +
a per-student selection; keep in Stage B until it can be cleanly separated.*

Only **Deterministic** fields should disappear from the Stage B OUTPUT contract (they are hydrated
from the KB). **Mixed** fields remain until cleanly separable. Reasoning GUIDANCE in the prompt is
never removed — only OUTPUT requirements for deterministic fields.

## InstructionalReasoning (governed canonical instruction)
| Field | Class | Rationale / KB source |
|---|---|---|
| active_instructional_element | **Judgment** | which element to teach depends on the draft |
| student_current_organization | **Judgment** | describes this student's writing |
| primary_developmental_tension | **Judgment** | the bottleneck for this draft |
| next_student_act | **Judgment** | contextual scaffold move |
| evidence_of_developmental_movement | **Judgment** | change vs this student's prior turn |
| degree_of_student_control | **Judgment** | this student's control level |
| continue_consolidate_release_or_shift | **Judgment** | sequencing for this student |
| required_dependency | **Judgment** | which dependency applies HERE |
| dependency_status | **Judgment** | state for this student |
| sufficiency_for_next_step | **Judgment** | is THIS draft sufficient |
| element_communicative_purpose | **Deterministic** | KB `io.communicative_purpose` (hydrated) → MIGRATE |
| canonical_performance_structure | **Deterministic** | KB `io.performance_structure` (hydrated) → MIGRATE |
| selected_developmental_resources | **Mixed** | KB provides the menu; selection is judgment → keep |
| resource_selection_rationale | **Judgment** | why for this student |
| dependency_rationale | **Mixed** | canonical "why X precedes Y" is KB; applicability is judgment → keep |
| next_developmental_step | **Mixed** | canonical `exit.next_operation` is KB; contextual sequencing is judgment → keep |

## StructuralReasoning (unified structural reasoner)
| Field | Class | Rationale / KB source |
|---|---|---|
| entry_point, available_portion, hierarchy_level, structure_identified | **Judgment** | about this draft |
| elements_present / emerging / absent / unnecessary | **Judgment** | this draft's structure |
| hierarchical_triage_rationale | **Judgment** | leverage call for this draft |
| element_relationships | **Deterministic** | KB `io.related_elements` (hydrated) → MIGRATE |
| developmental_dependencies | **Deterministic** | KB `exit.dependencies` (hydrated) → MIGRATE |
| active_exit_criterion | **Deterministic** | KB `exit.exit_criterion` (hydrated) → MIGRATE |

## Framework lenses M6–M14 (communicative_purpose, paragraph/evidence/coherence/conclusion_function,
## scaffolding_control, reader_construction, revision_development, integration_calibration)
**All Judgment.** Every field analyzes THIS student's writing (purpose inferred, paragraph function,
evidence gap, coherence, reader model, revision growth, calibration). KEEP entirely.
Exception within scaffolding_control: `primary_target` = Judgment (the object selection).

## DevelopmentalTheory top-level (observed_differentiations, supporting_evidence, emerging_intentional_control, …)
**All Judgment.** Observations/evidence about this student. KEEP.

## Candidate/Selected Invitation, Intervention, Telos
**Judgment.** The invitation, selection basis, intervention content, and telos are per-student. KEEP.

## Migration groups (Deterministic only — removed from Stage B OUTPUT, hydrated instead)
- **GROUP 1 — canonical element knowledge:** `instructional_reasoning.element_communicative_purpose`,
  `instructional_reasoning.canonical_performance_structure`.
- **GROUP 2 — canonical structural relations:** `structural_reasoning.element_relationships`,
  `structural_reasoning.developmental_dependencies`, `structural_reasoning.active_exit_criterion`.

All 5 are ALREADY supplied to Stage C + Teacher Review by the deterministic hydrator, so removing
them from the Stage B output changes no downstream behavior — it only shrinks the generated JSON.
Pydantic models keep these fields (with defaults), so omission parses cleanly.

**Deferred (Mixed):** `selected_developmental_resources`, `dependency_rationale`,
`next_developmental_step` — keep until the deterministic core is cleanly separated from the
per-student selection in a later, separate migration.
