# Phase II — Instructional Calibration · CIO #1: CENTRAL CLAIM
Architecture FROZEN (no changes). Read-only evaluation of instructional quality.
Corpus: 14 authentic samples across developmental levels + controls, run through the live
consolidated_v2 pipeline (real selection + real dialogue). Ownership guard = True for all 14.

## Selection results by developmental level
| Level | Samples | Selected | Verdict |
|---|---|---|---|
| L0 topic only | T1, T2 | Central Claim | ✓ correct |
| L1 personal opinion | P1, P2 | Central Claim | ✓ correct |
| L2 broad/vague claim | B1, B2, B3 | Central Claim | ✓ correct |
| L3 multiple competing claims | M1, M2 | Central Claim | ✓ correct |
| L4 task-misaligned observation | A1 (phones distract) | Central Claim | ✓ correct (redirected to answer task) |
| L4 task-misaligned SUBCLAIM + reason | A2 (uniforms reduce bullying) | **Evidence** | ⚠ under-selection (claim doesn't answer task) |
| CTRL precise claim, no evidence | C1 | Evidence | ✓ correctly ADVANCED past claim |
| CTRL precise claim, some evidence | C2 | Explanation | ✓ correctly advanced |
| CTRL strong / near-complete | C3 | Explanation | ⚠ completion-threshold instability (twin strong paragraph earlier → NO_CURRENT_TARGET) |

## The 8 questions (aggregate + notable)
1. **Correct target?** Yes in 12/14. Two calibration misses: A2 (should stay Central Claim; task-level position unset) and C3 (near-complete; arguably NO_CURRENT_TARGET).
2. **Would another structure produce more progress?** Only in A2 (Central Claim > Evidence) and C3 (stop vs refine). Elsewhere no.
3. **Developmental variation accurate?** Yes and impressively specific: "circling the topic without taking a position" (L0), "personal preference stated as argument" (P1), "claim contestable but vague" (B2), "claim undercut by immediate counter-evidence" (M1). A2's "assertion without concrete support" is accurate for Evidence but sidesteps the task-alignment issue.
4. **Dialogue appropriate?** Yes — consistently strong; developmentally graded (gentler at L0/L1, more conceptual at L4/CTRL).
5. **Ownership preserved?** Yes, 14/14 (guard True). Never writes the claim; uses fill-in-the-blank the student completes.
6. **Learner performs the cognitive work?** Yes — every turn hands the thinking back ("what is the ONE thing you want them to believe?").
7. **Would a likely revision improve the target?** Yes for the Central Claim cases — the contestability test + sentence-starter reliably move topic/opinion/broad/multi toward a scoped claim.
8. **Instructional errors / missed opportunities?** A2: strengthening a subclaim before the task-level claim is set. C3: coaching an explanation that is largely present rather than acknowledging completion.

## Strengths
- Developmentally correct selection across the full L0→L3 range; reliably names and redirects the four claim variations (topic, personal opinion, broad, multiple).
- Correctly ADVANCES beyond Central Claim once the claim is precise and answers the task (C1, C2) — not "stuck."
- Dialogue has a strong, repeatable instructional shape: affirm what's present → name the gap in reader terms → one concrete move (often a student-completed sentence stem) → the contestability test ("could a reasonable person disagree?").
- Ownership and meaning-before-jargon are excellent and consistent.

## Weaknesses
- **Task-alignment under-selection:** when a narrow SUBCLAIM carries a "because" reason (A2), the engine can read the claim as "present" and move to Evidence, teaching support for a position that does not answer the assignment question.
- **Completion-threshold instability:** near-complete strong writing is sometimes pushed to a refinement (C3 → Explanation) and sometimes closed (twin → NO_CURRENT_TARGET). The "claim is done" boundary is not stable.
- **Minor dialogue formulaicity:** the fill-in-the-blank stem appears in most turns; at higher levels a more open prompt could demand more; occasional two-moves-in-one-turn (P1, M1) slightly exceeds "one move."

## Recurring decision patterns
- Claim-shaped sentence + a reason ⇒ risk of being scored "claim present" even when it doesn't answer the task.
- Precise, task-answering claim ⇒ clean advance to Evidence/Explanation.

## Recurring dialogue patterns
- 4-beat structure (affirm → reader-gap → concrete move → contestability test).
- Consistent second-person, one-idea framing; strengths named before the gap.

## Recommended CIO refinements (Central Claim) — CALIBRATION, not architecture
1. Redefine "present" indicator: a Central Claim is PRESENT only when it takes a contestable position that **answers the assignment's question** — not merely when a claim-shaped sentence (even with a "because") is on the page.
2. Add a **task-alignment** observable: variation "task-misaligned subclaim" = contestable but does not answer the task ⇒ remains a Central Claim target (redirect), NOT a move to Evidence. (Fixes A2.)
3. Add developmental variations explicitly: "personal preference stated as argument" and "task-misaligned subclaim" (both observed).
4. Stabilize the completion boundary (shared with Explanation/closure): specify when claim+support are "solid enough" to return NO_CURRENT_INSTRUCTIONAL_TARGET vs. select a refinement, so strong writing is handled consistently (C3 vs twin).
5. Optional dialogue guidance: vary the scaffold beyond the sentence-stem at higher levels; hold to strictly one move per turn at L0–L1.

## Recommended priority refinement
- Keep Central Claim at the top (validated). Add a **task-alignment gate** to its selection guidance: do not advance to a dependent structure until the claim answers the task. This lives in the CIO/selection-prompt layer — no Decision Engine change required.

## Examples
- **Excellent:** P1 (separates personal preference from a defensible claim), M1 (surfaces the self-contradiction, asks the writer to pick one side), C1 (correctly advances to Evidence once the claim is precise).
- **Needs improvement:** A2 (subclaim → Evidence instead of a task-aligned claim), C3 (over-coaches an explanation that is largely present; completion threshold).

## Can calibration solve these without touching the Decision Engine? YES.
Both misses (A2 task-alignment, C3 completion) are solvable by refining CIO content + selection/closure guidance (the criterion the frozen selector applies), not by changing the decision component. No architectural change is warranted.
