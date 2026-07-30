# Sprint 2 — Closure Report: Engine Bridge

**Date:** 2026-07-30 · **Status:** VERIFIED — 12/12 bridge e2e checks pass; Sprint 1 unchanged (11/11).
**Objective delivered:** "The live coaching engine becomes both a CONSUMER and a PRODUCER of persistent
instructional state. Every instructional interaction begins by reading the current instructional state and
ends by writing the updated instructional state." No new instructional logic was added; the frozen Stage
B/C engine is untouched (SYSTEM_MESSAGE hash still `1c485e2c13d7b8ff`).

---

## New foundational architectural rule (implemented)
> "No instructional decision may exist only in generated text. Every instructional decision must be
> represented in persistent structured state before it is presented to the learner."

**How it is enforced:** the producer write runs inside `_run_reasoning` immediately after `_finalize_turn`
and **before** the `db.sessions.update_one` that makes the completed (learner-visible) turn durable. So by
the time any learner can poll the completed invitation, the structured decision + evidence + audit already
exist. The audit `instructional_turn` event stores the generated invitation in `generated_response`,
tying the presented text to the structured decision. Verified in test (`generated_text_tied_to_state`).

---

## Change surface (additive, non-invasive)
- `backend/compass_foundation.py` — added the Engine Bridge: `get_or_create_state_for_session`,
  `begin_instructional_turn` (CONSUMER), `record_instructional_turn` (PRODUCER), and a
  `GET /api/instructional-state-by-session/{session_id}` lookup. Added **optional, defaulted** fields to
  `InstructionalState` (`reason_for_selection`, `prerequisite_status`, `current_learner_task`,
  `last_learner_response`, `last_revision_produced`, `exit_criterion_description`, `turns_recorded`).
  These are backward-compatible extensions justified by the Sprint-2 dependency — no existing Sprint-1
  field or behavior was changed (Sprint-1 tests still pass 11/11).
- `backend/server.py` — TWO best-effort hooks in `_run_reasoning`: (1) CONSUMER read after the session
  loads; (2) PRODUCER write after `_finalize_turn`, before the turn is persisted/presented. Both wrapped
  in try/except so a bridge fault can never break the live coaching turn.
- `backend/tests/sprint2_bridge_test.py` — the e2e test.

**Not touched:** Stage B/C reasoners, CIO/dialogue logic, Knowledge Base, Organizing Thought, Sprint-1
guards/audit semantics.

---

## Per-turn persisted fields (all required fields covered)
Mapped from the frozen engine's `theory` output for every live turn:

| Required field | Source (theory / turn) |
|---|---|
| Current writing snapshot | learner content → `current_student_text` + `revision_history` |
| Demonstrated strengths | `structural_reasoning.elements_present`, `observed_differentiations/integrations/coordinations` → OBSERVED |
| Observed evidence | `instructional_reasoning.student_current_organization`, `evidence_of_developmental_movement` → OBSERVED evidence records |
| Hypothesized developmental needs | `instructional_reasoning.primary_developmental_tension`, `required_dependency`, `structural_reasoning.elements_absent` → HYPOTHESIZED |
| Unknowns | no object selected / exit undeterminable / `unresolved_tensions` → UNKNOWN |
| Selected Canonical Instructional Object | `scaffolding_control.primary_target` (⁄ `active_instructional_element`) |
| Reason for selection | `scaffolding_control.prioritization_rationale` |
| Structural & conceptual prerequisite status | `required_dependency` + `dependency_status` + `developmental_dependencies` → `prerequisite_status` |
| Current dialogue state | `scaffolding_control.cycle_status` |
| Current support level | `instructional_reasoning.degree_of_student_control` ⁄ `instructional_mode` |
| Current learner task | the invitation ⁄ `next_student_act` |
| Learner response | the student turn (`kind: content`) |
| Revision produced | learner content on a `revise` turn |
| Exit criterion status | `sufficiency_for_next_step` → met/not_met/UNKNOWN (+ description) |
| Advancement decision | recorded from `sufficiency` / `cycle_status` / `release` (engine's decision; not a new gate) |
| Teacher overrides | carried from state; latest attached to the audit event |
| Requirement IDs | VA-05, DS-01, DS-02, VA-06, VA-07 (+ TC-01 when an override is present) |
| Timestamp | every state + audit record |

Evidence is stored append-only in `evidence_records` with strict OBSERVED / HYPOTHESIZED / UNKNOWN
categories; the state's per-turn lists reflect the CURRENT reading. DS-02 suppression is applied: an
engine string that reads as a prohibited personal attribution is never stored as an OBSERVED fact (logged
as `evidence_suppressed`).

---

## Test results — 12/12 PASS (real live coaching turn)
`cd /app/backend && python3 tests/sprint2_bridge_test.py`
- live_turn_completed (real Stage B+C invitation, 1152 chars)
- bridge_produced_instructional_state (turns_recorded=1)
- selected_object_persisted → "Thesis — turn broad label into a contestable, focused claim…"
- learner_response_persisted · exit_status_valid (not_met) · epistemic_lists_present (6 OBSERVED / 6 HYPOTHESIZED / 1 UNKNOWN)
- consumer_read_logged (`turn_started`) · producer_write_logged (`instructional_turn`)
- audit_has_requirement_ids [VA-05, DS-01, DS-02, VA-06, VA-07] · audit_has_validation_results (5 guards)
- **generated_text_tied_to_state** (audit.generated_response == the presented invitation)
- audit_output_state_complete (all decision fields present)

Screenshot captured: `?trace=<state_id>&role=teacher` now renders the REAL bridged turn (Current target =
Thesis; OBSERVED strengths; HYPOTHESIZED "broad evaluative label, not a contestable claim"; UNKNOWN
"'bad' may mean harmful to friendships…"; support=scaffolded; exit=not_met).

Backward compatibility: Sprint-1 suite still 11/11.

---

## Deferred (per owner direction)
- **Wire Trace into navigation** — deferred (convenience, not architectural).
- **Specification reconciliation** — only session→state identifiers reconciled as needed for Sprint 2;
  full terminology/field-name alignment deferred until Canonical Specification v2.1 is frozen.
- **Stage B perturbation methodology** — deferred completely (research, not implementation).

## Known limitations / notes
- The default production path is `exhaustive` (no streaming) → the rule holds strictly. The opt-in
  `triage_experimental` path streams a partial invitation before finalize; its structured write still
  occurs at finalize, so a partial can render before persistence on that experimental path only. Flagged
  for tightening if triage is ever promoted.
- Bridge writes are best-effort (try/except) so they never break a live coaching turn; a bridge fault is
  logged (`[bridge] … failed`) rather than blocking the learner. Can be made strict (block-on-fault) once
  the Canonical Specification mandates it.
- State is keyed 1:1 by `session_id` for live turns.
