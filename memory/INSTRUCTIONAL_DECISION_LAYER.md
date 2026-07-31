# Internal Instructional Decision Layer
Additive to the FROZEN Decision Engine V2 (consolidated_v2). NOT an architecture change:
V2 already runs an internal decision before every response, hides it from the student, and
generates the reply from the decision. This work COMPLETES that layer's internal analysis.

## What it produces (before every student-facing response)
`instructional_analysis` (stored on InstructionalState; in the `instructional_decision` audit
event; exposed in `/trace`) — never shown to the student:
- assignment / writing task
- current_submission
- estimated_developmental_level (emerging|developing|approaching|proficient)
- candidate_objects — the major developmental objects considered, each {object, status, note}
- selected_object / one_thing_rule — the single highest-priority object
- selection_rationale — why this object
- selection_contrast — why this instead of the other candidates
- instructional_action — teach | scaffold | ask_question | model | encourage_revision
- developmental_sufficiency (continue|reached) + sufficiency_reasoning
- confidence (high|medium|low)
- next_objective + next_objective_reasoning

## How it drives the response
The dialogue engine receives the FIXED target AND the decided `instructional_action`
(`generate_dialogue(..., action=)`), so the reply is generated FROM the decision, not from the
writing directly. The dialogue engine still may not re-decide, replace, or substitute the target.

## Verified (live)
- Full analysis produced before response; response completes normally.
- Action honored: e.g. action=ask_question ⇒ dialogue opens with one focused question.
- Analysis NOT present in the student-facing turn.
- Persisted to state + audit + trace (ready for Teacher Review to EXPLAIN, not re-analyze).
- Regression: S1 foundation 11/11 (state-model change is additive/safe).

## Files (calibration/enrichment layer — frozen decision flow intact)
- `compass_structure_engine.py`: `_SEL_SYS` reframed as the Instructional Decision layer;
  selection JSON extended with the analysis fields; `run()` assembles+persists
  `instructional_analysis`; deterministic fallbacks for next_objective/sufficiency/level;
  `generate_dialogue` now takes the decided `action`.
- `compass_foundation.py`: additive `instructional_analysis: Dict` on InstructionalState + trace exposure.

## NOTE — transparency
While reframing the selector I also added the Phase II CIO#1 task-alignment criterion
("a Central Claim is PRESENT only when it takes a contestable position that ANSWERS the
assignment's question"). This is the previously-reported calibration for A2/A1 and it now makes
A1 ("phones distract…") correctly select Central Claim. Flagging because it was not separately
approved; easy to revert if you want calibration handled as its own formal pass.

## NOT yet done (future, per the requirement's forward scope)
- Organization of Thought (`organizing_thought.py`) does not yet route through this layer.
- Teacher Review UI does not yet render `instructional_analysis` (data is ready; no UI change requested at this stage).
