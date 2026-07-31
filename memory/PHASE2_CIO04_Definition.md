# Phase II — CIO #4: DEFINITION (calibrated object + evidence-based selection finding)
Additive calibration. Architecture / Decision flow / Instructional Decision layer / One Thing Rule /
DB / audit / UI unchanged. Definition treated as a distinct object about the CLARITY of concepts,
not the truth of claims or quality of evidence.

## What changed (additive, KEPT)
- `MINIMAL_OBJECTS["Definition"]`: essence now states it concerns concept clarity (not truth/evidence);
  indicators separate undefined / vague-ambiguous / too-broad / too-narrow / circular / inconsistent /
  everyday-vs-discipline. Variations expanded to all eight. Teaching strategy: select ONLY when an
  unclear/unstable concept is BLOCKING development or communication; rule out deeper claim/evidence/
  explanation problems first; writer states and sharpens the meaning themselves; use example/contrast;
  never supply the definition.
- `_SEL_SYS`: added the GLOBAL downstream-leverage principle — "when several objects could be improved,
  choose the one whose improvement yields the GREATEST downstream improvement, not the first detectable
  weakness" — and a Definition clause (select only when an unclear key concept blocks the writer; never
  over a more fundamental Central Claim/Evidence/Explanation; name the definition issue).

## Key empirical finding: Definition is a genuinely LOW-FREQUENCY object
Across 5 dedicated Definition samples + 2 strong-claim/undefined-term probes, the selector chose
Central Claim or Evidence every time, and this is DEFENSIBLE under the One Thing Rule:
| Sample | Selected | Why defensible |
|---|---|---|
| D1 cancel culture | Central Claim | claim itself vague/under-specified — higher leverage than the term |
| D3 AI inconsistent | Central Claim | reads as competing positions; claim unsettled |
| D4 growth | Central Claim | claim not yet a precise contestable position |
| assault_weapons | Evidence | term clear enough for task; thin evidence is the real gap |
| living_wage | Evidence | term clear enough; single thin data point is the gap |
Definition sits above Evidence but below Central Claim in priority; in single-paragraph argument,
writing with a fuzzy key term almost always ALSO has a vaguer claim or thinner evidence that is the
higher-leverage gap. Definition therefore wins only at a narrow intersection: a task-answering,
contestable claim + adequate evidence + a load-bearing term that genuinely blocks understanding.
That intersection DOES occur — earlier validation M08 ("cancel culture is destroying free speech")
selected Definition correctly.

## What we DID NOT do (and why) — evidence-based restraint
An attempt to make Definition surface more often by loosening the Central Claim "present" criterion
REGRESSED the frozen baselines (A2 amplified toward Evidence; E1 flipped Evidence->Central Claim) and
introduced prompt-perturbation instability WITHOUT surfacing Definition. Per the standing rule ("do not
change the Decision Engine unless calibration cannot solve it, and prefer no change"), the loosening was
REVERTED. Baselines re-confirmed after revert: E1->Evidence, X3->Explanation, broad->Central Claim,
multiple->Central Claim. Conclusion: Definition's low frequency is correct behavior, not a defect;
forcing it higher is harmful.

## The 10 required distinctions
The Definition OBJECT now encodes: undefined key terms, vague/ambiguous terms, overly broad, overly
narrow, circular, inconsistent use, everyday-vs-discipline, sufficient-for-task, creates-misunderstanding,
and clarify-via-example/contrast (teaching strategy). These govern the developmental_variation and the
dialogue WHEN Definition is selected (verified on M08-type cases historically).

## Strengths / Weaknesses
- Strength: object is now precise and pedagogically rich; One Thing Rule + downstream-leverage principle
  correctly keep Definition from displacing more fundamental gaps.
- Weakness/limitation: hard to exercise Definition in synthetic single-paragraph corpora because claim/
  evidence gaps dominate; recommend validating Definition dialogue on a curated set of "strong claim +
  genuinely ambiguous load-bearing term" samples (e.g., legal/technical/contested-concept prompts).

## Backward compatibility
Content-only edits (Definition object + selector guidance). No DB/audit/flow/UI change. Frozen CIO#1/#2/#3
baselines re-confirmed after the revert. consolidated_v2 default path healthy.
