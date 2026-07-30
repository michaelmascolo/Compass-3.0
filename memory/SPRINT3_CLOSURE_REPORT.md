# Sprint 3 — Closure Report: Instructional Decision Engine

**Date:** 2026-07-30 · **Status:** VERIFIED — Sprint 3 **16/16**; Sprint 1 **11/11**; Sprint 2 **12/12**;
Stage B/C engine unchanged (`SYSTEM_MESSAGE` hash still `1c485e2c13d7b8ff`).
**Recommendation:** **ACCEPT & FREEZE Sprint 3.**

Each live coaching turn now selects exactly ONE instructional target through an explicit, evidence-based
decision process (A–F) and writes the structured decision into persistent state **before** the learner-
facing response is presented. Target selection only — no new dialogue, no scaffolding sequences, no CIO
knowledge-base rewrite.

## 1. Files created / modified
- **Created** `backend/compass_decision_engine.py` — the decision engine: canonical priority order,
  prerequisite map, evidence normalization, the pure A–F `decide()`, guards DE-01..DE-05, live
  `decide_for_session()`, and `apply_teacher_target_override()` (TC-02).
- **Created** `backend/tests/sprint3_decision_tests.py` — certification tests 1–12 + guard checks + TC-02.
- **Modified (additive only)** `backend/compass_foundation.py` — added optional Sprint-3 fields to
  `InstructionalState`; extended the diagnostic-trace payload with the decision block; added
  `POST /api/instructional-state/{id}/target-override` (TC-02).
- **Modified (additive only)** `backend/server.py` — ONE additive call in `_run_reasoning` after the
  Sprint-2 bridge and before the session write: `compass_decision_engine.decide_for_session(...)`.
- **Modified (additive only)** `frontend/src/components/DiagnosticTrace.jsx` — added the read-only
  "Instructional Decision (Sprint 3)" section.

## 2. Exact change surface
Decision logic lives entirely in the new isolated module. `server.py` gained a single best-effort call
(wrapped in try/except so it can never break a live turn). `compass_foundation.py` gained optional fields
+ trace fields + one endpoint — no existing field, guard, or behavior changed (Sprint-1/2 tests still
pass). No modification to Stage B/C, the SYSTEM_MESSAGE, CIO knowledge content, or legacy session records.

## 3. New persistent fields (all optional, backward-compatible; on `InstructionalState`)
`demonstrated_strengths`, `strength_status`, `candidate_instructional_objects`,
`selected_instructional_object`, `selected_object_definition`, `structural_prerequisite_status`,
`conceptual_prerequisite_status`, `observed_selection_evidence`, `priority_rationale`, `deferred_targets`,
`decision_status`, `decision_confidence`, `decision_uncertainty`, `engine_recommendation`
(preserves the original recommendation across a teacher override), `decision_requirement_ids`,
`decision_timestamp`.

## 4. New requirement IDs / guards
- **DE-01** — exactly one active instructional target OR an explicit blocked/no-target status.
- **DE-02** — the selected target is supported by ≥1 OBSERVED evidence record.
- **DE-03** — no HYPOTHESIZED/UNKNOWN item is treated as an observed fact (selection uses OBSERVED only).
- **DE-04** — missing/contradictory evidence produces a blocked state rather than an invented decision.
- **DE-05** — prohibited personal attributions never influence target selection (filtered before A–F).
- **TC-02** — a teacher override is honored, separately recorded, preserves the original engine
  recommendation, is visible in the trace, and generates an append-only audit event; never treated as
  evidence about the learner.
Decision-status vocabulary: READY, BLOCKED_INSUFFICIENT_EVIDENCE, BLOCKED_CONTRADICTORY_EVIDENCE,
BLOCKED_PREREQUISITE_UNKNOWN, TEACHER_OVERRIDE, and **NO_TARGET_SUFFICIENT** (an additive value to honestly
represent Test 6's "no-current-target" state without inventing a weakness; treated as an explicit
non-active status for DE-01).

## 5. Test results — 16/16 (`python3 tests/sprint3_decision_tests.py`)
| Test | Required | Result |
|---|---|---|
| T1 no thesis / polished sentences | select Thesis, not Sentence Construction | PASS (Thesis, READY) |
| T2 clear claim, no evidence | select Evidence after confirming claim | PASS (Evidence, prereq MET) |
| T3 evidence present, relationship unexplained | select Explanation, don't ask for more evidence | PASS (Explanation) |
| T4 competing paragraph ideas | Paragraph Main Point before sentence refinement | PASS |
| T5 mechanical transition, unclear relationship | underlying relationship, not a new transition word | PASS (→ Explanation) |
| T6 strong writing | no invented weakness | PASS (NO_TARGET_SUFFICIENT, no target) |
| T7 insufficient evidence | block + UNKNOWN, no invented target | PASS (BLOCKED_INSUFFICIENT_EVIDENCE) |
| T8 contradictory evidence | block/uncertain, no silent choice | PASS (BLOCKED_CONTRADICTORY_EVIDENCE) |
| T9 multiple weaknesses | store candidates, select exactly one | PASS (1 selected, 3 deferred) |
| T10 teacher override | preserve original + honor teacher, log both | PASS (engine_rec=Evidence, selected=Thesis) |
| T11 personal attribution | suppress from selection evidence | PASS (suppressed; selection unaffected) |
| T12 persistence-before-presentation | decision exists before learner-visible response | PASS (real turn; decision persisted) |
| guards (ready / blocked / no-target) | DE-01..DE-05 pass | PASS ×3 |
| TC-02 live | override honored + separately recorded on real state | PASS (selected=Conclusion, engine_rec preserved) |

## 6. Regression — Sprint 1: 11/11 · Sprint 2: 12/12
Both suites re-run green after Sprint 3. Stage B `SYSTEM_MESSAGE` hash unchanged (`1c485e2c13d7b8ff`).

## 7. Trace evidence (real coaching turns)
Screenshot captured (`?trace=<state_id>&role=teacher`). The read-only, teacher/admin-gated trace now shows
the "Instructional Decision (Sprint 3)" section for a real turn: Decision status `READY · confidence
medium`; Candidate targets [Reader Orientation, Thesis]; Selected target **Reader Orientation** (+brief
definition); Observed evidence (selection); Prerequisite status (structural/conceptual); Priority
rationale; Deferred targets [Thesis]; Decision uncertainty; Decision requirement IDs DE-01..DE-05; decided
timestamp. No numerical score; no learner-deficiency language; students receive HTTP 403.

## 8. Known limitations
- On live turns the decision engine consumes the frozen engine's `structural_reasoning`; object
  normalization is keyword-based, so element labels that don't map to a canonical object are ignored
  (conservative — can cause `strength_status=UNKNOWN` rather than inventing a strength, which is correct).
- The full-essay certification scenarios (T1–T11) are validated at the decision-logic layer with explicit
  OBSERVED evidence inputs (the engine's true input contract is persistent state, not raw essays); T12
  validates the live path end-to-end.
- Conceptual prerequisite status is generally `UNKNOWN`/`NOT_MET` from observable signals only (never
  inferred from the learner's mind), by design.
- Decision writes are best-effort (never block a live turn); a fault is logged, not surfaced to the learner.

## 9. Confirmation
Dialogue, scaffolding ladder, Stage B/C methodology, and CIO knowledge content were **not redesigned**.
Only object NAMES are referenced. Sprint 1 and Sprint 2 behavior is unchanged (additive fields/endpoint
only). Legacy session records were not modified. The persistence-before-presentation rule holds on the
production path (decision written before the learner-visible turn).

## 10. Recommendation
**Accept and freeze Sprint 3.** Sprint 4 not begun.
