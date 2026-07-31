# Calibration Investigation 01 — the Central Claim selection tendency
Phase: instructional calibration (architecture FROZEN). Read-only; NO code changed.
Method: ran the REAL production selector `compass_structure_engine.select_structure` on 14
authentic middle-range samples concentrated in the borderline zone ("claim present but does
not fully answer the task"), alongside an INDEPENDENT "greatest-learning" second-opinion prompt
(Sonnet, offline) instructed to weigh claim-first vs act-now-on-a-lower-structure tradeoffs.

## Headline finding — the concern is NOT supported; the opposite risk exists
- Engine selected **Central Claim in 8/14**. The independent learning-leverage judge selected
  **Central Claim in 14/14**, and answered `lower_structure_would_help_more = False` in **all 14**.
- Engine == learning-optimal in 8/14. In **all 6 divergences the engine picked a DEPENDENT
  structure** (Evidence ×1, Explanation ×2, Definition ×2, Reader Orientation ×1) where the
  judge said Central Claim was higher leverage.
- Net: Central Claim is **not over-selected**. If anything the engine **intermittently
  UNDER-selects** it — diverting to a support structure when the writer has surface material
  (a stat, an anecdote, a key term) even though the governing claim does not yet take a
  contestable position that answers the task.

## Why (representative divergences)
- social_broad / games_harm: engine → Explanation (connect the study to the claim); judge →
  "the claim is too vague to anchor that reasoning; fixing the claim multiplies the value of all
  existing and future evidence."
- uniforms_bully: engine → Evidence (strengthen the anecdote); judge → "no governing arguable
  position; a clear claim gives every sentence a job."
- zoos_ethics / voting_age: engine → Definition ("cruel"/"mature enough" undefined); judge →
  "define-first props up a fuzzy thesis; set the contestable claim first."
- sports_required: engine → **Reader Orientation on a single-paragraph task** — a genuine
  mis-pick (whole-piece structure; should be not_applicable for one paragraph).

## Answers to the four investigation questions
1. **Does Central Claim truly have highest developmental leverage here?** Yes, in the borderline
   zone. Independent evaluation agrees 14/14. You cannot productively teach support for a claim
   that has not yet taken the task's position — the tendency is pedagogically sound, not a defect.
2. **Would another structure sometimes produce greater learning?** Not in this evidence
   (`lower_helps_more = False` 14/14). The demonstrated risk runs the other way: teaching
   Evidence/Explanation/Definition too early, reinforcing an uncommitted claim.
3. **Should the priority ordering change?** **No.** Central-Claim-above-support is validated.
   Recommended calibration is to the *selection criterion*, not the order: do not select a
   dependent structure while the Central Claim is missing/partial **with respect to the task**.
4. **Do Canonical Instructional Objects need refinement?** Minor, calibration-level only:
   - Central Claim "present" indicator -> "takes a contestable position that answers the
     assignment's question" (not merely "makes some claim"); add a selection guard: defer
     Evidence/Explanation/Elaboration/Definition/Transition/Closure until the claim answers the task.
   - Reader Orientation: firmly not_applicable for single-paragraph units.
   - Definition: select only when a load-bearing term is ambiguous AND the claim already answers
     the task; otherwise defer to Central Claim.

## Limitations (state honestly before acting)
- The second opinion is itself an LLM and may share model-level bias toward Central Claim; two
  LLMs agreeing is weaker than expert-teacher agreement. **Triangulate with human teacher review
  on authentic student corpora before implementing any calibration.**
- N=14, hand-authored to sit in the borderline zone — direction is clear, magnitudes are not.
- No architectural changes; the divergences are calibration questions, not defects (except the
  single Reader-Orientation-on-one-paragraph mis-pick, which is a canonical-object applicability fix).

## Recommended next step (for approval — do not implement yet)
Run a teacher-in-the-loop triangulation on a real student-writing set, then, if confirmed, a
calibration pass refining the three Canonical Instructional Objects above. No architecture change.
