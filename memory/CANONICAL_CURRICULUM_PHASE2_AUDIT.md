# Phase 2 — Canonical Curriculum Audit (READ-ONLY; no production code modified)

Question: Is the Canonical Curriculum (5 primary models in `compass_curriculum.py`) sufficiently
complete to become the SOLE authoritative source for paragraph instruction?

Legend: FULLY / PARTIAL / NOT COVERED / CONTRADICTORY (relative to the Canonical Curriculum).

## A. Live instructional objects (`compass_structure_engine.MINIMAL_OBJECTS`, 11 objects, 5 fields)
| # | Current component (live object) | Current knowledge it encodes | Canonical location | Gap | Classification & recommendation |
|---|---|---|---|---|---|
| 1 | Reader Orientation | "opening move that tells reader what the piece is about + why worth attention" | Opening | Canonical Opening is OPTIONAL, audience-defined, explicitly rejects mandatory hook/attention-getter; live frames it as a required orienting move | **PARTIAL + CONTRADICTORY** (optionality & purpose). Replace with canonical Opening. |
| 2 | Central Claim | "single CONTESTABLE position that ANSWERS the task" | Thesis | Canonical Thesis = principal integrated message; explicitly forbids universal "must be contestable"; adds topic-vs-thesis + Generative Integration | **PARTIAL + CONTRADICTORY** (contestability & task-answer framing). Replace with canonical Thesis. |
| 3 | Paragraph Main Point (unity) | "paragraph develops ONE controlling idea; sentences cohere" | Thesis (Organizing Relevance requirement) — folds into Thesis per reconciliation | Live treats it as a SEPARATE primary object competing with Central Claim | **PARTIAL / REORGANIZED** — not a separate canonical object. Fold into Thesis (reconciliation). |
| 4 | Definition | calibrated 5-field object (undefined/vague/broad/narrow/circular/inconsistent) | Subordinate "Definition" — NOTES ONLY (no model) | No authoritative subordinate model exists yet | **NOT COVERED** (subordinate not modeled). Author subordinate model (later phase). |
| 5 | Evidence | relevance / specificity / adequacy / direction; supports the CLAIM directly | Evidence / Example | Canonical makes Evidence SUBORDINATE TO ELABORATION and requires an elaborative point first; adds interpretation, subordination, proportionality, audience-need | **PARTIAL + CONTRADICTORY** (dependency: claim→evidence vs elaboration→evidence). Replace with canonical Evidence/Example. |
| 6 | Explanation | "reasoning linking evidence→claim" | (reconciliation-pending — NOT canonical Elaboration per B(c)) | Canonical hasn't placed Explanation (within Elaboration / Evidence relation / distinct object) | **NOT COVERED / UNRECONCILED**. Decide placement (reconciliation). |
| 7 | Elaboration (live) | thin: "development that gives an idea enough substance"; ranked LOW (priority 7, behind Evidence/Explanation) | Elaboration (canonical) | Canonical Elaboration is the PRINCIPAL work (differentiation+integration, naïve-reader Q) and OUTRANKS Evidence, which is subordinate to it. Live inverts this. | **PARTIAL + CONTRADICTORY** (role & priority inversion — the biggest architectural conflict). Replace with canonical Elaboration + re-rank. |
| 8 | Transition | signal of how two ideas relate | Subordinate "Transition" — NOTES ONLY | No model | **NOT COVERED**. Model later if it meets Distinctness Principle. |
| 9 | Paragraph Closure | "completes a paragraph's work before piece moves on" | Conclusion (partial) | Canonical Conclusion = final INTEGRATION, not just stopping | **PARTIAL**. Merge into canonical Conclusion. |
| 10 | Conclusion (live) | "consolidates what the argument means, not merely restate" | Conclusion (canonical) | Canonical adds forms-of-completion, optional significance, integration criterion | **PARTIAL (largely consistent)**. Replace with canonical Conclusion. |
| 11 | Sentence Construction | sentence-level clarity/refinement | — none — | Canonical curriculum has NO primary or subordinate home for sentence-level instruction | **NOT COVERED**. Confirm whether sentence-level is in scope. |

## B. Prompts / selectors / judgments / dialogue / review / closure
| Component | Current knowledge | Canonical location | Gap | Classification & recommendation |
|---|---|---|---|---|
| `_SEL_SYS` selection heuristics | fixed priority list (Reader Orientation→Central Claim→Paragraph Main Point→Definition→Evidence→Explanation→Elaboration…), One Thing Rule, contestability/task-answer tests | per-structure `observable_decision_questions` + `structural_dependencies` in every model | Canonical supplies per-structure decision questions & dependency ordering, but NO explicit cross-structure LEVERAGE/arbitration procedure ("which structure first" as one algorithm); live priority order CONTRADICTS canonical architecture (Elaboration-central, Evidence-subordinate, Opening/Conclusion optional) | **PARTIAL + CONTRADICTORY**. Source decision questions & dependency order from canonical; author a canonical cross-structure leverage procedure (gap). |
| `_priority_digest()` | essence + present-indicator per object, in priority order | `definition`+`function`+`structural_requirements` | live essences are generic subsets | **PARTIAL**. Regenerate from canonical fields. |
| Developmental sufficiency (selector LLM heuristic) | generic "is it solid" judgment | `developmental_sufficiency` in every model (rich, per-structure) | none for the 5 primaries | **FULLY COVERED (primaries)**. Source directly from canonical. |
| `_DLG_SYS` + `generate_dialogue` (discovery/rescue, 6-function voice) | generic delivery shape + constraints-before-strategies I wrote | `discovery_instruction` + `rescue_instruction` per model | canonical gives per-structure CONTENT; live gives generic delivery mechanics | **PARTIAL**. Source per-structure discovery/rescue from canonical; keep delivery mechanics. |
| `_CLOSURE_SYS` + `generate_closure` | generic "acknowledge strengths, offer optional next" | Conclusion + `developmental_sufficiency` | closure ≠ Conclusion; canonical defines completion/integration | **PARTIAL**. Derive from canonical Conclusion + sufficiency. |
| `NOTICING_SYSTEM_MESSAGE` (interim cards) | "emerging central idea/claim" + "structural relationship" | Thesis (integrated message) + Elaboration (differentiation/integration) | generic terminology ("central idea/claim" vs "integrated message"); separate UX concern | **PARTIAL**. Re-anchor to canonical terms if retained. |
| Teacher Review (`teacher_review_fixtures.json`, precomputed) | static hand-authored explanations in generic composition terms | could be generated from `structural_requirements` + `observable_decision_questions` | fixtures do not reference canonical at all | **NOT COVERED**. Regenerate from canonical (wiring phase). |

## C. Sufficiency verdict
**Sufficient AND authoritative for the FIVE PRIMARY paragraph structures.** Each primary model fully
covers definition, function, dependencies, requirements, variations, sufficiency, discovery, rescue,
and observable decision questions — enough to drive selection, dialogue, sufficiency, and Teacher
Review for those structures, and it resolves several live contradictions (contestability, elaboration
vs evidence priority, opening/conclusion optionality).

**NOT YET sufficient to be the SOLE authoritative source for ALL paragraph instruction**, blocked by
five gaps:
1. **Subordinate structures unmodeled** — Definition & Transition are actively used live; Qualification/
   Comparison/Analogy are notes only. No authoritative subordinate models exist.
2. **Explanation placement unreconciled** — live has an Explanation object with no canonical home.
3. **Sentence-level instruction has no canonical home** — live "Sentence Construction" maps to nothing.
4. **Cross-structure leverage/selection procedure is not canonically specified** — canonical gives
   per-structure decision questions and a dependency-implied order, but not an explicit "which structure
   is highest-leverage now" algorithm; the live priority order directly contradicts canonical architecture.
5. **Paragraph Main Point → Thesis migration** and unity handling not yet modeled.

**Recommendation:** the curriculum is ready to become the authoritative source for the five primary
structures; before it can be the SOLE source, author (a) the subordinate-structure models on the lighter
schema, (b) the Explanation reconciliation decision, (c) a canonical cross-structure leverage/selection
procedure, and (d) an explicit scope decision on sentence-level instruction. All are authoring/decision
tasks for you — not inventions I should make.
