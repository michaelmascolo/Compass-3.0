# Phase II — CIO #3: EXPLANATION (calibrated + verified)
Additive calibration. Explanation treated as a DISTINCT object, not an extension of Evidence.
Architecture / Decision flow / DB / audit / UI unchanged. Verified live.

## What changed (additive)
- `MINIMAL_OBJECTS["Explanation"]`: essence now covers HOW **and WHY** without overreach; indicators
  separate merely-stated / implicit / summary-as-interpretation / superficial / overstated /
  unsupported-reasoning / explicit-causal. Variations expanded to all seven. Teaching strategy:
  confirm claim + adequate evidence first; then have the WRITER name the causal/logical relationship;
  never supply the explanation.
- `_SEL_SYS`: Explanation is the focus ONLY when a clear task-answering claim AND adequate/relevant
  evidence already exist and the unstated/faulty reasoning is the highest-leverage gap; it must not
  replace a Central Claim or Evidence problem; name the explanation issue in developmental_variation.

## Verification corpus (clear claim + adequate evidence, varied reasoning; + controls)
| Sample | Condition | Selected | Verdict |
|---|---|---|---|
| X1 | evidence merely stated | **Explanation** (implicit/no reasoning) | ✓ |
| X2 | implicit + thin evidence | Evidence (adequacy: "one district, one year") | ✓ One Thing Rule (evidence deeper) |
| X3 | summary mistaken for interpretation | **Explanation** ("restates what the study showed, not *why*") | ✓ subtle hit |
| X4 | superficial + correlational evidence | Evidence (relevance/adequacy) | ✓ defensible boundary |
| X5 | overstated reasoning | **Explanation** (quotes the overreach, "does a single study prove that?") | ✓ subtle hit |
| X6 | unsupported reasoning introduced | **Explanation** ("developers are greedy" unbacked premise) | ✓ subtle hit |
| X7 | explicit causal (present) | **Explanation** (pushes to unpack further) | ~ slight over-selection, defensible |
| CTRL | no evidence | Evidence, NOT Explanation | ✓ One Thing Rule |
| CTRL | unclear claim | Central Claim | ✓ One Thing Rule |

## The 10 required distinctions — all exercised
merely stated (X1) · interpreted vs not (X3) · explicit connection (X7) · implicit connection (X1,X3) ·
superficial (X4) · causal/logical relationship (X5,X7) · overstates support (X5) · unsupported reasoning
(X6) · summary-vs-interpretation (X3) · why-the-evidence-matters (dialogues in X1/X3/X7 push exactly this).

## Strengths
- Nails the hardest distinctions: summary-as-interpretation, overstatement, unsupported premises.
- Dialogue quotes the writer's own overreach / restatement and asks THEM to supply the reasoning —
  ownership fully preserved; never writes the explanation (action=ask_question throughout).
- One Thing Rule respected both directions: defers UP to Central Claim (unclear claim) and stays on
  Evidence when the evidence itself is thin/off-point (X2, X4), rather than polishing reasoning atop
  weak support.

## Watch items (calibration, not defects)
- Evidence/Explanation boundary leans to Evidence when evidence adequacy/relevance is questionable
  (X2, X4). Pedagogically sound (don't reason atop thin evidence) but means "superficial explanation +
  borderline evidence" is usually coached as Evidence.
- X7: near-complete explicit reasoning still selected Explanation for further unpacking — mild
  over-selection; reasoning was genuinely tightenable, so acceptable.

## Backward compatibility
Content-only edits to compass_structure_engine (Explanation object + selector guidance). No DB/audit/
flow/UI change. consolidated_v2 default path healthy (9/9 corpus completed). CIO#1/#2 behavior intact.
