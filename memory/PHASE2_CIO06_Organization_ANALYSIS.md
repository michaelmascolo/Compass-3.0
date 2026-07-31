# Phase II — CIO #6 (Organization) Boundary Analysis — RECOMMENDATION (no code changed)

ANALYSIS ONLY. No engine / prompt / selector / DB / audit / UI change. Architecture FROZEN.
Scope fixed by user: single paragraph only. "Organization" = logical sequencing/arrangement
of ideas WITHIN one paragraph (order of sentences). Question: is Organization a genuinely
distinct developmental OBJECT from Paragraph Unity, or merely an INDICATOR of it at this scale?

## The conceptual distinction (they are NOT the same judgment)
- **Paragraph Unity (CIO #5, "Paragraph Main Point")** asks a MEMBERSHIP question:
  *does every sentence belong to ONE controlling idea?* Failure = drift / tangent / a second
  competing topic. The fix is keep / cut / split.
- **Organization** asks a SEQUENCE question: *given that the sentences all belong, are they in
  the RIGHT ORDER for a reader to follow the reasoning?* Failure = claim buried at the end,
  effect stated before cause, scrambled "first/second/finally", a supporting detail arriving
  before the point it supports. The fix is move / reorder.

So conceptually they are distinct: unity is about *what belongs*, organization is about
*what order*. This is a real difference in instructional judgment.

## Empirical probe (live selector, 2 runs, 8 single-paragraph samples)
Harness `/tmp/wt/cio6_organization_probe.py` — 4 "pure ordering" cases (unity intact, order
scrambled), 2 unity cases, 2 controls. Selector = claude-haiku-4-5.

| Sample (intended = ordering problem) | Selected by engine | What the engine "saw" |
|---|---|---|
| ORG-1 conclusion-first, claim buried at end | **Central Claim** (partial) | buried claim read as an under-contestable claim, not a mis-order |
| ORG-2 effect-before-cause | **Evidence** (partial) | ignored order; saw the biological premise as unsupported |
| ORG-3 scrambled "first/second/finally" points | **Paragraph Main Point** (misleading) | routed to Unity as "poorly-coordinated support" |
| ORG-4 detail before the point it supports | **Evidence** (partial) | ignored order; saw an unsupported premise |
| UNITY-1 drift/tangent (control) | Paragraph Main Point | correct |
| UNITY-2 two competing ideas (control) | Paragraph Main Point / Central Claim (flips) | correct, borderline |
| CTRL no-claim | Central Claim | correct |
| CTRL clean, well-ordered | Evidence (partial) | correct — no ordering gap found |

### Two findings that decide the question
1. **A "pure single-paragraph ordering problem" is hard to even construct.** In 3 of 4 attempts
   (ORG-1/2/4), the moment I made the sentences genuinely on-topic, the engine correctly found a
   MORE fundamental gap (claim contestability, evidence adequacy) that outranks ordering by the
   One Thing Rule. At single-paragraph scale, when claim + evidence + explanation are truly solid,
   a residual "wrong order" almost never survives as the *highest-leverage* issue.
2. **Where ordering did survive (ORG-3), the engine already routes it to Paragraph Unity** and its
   calibrated variation "poorly-coordinated support," and CIO #5's teaching strategy already says
   the writer decides what to "keep, cut, **move**, or split" — i.e. reordering is already inside
   Paragraph Unity's operational scope. No instructional coverage is lost.

## Is there a case where a skilled teacher picks Organization, NOT Unity?
Only ORG-3 is arguably that case (all sentences belong to one idea; the sole defect is scrambled
sequence). A teacher might say "your points are all relevant — the ORDER is jumbled." But the
instructional MOVE ("name your point, then arrange the sentences that develop it") is the SAME tool
Paragraph Unity already hands the writer. The distinct judgment exists; the distinct *intervention*
does not, at single-paragraph scale.

## Where Organization becomes genuinely irreducible: MULTI-paragraph
At multi-paragraph scale each paragraph can be perfectly unified yet the paragraphs sit in the
wrong sequence (chronology vs. importance vs. logical dependency). There Unity offers NO guidance,
and "move a sentence" no longer covers it — you must sequence whole chunks of reasoning. That is a
distinct instructional object Paragraph Unity cannot express. (Out of current scope per user.)

## RECOMMENDATION
**DEFER CIO #6 (Organization) to multi-paragraph composition.** At the single-paragraph level it is
conceptually distinct but NOT an independent highest-leverage instructional object: its symptoms are
already, and correctly, absorbed by the calibrated Paragraph Unity CIO ("poorly-coordinated support"
+ the keep/cut/**move**/split strategy), and the live selector never needs it (deeper gaps dominate,
or Unity already catches the residue). Adding it now would introduce a boundary overlap the selector
would have to arbitrate ("is this drift or mis-order?") on the very same paragraph, for near-zero
instructional payoff — violating the "every CIO is a genuinely distinct judgment" principle.

**Do NOT treat it as a new CIO now. Do NOT expand the selector.** Optional, and only if you later
approve it as its own small calibration pass: sharpen one Paragraph Unity variation label so
"poorly-coordinated support" explicitly reads "poorly-coordinated / out-of-sequence support," making
the reorder subtype visible to teachers WITHOUT a new object. Not done here — analysis only.
