# Phase II — CIO #2: EVIDENCE (calibrated + verified)
Additive calibration of the Instructional Decision layer. Architecture/flow unchanged; only the
Evidence Canonical Instructional Object + selector guidance were enriched. Verified live.

## What changed (additive)
- `MINIMAL_OBJECTS["Evidence"]`: essence + observable indicators now separate PRESENCE, RELEVANCE,
  ADEQUACY, and DIRECTION (supports vs contradicts). Developmental variations expanded to:
  Unsupported assertion · Irrelevant support · Vague/general support · Partial support (covers only
  part of the claim) · Relevant but inadequate · Evidence that contradicts the claim · Specific,
  relevant, adequate evidence. Teaching strategy: check the claim first, then judge relevance /
  specificity / adequacy; never supply or judge the evidence for the writer.
- `_SEL_SYS`: Evidence is the focus ONLY once a clear, task-answering claim exists (One Thing Rule);
  name the evidence issue on three axes (relevance / specificity-adequacy / direction); if evidence
  is specific+relevant+adequate but unexplained, the object is Explanation, not Evidence.

## Verification corpus (clear claim + varied evidence; + unclear-claim control)
| Sample | Condition | Selected | Verdict |
|---|---|---|---|
| E1 | unsupported assertion | Evidence ("zero concrete material") | ✓ presence |
| E2 | present but irrelevant | Evidence (names traffic complaint as "not evidence bearing on the claim") | ✓ relevance |
| E3 | vague support, imprecise claim | Central Claim (claim not yet a precise contestable position) | ✓ defensible (One Thing Rule) |
| E4 | specific but uninterpreted | **Explanation** (evidence present+adequate, reasoning unstated) | ✓ boundary correct |
| E5 | partial support | Evidence (probes whether it supports THIS claim) | ✓ partial/adequacy |
| E6 | evidence contradicts claim | Central Claim (recognizes self-undermining; commit to a position first) | ✓ contradiction recognized, defensible |
| E7 | single-anecdote adequacy | Evidence ("presented as proof without scope") | ✓ adequacy |
| CTRL | unclear claim | Central Claim (NOT Evidence) | ✓ One Thing Rule guard |

## The 8 required distinctions — all exercised
presence (E1) · relevance (E2) · adequacy (E5,E7) · explanation/interpretation boundary → Explanation (E4) ·
unsupported assertion (E1) · partial support (E5) · contradicts claim (E6 recognized) · where more evidence
would strengthen reasoning (dialogues in E1/E2/E5 push exactly this). Evidence never chosen over an
unsettled claim (CTRL, E3, E6).

## Strengths
- Precise, dimension-named variations (relevance vs adequacy vs direction), not generic "add evidence."
- Correct object boundaries: defers UP to Central Claim when the claim is the deeper issue; defers DOWN
  to Explanation when evidence is present but unexplained.
- Dialogue applies a consistent skeptic test ("can a reader check this? does it actually support THIS
  claim?"), action-driven (ask_question), ownership preserved, never supplies evidence.

## Weaknesses / watch items (calibration, not defects)
- The claim-precision gate is assertive: borderline-adequate claims with weak evidence (E3) route to
  Central Claim rather than Evidence. Pedagogically sound (fix the claim before its support) and
  consistent with CIO#1, but worth monitoring for over-deferral on genuinely precise claims.
- "Evidence contradicts the claim" (E6) currently surfaces as a Central Claim decision (commit to a
  position) rather than an Evidence-direction lesson; defensible, but the dedicated "contradicts"
  Evidence variation may rarely be the selected object.

## Backward compatibility / architecture
No DB/audit/override/flow changes. Single-decider flow intact. S1 foundation 11/11; consolidated_v2
default path healthy (8/8 corpus completed). CIO#1 Central-Claim behavior unaffected.
