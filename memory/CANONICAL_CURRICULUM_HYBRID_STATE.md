# Canonical Curriculum — HYBRID EXECUTION STATE (containment + documentation pass, 2026-06)

Corrected characterization: the dialogue layer is PARTIALLY WIRED to `compass_curriculum` via
`_resolve_teaching_source()`. Current reality:
- selector still selects LEGACY live objects (`compass_structure_engine.MINIMAL_OBJECTS`);
- dialogue resolves SOME legacy objects to canonical teaching sources (name + content);
- learner-STATE judgment (status: missing/partial/misleading/present) still comes from the LEGACY selector;
- dialogue FORM is still controlled by the generic dialogue prompt (`_DLG_SYS`);
- sufficiency, interim noticing, Teacher Review, closure, UI: NOT canonically wired.

## Per live object (selector name → mapping → teaching source → sufficiency source → status)
| Legacy selector object | Approved canonical mapping | Current TEACHING source | Current SUFFICIENCY source | Mapping status |
|---|---|---|---|---|
| Reader Orientation | Opening | **Canonical: Opening** (ready) | legacy selector LLM | APPROVED-by-AC#1 (obsolete→Opening) |
| Central Claim | Thesis | **Canonical: Thesis** (ready) | legacy selector LLM | **APPROVED** (explicit) |
| Paragraph Main Point | Thesis | **Canonical: Thesis** (ready) | legacy selector LLM | APPROVED (Phase-1 D: folds into Thesis) |
| Definition | — none — | legacy Definition CIO | legacy selector LLM | ABSENT (subordinate not modeled) |
| Evidence | Evidence / Example | **Canonical: Evidence / Example** (ready) | legacy selector LLM | PROVISIONAL (name approved; canonical makes it subordinate-to-Elaboration → architectural contradiction w/ live claim→evidence order) |
| Explanation | — none (mapping REMOVED) — | legacy Explanation CIO | legacy selector LLM | **ABSENT — no approved canonical mapping** (Explanation→Elaboration removed this pass) |
| Elaboration | Elaboration | **Canonical: Elaboration** (ready) | legacy selector LLM | PROVISIONAL (live Elaboration is thin/low-priority; canonical Elaboration is the new principal object — content routing not explicitly approved) |
| Transition | — none — | legacy Transition CIO | legacy selector LLM | ABSENT (subordinate not modeled) |
| Paragraph Closure | Conclusion | **Canonical: Conclusion** (ready) | legacy selector LLM | PROVISIONAL (merge into Conclusion not explicitly approved) |
| Conclusion | Conclusion | **Canonical: Conclusion** (ready) | legacy selector LLM | PROVISIONAL (canonical name aligned; content routing not explicitly approved) |
| Sentence Construction | — none — | legacy Sentence Construction CIO | legacy selector LLM | ABSENT (no canonical home) |

Notes:
- SUFFICIENCY source is legacy selector LLM for ALL objects (sufficiency not wired — out of scope).
- TEACHING source = canonical only when the mapped structure `is_structure_ready()` (all 5 primaries are).
- Only **Central Claim → Thesis** is explicitly approved. **Reader Orientation→Opening** and
  **Paragraph Main Point→Thesis** follow directly from earlier accepted directives (AC#1 / Phase-1 D).
  The remaining canonical routings (Evidence, Elaboration, Paragraph Closure, Conclusion) are
  PROVISIONAL and awaiting the same explicit approval Thesis received. They were NOT changed this pass.
- No reconciliation performed. Live objects unchanged. Selector/priority/sufficiency/noticing/
  Teacher Review/closure/UI/DB/audit/OT untouched.
