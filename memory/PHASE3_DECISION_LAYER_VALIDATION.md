# Phase III — Instructional Decision Layer Validation (VALIDATION ONLY, no code changed)

Architecture FROZEN. No engine / prompt / selector / DB / audit / UI change.
Two tasks: (1) Principle Audit of CIO #1–#5; (2) Mixed-Object Stress Test of the One Thing Rule.
Selector = claude-haiku-4-5. Harness: `/tmp/wt/phase3_mixed_object_stress.py`.

═══════════════════════════════════════════════════════════════════════════
## TASK 1 — PRINCIPLE AUDIT (Distinctness Principle: distinct JUDGMENT **and** distinct INTERVENTION)

| CIO | Distinct JUDGMENT (the question asked) | Distinct INTERVENTION (the coaching act) | Verdict |
|---|---|---|---|
| #1 Central Claim | Is there ONE contestable position that answers the task? | Name the one thing a reader must accept; sharpen until a skeptic could disagree. | ✅ both |
| #2 Evidence | Is the claim backed by specific / relevant / adequate checkable material? | Have the writer weigh their material on relevance·specificity·adequacy; notice mismatch; decide. | ✅ both |
| #3 Explanation | Is the HOW/WHY reasoning that links evidence→claim explicit and not overreaching? | Have the writer put the causal/logical link into words; test real reasoning vs. restatement. | ✅ both |
| #4 Definition | Does a load-bearing term have a precise, consistent working meaning? | Have the writer notice the leaned-on word and state its working meaning in their own words; sharpen too-broad/narrow/circular; keep consistent. | ✅ both |
| #5 Paragraph Unity | Does every sentence serve ONE controlling idea (membership)? | Have the writer name the controlling idea, test each sentence against it, keep/cut/move/split. | ✅ both |

**All five satisfy BOTH conditions.** Two boundary notes (NO merge or redefinition warranted):

- **B1 · Evidence ↔ Explanation (closest adjacent pair).** Distinct interventions — *get/assess the
  material you're standing on* (Evidence) vs. *articulate the reasoning linking it to the claim*
  (Explanation) — but the empirical borderline is thin (historically documented E1 oscillation).
  The engine keeps them apart correctly (see M2 & M6: claim+data present, reasoning absent → Explanation,
  not Evidence). Monitor; do not merge.

- **B2 · Central Claim ↔ Paragraph Unity share ONE symptom.** "Two or more competing ideas/claims"
  appears as the `misleading` indicator of BOTH objects. This is a shared *symptom* in the JUDGMENT,
  NOT a shared intervention: two competing claims are fixed by *choosing/sharpening one governing
  position* (Central Claim), not by *keep/cut/move/split of sentences* (Unity). The priority order
  (Central Claim above Paragraph Main Point) deterministically routes competing-claims → Central Claim,
  which is the correct intervention. Confirmed live in M7 & M10 (both stable → Central Claim). This is
  a deliberate, priority-resolved boundary, consistent with the Distinctness Principle. Do not merge.

**Audit conclusion:** CIO #1–#5 form five genuinely distinct instructional objects by both criteria.
No overlap in intervention requires a merge or redefinition. Two boundaries are adjacent (B1) or
share a symptom (B2), both correctly resolved by priority + intervention type at runtime.

═══════════════════════════════════════════════════════════════════════════
## TASK 2 — MIXED-OBJECT STRESS TEST (3 runs/case, does One Thing Rule pick ONE highest-leverage object?)

| Case | Competing issues engineered | Modal selection | Stable 3/3 | Assessment |
|---|---|---|---|---|
| M1 | Claim × Evidence (no claim, no support) | Central Claim (missing) | ✅ | SUCCESS — can't teach evidence for a non-claim |
| M2 | Evidence × Explanation (claim+data present, no reasoning) | Explanation (missing) | ✅ | SUCCESS — correctly chose link over material, and over Definition of "strengthen" |
| M3 | Definition × Claim (term undefined + claim vague) | Central Claim (partial) | ✅ | SUCCESS — claim must settle before "freedom" can be defined |
| M4 | Unity × Evidence (intended solid claim + tangent + thin support) | Central Claim (partial) | ✅ | AMBIGUOUS — engine judged the claim under-contestable and escalated above the intended Unity/Evidence contest |
| M5 | Claim × Evidence × Explanation (3-way, all thin) | Central Claim (missing) | ✅ | SUCCESS — foundation first |
| M6 | Explanation × Definition (claim+data solid, term slippery, link implicit) | Explanation (missing) | ✅ | SUCCESS — link over term |
| M7 | Unity × Explanation (two competing points) | Central Claim (missing/competing) | ✅ | AMBIGUOUS (defensible) — B2 boundary: competing claims → Central Claim by priority |
| M8 | Claim × Definition × Evidence (3-way) | Central Claim (missing) | ✅ | SUCCESS — claim determines what needs defining |
| M9 | Evidence × Explanation × Unity (intended solid claim + tangent + weak link) | Central Claim (missing) | ✅ | AMBIGUOUS — same as M4: intended-adequate claim read as under-contestable |
| M10 | Claim × Unity (a claim + a second competing claim) | Central Claim (misleading/competing) | ✅ | SUCCESS (defensible) — B2 boundary resolved to Central Claim |

**Stability: 10/10 cases stable across all 3 runs. One-target discipline: 10/10 — never emitted
multiple targets; every case produced exactly one highest-leverage object with a grounded contrast
rationale for why NOT the others.**

### Successful cases (7): M1, M2, M3, M5, M6, M8, M10
The layer applied the One Thing Rule as designed: walked priority from the top, selected the first
not-yet-solid applicable structure, and its `selection_contrast` correctly explained why the lower
structures were premature (e.g. M2 rejected Definition of "strengthen" as lower-leverage than the
missing reasoning; M8 gated Definition behind an unsettled claim).

### Ambiguous cases (3): M4, M9 (and M7 as a defensible variant of B2)
- **M4 & M9** — I engineered these to make Central Claim *adequate* so that a Unity/Evidence/Explanation
  contest would be the live one. The engine instead judged the claims ("bike lanes make commuting
  safer"; "remote work benefits employees") as **only partial / not contestable enough** and escalated
  to Central Claim. This is NOT a One-Thing-Rule failure — it is the **CIO #1 contestability bar**
  (calibrated in Phase II) firing: a claim that merely asserts a benefit is treated as under-established.
  Consequence for validation design: it is genuinely hard to hold "claim solid" fixed while stressing
  lower objects, because the contestability bar is strict. The behavior is internally consistent and
  defensible; flagged as ambiguous only because it pre-empted the *intended* competition.
- **M7** — two competing points routed to Central Claim (B2). Defensible by priority + intervention
  type; recorded as the expected resolution of the shared competing-ideas symptom.

### What the stress test demonstrates
1. The Instructional Decision layer **reliably collapses multiple simultaneous weaknesses to ONE
   highest-leverage object** (10/10 single, stable, rationalized).
2. Its ordering logic is **foundation-first and defensible**: unsettled/absent claims consistently
   outrank downstream Evidence/Explanation/Unity, exactly as the priority list intends.
3. The only "surprises" (M4/M9) are the **CIO #1 contestability bar** doing its job, not a decision-
   layer defect. If a future validation wants to isolate a pure Evidence×Explanation×Unity contest,
   the fixture must use a claim strong enough to clear the contestability bar (as M2/M6 do — both of
   which correctly moved past Central Claim).

═══════════════════════════════════════════════════════════════════════════
## OVERALL PHASE III VERDICT
- **Task 1:** CIO #1–#5 are all distinct by the Distinctness Principle (distinct judgment + distinct
  intervention). No merges. Two documented boundaries: B1 Evidence↔Explanation (adjacent, monitor),
  B2 Central Claim↔Paragraph Unity (shared "competing ideas" symptom, priority-resolved to the correct
  intervention).
- **Task 2:** The One Thing Rule holds under mixed-object pressure — 10/10 stable single selections
  with grounded contrasts; no target fragmentation. The three ambiguous cases trace to the (correct)
  CIO #1 contestability bar, not to the decision layer.
- **No code changed.** Nothing requires calibration from this pass. If action is later desired, the
  only candidates are documentation-only: note B2 in-code, and add a validation-fixture guideline that
  "claim-adequate" fixtures must clear the contestability bar.
