# Decision Engine V2 — Learner Execution Path (consolidated_v2)
From student submission to first AI response. Verified live 2026-07.

Default `reasoning_mode = consolidated_v2` (env flag `COMPASS_REASONING_MODE`,
rollback = `exhaustive`). RP5_MODES = ("consolidated_v2","structure_v5").

## STEP 0 — HTTP ingress  (NO decision)
`POST /api/sessions/{id}/interact` -> `server.interact()` (server.py ~L3600)
- Mongo read (session). Guards: empty (400), reflection terminal (409), concurrent turn (409).
- Append student Turn(complete) + placeholder AI Turn(processing); Mongo write.
- `asyncio.create_task(_run_reasoning(...))`; return immediately (disconnect-safe).

## STEP 1 — background dispatcher  (NO decision)
`server._run_reasoning()` (~L3441)
- Mongo read (fresh session).
- `compass_foundation.begin_instructional_turn()` -> get_or_create InstructionalState + `turn_started` AUDIT.
- mode in RP5_MODES -> `_finalize_structure_v5()` then RETURN.
- ⛔ NOT reached: Stage A `_select_relevant_domains`, Stage B `_run_engine`/SYSTEM_MESSAGE,
  Stage C `_render_coaching`, Sprint-2 `record_instructional_turn`, Sprint-3 `decide_for_session`,
  RP4 `select_response`, triage_experiment, governance_v2.

## STEP 2 — V2 finalize wrapper  (NO decision)
`server._finalize_structure_v5()` (~L3394)
- Mongo read (fresh session) -> `compass_structure_engine.run()`  ← the ONLY decision component.

## STEP 3 — DECISION ENGINE V2  `compass_structure_engine.run()`
- 3a get_or_create state (Mongo read).
- 3b record current_student_text / revision entry (in-memory).
- 3c teacher-override scan (state.teacher_overrides) — human authority, no LLM.
- 3d **LLM CALL #1 — select_structure()**  [Claude Haiku 4.5, `_SEL_SYS`, ~3.5KB]
      ← ★ THE SINGLE INSTRUCTIONAL DECISION POINT. Highest-priority structure not yet solid.
      Returns selected / status / developmental_variation / established / justification /
      instructional_intent / confidence. Deterministic name resolve+normalize.
- 3e **RETRIEVAL — retrieve_object(target)** : in-memory lookup of ONE minimal object
      (5 fields) from MINIMAL_OBJECTS. No document load, no DB fetch, no vector search.
- 3f authoritative decision assembly (deterministic): {override | null-target | target}
      -> decision_status / instructional_need / coaching_path. Override preserves engine_recommendation.
      This target is authoritative; nothing downstream may change it.
- 3g write decision onto InstructionalState (Mongo write), incl. developmental_variation, instructional_intent.
- 3h AUDIT `instructional_decision` (DE-01/DE-04/DE-06/VA-06 + validation results).
- 3i **LLM CALL #2 — generate_dialogue() | generate_closure()** [Claude Sonnet 4.6, `_DLG_SYS`/`_CLOSURE_SYS`, ~2.2KB]
      NOT a decision. Receives the FIXED target; may explain/scaffold/question/pace/preserve ownership.
      May NOT select/replace/reinterpret/re-diagnose. Ownership-guard regex on output.
- 3j AUDIT `coaching_dialogue` (coaching_path, one_target=True, consistent_with_decision=True by construction).
- 3k return {invitation, instructional_intent_obj, decision, _meta}.

## STEP 4 — persist AI turn  (NO decision)
`_finalize_structure_v5`: Mongo read (fresh) -> fill placeholder (content, status=complete,
reasoning_path=structure_v5) -> Mongo write. Log `[rp5] llm_calls=2 select=.. dialogue=.. total=..`.

## STEP 5 — consumers only (NO decision)
Frontend polls `GET /sessions/{id}`; teacher `?trace=<state_id>` -> `/instructional-state/{id}/trace`
(DiagnosticTrace.jsx) + `/audit`. Development Panel / preview analytics display only.

## Per-learner-turn totals
- LLM calls: **2** (Haiku select + Sonnet dialogue). Was ~3 (Stage A + Stage B + Stage C).
- Retrievals: **1 in-memory** minimal object (5 fields). Was: Stage-A load of full canonical sections.
- Instructional decision points: **exactly 1** (select_structure) + teacher override (human, recorded not remade).
- No second engine re-derives or replaces the target anywhere on the learner path.

## Remaining decision-authority duplication on learner path: NONE.
Other target-setters exist only OFF the learner path: teacher override (intended), and the
retained `exhaustive` rollback + offline harness/triage/governance (not learner-selectable under the flag).
