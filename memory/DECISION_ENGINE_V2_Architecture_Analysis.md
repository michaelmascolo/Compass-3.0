# Decision Engine V2 — Pre-Implementation Architecture Analysis
Read-only analysis. No code changed. Date: 2026-07 (post Revision Package 5).

## Question
Where are instructional decisions currently made? Map every contributor, modifier,
prompt, and consumer; state whether decision-making is centralized or distributed;
recommend whether V2 (A) replaces one isolated component, (B) requires consolidation
first, or (C) needs a different architecture.

## Scope note
There are now FOUR runtime "reasoning_mode" paths that each make instructional
decisions differently: `exhaustive` (default/frozen), `triage_experimental`,
`governance_v2` (flagged), and `structure_v5` (Revision Package 5, new). The default
path is the tangled one; `structure_v5` is already centralized.

---

## 1. Components that SELECT the instructional target

| # | Module / function | Role in selection | Path |
|---|---|---|---|
| S1 | `server._select_relevant_domains` (~L2744) — STAGE A selector LLM | Decides which canonical domains + instructional objects are loaded → constrains what CAN be taught | exhaustive |
| S2 | `server.SYSTEM_MESSAGE` (~L842) via `_run_engine`/`_build_prompt` — STAGE B reasoner LLM | **Primary target selector**: sets `theory.scaffolding_control.primary_target`, `instructional_reasoning.active_instructional_element`, `integration_calibration.primary_framework` | exhaustive |
| S3 | `compass_decision_engine.decide_for_session` → `decide` (A–F) | **Independent SECOND selector**: re-derives a target from `theory.structural_reasoning` via normalization + prerequisites; can disagree with S2 | exhaustive |
| S4 | `triage_experiment.run_triage_pipeline[_streaming]` | Own reasoner that sets `scaffolding_control.primary_target` | triage |
| S5 | `governance_v2.run_governance_v2` | Two-layer reasoner producing `primary_target` | governance_v2 |
| S6 | `compass_structure_engine.select_structure` (STEP 1) | **Sole decider** on its path: highest-priority unmet structure | structure_v5 |

## 2. Components that MODIFY / FILTER / REINTERPRET the decision

| # | Module / function | What it does to the decision |
|---|---|---|
| M1 | `server._build_coaching_plan` + `_coaching_plan_prompt` + `_render_coaching` + `_validate_coaching` (STAGE C) | Renders learner text bound to S2's target; `_validate_coaching` can flag/re-anchor emphasis (target vs `required_dependency`) and re-run — a bounded reinterpretation |
| M2 | `compass_foundation.record_instructional_turn` (Sprint 2 bridge) | Re-expresses S2's decision into persistent-state fields (`current_instructional_object`); a second representation |
| M3 | `compass_decision_engine._write_decision_onto_state` | Overwrites M2's state value with S3's independently-derived target |
| M4 | `compass_coaching_controller.select_response` (RP4) | **Gates/replaces** the learner-facing text by CASE 1–4; for CASE 2/3/4 substitutes canned controller text, discarding S2/M1 output |
| M5 | `compass_foundation.add_override` / `teacher_target_override` + `apply_teacher_target_override` | Human override: sets `selected_instructional_object` + `TEACHER_OVERRIDE`; honored by S3/S6 next turn |
| M6 | `compass_structure_engine.run` (override branch) | Applies M5 override on the structure_v5 path; preserves engine recommendation |

## 3. Prompts that participate in instructional decision-making
- STAGE-A selector prompt (inside `_select_relevant_domains`) — retrieval decision.
- **`SYSTEM_MESSAGE`** (Stage B reasoner, ~L842–1119) — the dominant decision prompt (M6–M14 frameworks + M11 controller + governed canonical instruction).
- Stage C `_coaching_plan_prompt` + `_render_coaching` system prompt — rendering/re-anchoring.
- `NOTICING_SYSTEM_MESSAGE` (~L1977) — interim noticing beats (reads the forming decision).
- `triage_experiment` prompts (triage + focused analysis).
- `governance_v2` layer-1 / layer-2 prompts.
- RP5 `compass_structure_engine._SEL_SYS` (selection), `_DLG_SYS` (dialogue), `_CLOSURE_SYS` (no-target).
- NOTE: **Sprint 3 (`decide`) uses NO prompt** — it is deterministic Python over the reasoner's structural output.

## 4. Components that merely CONSUME the decision
- `server._finalize_turn` (persist turn + theory; compute movement).
- `frontend DiagnosticTrace.jsx` (reads `/trace`), `DevelopmentPanel.jsx` (reads `theory`), `StudentWorkspace.jsx` / `PublicPreview.jsx` (read turn content).
- `compass_foundation` trace/audit endpoints.
- `_update_preview_analytics`.
- Test harness `_harness_run_turn` + separate LLM evaluator `_evaluate_case` (meta-judgement of quality, not an instructional decision).

## 5. Centralized or distributed?
**Distributed and REDUNDANT on the default (`exhaustive`) path.** The single "what to
teach" decision is made or re-made in at least three independent places every turn —
S2 (reasoner), S3 (Sprint-3 A–F engine), and it is re-anchored/replaced downstream by
M1 (Stage C validator) and M4 (RP4 gate) — spread across 5+ modules, plus two more
whole alternate deciders (S4 triage, S5 governance). These deciders can and do
**disagree** (the live walkthrough showed S2 producing a coherent "sharpen the central
claim" target while S3 emitted `BLOCKED_CONTRADICTORY_EVIDENCE`, and M4 then replaced
the good invitation with a generic "mixed signals" line).

**`structure_v5` (RP5) is the only centralized path**: S6 decides once, retrieval is
minimal, and the dialogue engine is contractually forbidden from re-deciding.

---

## Recommendation: **B (consolidate first) — and the consolidation already largely exists as RP5**

Option **A is not viable** for the default path: there is no single isolated component
to swap. Selection is smeared across S1→S2→S3 and reinterpreted by M1/M4, with S4/S5 as
parallel deciders. Dropping a "V2" beside this tangle adds a *sixth* decider and worsens
the redundancy the walkthrough exposed.

The correct move is **B, realized by promoting RP5's `compass_structure_engine` to be
Decision Engine V2** — i.e. converge on the already-centralized component rather than
build a new one alongside the old ones:

1. **Single authoritative decider.** `compass_structure_engine.select_structure` becomes
   the ONLY selector. Retire S3 (`decide_for_session`) as a live decider and demote M4
   (RP4 controller) — RP5's dialogue engine already replaces its gating role.
2. **Demote the Stage B reasoner (S2) off the student's decision + latency path.** Keep
   it, if wanted, only as an OPTIONAL advisory/telemetry lens for the teacher research
   view and the test harness — never as the thing that picks the target. This is what
   removes the ~55–95s cost and the S2↔S3 disagreement class of bugs.
3. **Keep Sprint 1–4 infrastructure as consumers only** (state, evidence, audit, teacher
   override) — no DB/audit/override redesign; they already work under RP5 unchanged.
4. **Fold S1 (Stage-A retrieval) into the structure decision** — RP5 already retrieves a
   single minimal object after selection, eliminating the separate retrieval decision.
5. **Alt paths (S4 triage, S5 governance) become dead/experimental** and should be
   flag-gated off the default so only ONE decision architecture is live for learners.

Net: V2 is not a new component but a **convergence** — make the one already-centralized
decider authoritative and turn every other decider into an advisor or a consumer. Only
option C (a wholly different architecture) if the product later needs multi-domain
decisions (reading, math), in which case `compass_structure_engine`'s generic
`MINIMAL_OBJECTS`/priority-order pattern is the seam to generalize — still one decider.
