# Stage B Prompt — Architectural Review (conceptual-cleanliness audit)

**Date:** 2026-07-29 · **Mode:** READ-ONLY. Nothing rewritten, shortened, or optimized.
**Scope:** The full Stage B reasoner prompt = the static `SYSTEM_MESSAGE`
(`server.py` L842–1116, with `<<CANONICAL_EXIT_CRITERIA>>` injected at L1119) **plus** its
per-turn assembly in `_build_prompt` (L1263–1296) and the KB/hydrator layer
(`_build_exit_criteria_block` L131, `hydrate_element` L186, instructional objects / network / resource menu).
**Purpose:** determine whether Stage B is *conceptually* clean, or whether months of additive layering
have produced duplication, overlap, obsolescence, or competition. NOT to make it shorter.

---

## 0. Method
I read the prompt top-to-bottom as though for the first time and built a section inventory (23 sections,
below). For each recurring idea I traced every place it is stated, then classified each occurrence.
I did **not** treat "repeated" as automatically "wrong": Stage 3 already proved that a field can look
deterministic yet be reasoning-active (`element_relationships`), so I separate *reinforcing repetition*
(deliberate, safety-serving) from *historical layering* (accidental, competing, or maintenance-risky).

### Section inventory (in prompt order)
1. Opening role line · 2. **COMPASS CONSTITUTION** (7 principles + default sequence, L844–859) ·
3. **UNIFIED STRUCTURAL REASONING** (hierarchy, entry points, 9-step reasoning sequence, triage,
`<<CANONICAL_EXIT_CRITERIA>>`, CANONICAL COACHING SEQUENCE, COACHING EXECUTION CONTRACT) ·
4. Non-diagnosis / provisional-theory / asymmetry / **domain-independence** paragraphs (L902–908) ·
5. CANONICAL WRITING MODEL + INSIDE-OUTSIDE COORDINATION (L910–912) ·
6. **M6** Communicative Purpose · 7. **M7** Paragraph Function · 8. **M8** Evidence ·
9. **M9** Transition & Coherence · 10. **M10** Conclusion ·
11. **M11** Recursive Scaffolding Controller (Master Loop 1–8 + stopping rules) ·
12. **M12** Reader Construction · 13. **M13** Revision as Development ·
14. **M14** Integration & Calibration · 15. **GOVERNED CANONICAL INSTRUCTION** (14-step + governance +
Student-Facing Response Shape A–E) · 16. **ENGINE REFINEMENTS W-A..W-E** ·
17. DRAFT RULE · 18. **RECURSIVE LOOP** (10 steps) · 19. STUDENT-FACING INVITATION RULES ·
20. **M5A** Writing Instruction Boundary + Anti-Coauthoring + Self-Check + Content Mode ·
21. **DEVELOPMENTAL INSTRUCTION LAYER** (5 intervention types + timing + restraint) ·
22. OUTPUT FORMAT (JSON schema) · 23. BREVITY.

---

## 1. Overall verdict (read this first)
Stage B is **not chaotic and not internally contradictory in its instructional philosophy** — every
section pulls toward the same pedagogy (teacher-directed, structure-before-content, one target/turn,
scaffold-not-supply, sufficiency-not-perfection). It also already contains an explicit
**conflict-resolution mechanism**: the Constitution declares itself highest authority and says "if any
lower-level instruction, legacy phrasing, or example conflicts with a constitutional principle, THE
CONSTITUTIONAL PRINCIPLE GOVERNS." That single meta-rule is doing a lot of quiet work and is the main
reason the accumulated layers have not produced behavioral incoherence.

**However**, the prompt shows clear signs of **historical layering**:
- The **coaching arc** and the **anti-coauthoring boundary** are each restated ~4–10 times.
- There are **three parallel "run this loop every turn" procedures** (Unified Structural Reasoning,
  M11 Master Loop, Governed 14-step, plus the older Recursive Loop) whose relationship a fresh reader
  must infer.
- There are **two parallel "what kind of move" taxonomies** (M5 intervention types vs M11 instructional
  modes) joined by a hand-written crosswalk.
- There are **four overlapping "knowledge source" vocabularies** (canonical domains / cultural_resources /
  instructional objects / shared resource menu).
- There is **one genuine conceptual conflict** (Finding F1): the "you are domain-independent and hold NO
  built-in instructional sequence" paragraph predates — and now contradicts — the Constitution's explicit
  built-in Default Guided Composition sequence and the baked-in canonical hierarchy/exit-criteria.

Conclusion: Stage B is **conceptually coherent in intent but layered in form.** The right next step is
**intentional consolidation of a small number of named structures** (discussed, not silently cut), NOT
further experimental field removal. Crucially — per Step 3 — "a value is also produced by the hydrator"
does **not** mean "safe to remove from Stage B"; the structural-relation fields are reasoning-active.

---

## 2. Findings (each with: why · reasoning-or-communication · keep? · discuss?)

### F1 — GENUINE CONFLICT: "domain-independent reasoner, no built-in sequence" vs the built-in Constitution/hierarchy
- **Where:** L908 "You are domain-independent as a REASONER. You hold NO built-in instructional sequence
  for essay writing. Domain-specific writing knowledge comes ONLY from the CANONICAL WRITING MODEL
  supplied in the request." — vs — Constitution "DEFAULT GUIDED COMPOSITION INSTRUCTIONAL SEQUENCE" (L858),
  the CANONICAL STRUCTURAL HIERARCHY (L863–867), and the injected CANONICAL EXIT CRITERIA (L886) which
  *do* encode essay-specific structure and a default sequence directly in the prompt.
- **Why it's a conflict:** this is the one place two instructions make **opposite factual claims about the
  system's own architecture.** The domain-independence paragraph is a genuine artifact of the earlier
  "engine is domain-neutral; all writing knowledge is external data" design; the three-layer architecture
  has since deliberately moved canonical writing knowledge *into* the constitution/hierarchy/exit-criteria.
- **Reasoning or communication:** **Reasoning.** It affects how the model treats its own built-in
  knowledge (may it lean on the Constitution's sequence, or must it pretend to hold none?).
- **Keep?** The *intent* behind it (keep developmental reasoning distinct from canonical writing content;
  don't invent domain facts not supplied) is still valuable and should remain. The *literal claim* ("NO
  built-in instructional sequence," "knowledge comes ONLY from the supplied model") is now false and
  competes with the Constitution.
- **Discuss?** **Yes — highest priority.** This is the clearest candidate for intentional reconciliation:
  restate as "your developmental *reasoning* is domain-independent; your canonical *writing knowledge* is
  the Constitution + supplied objects — keep the two distinct" rather than "you hold none."

### F2 — HEAVY DUPLICATION: the coaching arc is stated 4× (plus 2 partial echoes)
- **Where:** Constitution "DEFAULT GUIDED COMPOSITION INSTRUCTIONAL SEQUENCE" 7 steps (L858) ·
  "CANONICAL COACHING SEQUENCE" 8 steps (L890) · COACHING EXECUTION CONTRACT "ALWAYS NAME THE LESSON"
  5-step order (L893) · W-E "MANDATORY STUDENT-FACING SEQUENCE" a–f (L1019). Partial echoes: Governed
  "STUDENT-FACING RESPONSE SHAPE A–E" (L1008) and Recursive Loop steps 7–9 (L1039–41).
- **Why:** all describe the same arc — recognize emerging competence → name the focus → explain its
  purpose → identify the missing dependency → scaffold it → return to the larger structure → release.
  They mostly agree; small differences (7 vs 8 steps; the Execution Contract's stricter "name the lesson
  BEFORE any content talk" ordering) mean the wording can be pulled slightly differently by whichever the
  model latches onto.
- **Reasoning or communication:** primarily **Communication** (the shape/wording of the student message),
  with mild reasoning impact via ordering emphasis.
- **Keep?** Keep the arc; keep the Execution Contract's stricter "name the lesson first" nuance and W-E's
  dependency-specific version (they add real constraints). The two nearly-identical 7/8-step lists are the
  redundant pair.
- **Discuss?** **Yes.** Candidate for one canonical sequence referenced by name, with the Execution
  Contract and W-E stated as *deltas* on it rather than full re-listings.

### F3 — HEAVY REINFORCEMENT: the anti-coauthoring / "never supply content or rewrite" boundary is stated ~10×
- **Where:** Constitution principle 6 (L855) · asymmetry paragraph "NEVER write or substantially rewrite"
  (L906) · SCAFFOLD RATHER THAN SUPPLY (L896) · a per-framework "Per the WRITING INSTRUCTION BOUNDARY
  (M5A) you may teach X but may NOT invent Y" clause inside **each** of M6, M7, M8, M9, M10, M12, M13
  (7 near-identical restatements) · Governed "SUPPORTED PERFORMANCE" (L1005) · the full **M5A** section
  + ANTI-COAUTHORING + SELF-CHECK + CONTENT MODE (L1046–1051) · W-C NO COPYABLE CONTENT (L1014) ·
  STUDENT-FACING INVITATION RULES (L1044).
- **Why:** this is the most-repeated idea in the prompt. The **7 per-framework restatements** are the
  clearest layering — each milestone re-derived the same boundary in its own words.
- **Reasoning or communication:** **Both**, but note this is a **safety-critical** constraint, so *some*
  repetition is deliberate reinforcement, not accident. The question is whether 10 copies buy more safety
  than 2–3 well-placed ones.
- **Keep?** Keep M5A as the single authoritative statement + W-C's "no copyable content even as an example"
  sharpening + one self-check. The 7 per-framework echoes are the reduction candidates.
- **Discuss?** **Yes — but treat as an experiment, not an assumption.** Whether the per-framework echoes
  affect behavior is empirically testable (they plausibly only reinforce). Given Step-3 lessons, do NOT
  assume they're inert; if consolidated, benchmark anti-coauthoring adherence before/after.

### F4 — REINFORCEMENT: "one target / one invitation per turn" stated ~8×
- **Where:** Constitution principle 4 (L853) · General Reasoning Sequence step 8 (L881) · M11 step 4 +
  "NEVER teach multiple major concepts" (L955) · M11 FUTURE CYCLES (L961) · M12 (L970) · M14 (L981/986) ·
  STUDENT-FACING INVITATION RULES (L1044) · W-A..W-E preamble (L1011).
- **Why:** every orchestration-related section re-asserts the one-target rule.
- **Reasoning or communication:** **Reasoning** (target selection).
- **Keep?** Yes — but M11 is its natural owner; the other 7 are echoes. This is low-risk redundancy.
- **Discuss?** Optional. Lower priority than F1–F3.

### F5 — PARALLEL TAXONOMIES: M5 "intervention.type" (5) vs M11 "instructional_mode" (6) with a manual crosswalk
- **Where:** Developmental Instruction Layer types = interpretation_only | instruct_then_invite |
  invite_only | consolidate | postpone_instruction (L1053–1058). M11 modes = developmental_question |
  explicit_instruction | brief_demonstration | guided_revision | reflection | consolidation (L956, schema
  L1078). M11 step 5 hand-maps between them ("developmental_question→interpretation_only|invite_only;
  explicit_instruction→instruct_then_invite; consolidation→consolidate").
- **Why:** two overlapping vocabularies for "what kind of move to make this turn," bridged by a
  hand-written mapping — textbook historical layering (M5 predates the M11 controller). The model must
  populate **both** `scaffolding_control.instructional_mode` and `intervention.type` and keep them
  consistent every turn.
- **Reasoning or communication:** **Reasoning** (and it costs output tokens: two fields + the mental
  crosswalk).
- **Keep?** The *concept* (choose a calibrated move) must remain. Maintaining two enumerations is the
  redundancy.
- **Discuss?** **Yes — high value.** Unifying to one taxonomy (or formally declaring one primary and the
  other derived) would remove a standing consistency burden. Because both are in the output contract, this
  is exactly the kind of change to run through the Step-3 noise-floor protocol.

### F6 — THREE OVERLAPPING "LOOPS": Unified Structural Reasoning · M11 Master Loop · Governed 14-step · (+ Recursive Loop)
- **Where:** UNIFIED STRUCTURAL REASONING 9-step "GENERAL REASONING SEQUENCE" (L873–882) · M11 "MASTER
  DEVELOPMENTAL LOOP" 1–8 (L951–960) · GOVERNED CANONICAL INSTRUCTION 14-step (L988–999) · the older
  RECURSIVE LOOP 10 steps (L1032–1042).
- **Why:** four "each turn, do this ordered procedure" lists. They operate at *different levels*
  (structural location → orchestration/prioritization → instructional-object reasoning → developmental
  theory-revision + candidate generation) and largely **compose** rather than conflict, but they
  independently repeat shared steps (identify unit; confirm purpose; diagnose; pick ONE; evaluate movement;
  consolidate). A fresh reader cannot easily tell whether these are four passes or one pass described four
  ways.
- **Reasoning or communication:** **Reasoning** (and latency — the model may narrate several loops into the
  output fields).
- **Keep?** All four contain unique, load-bearing content (e.g., structural hierarchy location lives only
  in Unified; candidate-invitation generation + theory revision lives only in Recursive Loop). None is
  purely dead.
- **Discuss?** **Yes.** Worth an explicit "these are ONE turn viewed at four levels; here is how they nest"
  framing so the layering is intentional and legible. This is the biggest *organizational-clarity* issue.

### F7 — FOUR KNOWLEDGE-SOURCE VOCABULARIES that overlap
- **Where:** `_build_prompt` injects (a) canonical **domain** sections, (b) retrieved **instructional
  objects**, (c) instructional **network**, (d) developmental **profile**, (e) **SHARED DEVELOPMENTAL
  RESOURCE MENU**. Prose refers to "canonical writing model / domains," "**cultural_resources**"
  (L1055/1059 Developmental Instruction Layer), "instructional objects" (Governed layer), and
  "developmental resources" (menu) — partly synonymous, partly distinct.
- **Why:** the Developmental Instruction Layer still tells the model to draw resources from "the supplied
  domain's **cultural_resources**," while the newer Governed layer tells it to reason from **instructional
  objects** + the **shared resource menu.** Two parallel resource-retrieval stories; the older
  cultural_resources path may now be largely superseded.
- **Reasoning or communication:** **Reasoning** (which knowledge vocabulary governs the turn).
- **Keep?** Verify empirically whether `cultural_resources` is still doing work distinct from instructional
  objects; if it is, keep and disambiguate the vocabulary; if not, it may be **obsolete**.
- **Discuss?** **Yes.** Naming one canonical vocabulary would reduce ambiguity. (Do not assume obsolete
  without a check — same discipline as Step 3.)

### F8 — TRIPLE STATEMENT: "restraint / don't over-teach competent work"
- **Where:** Developmental Instruction Layer "RESTRAINT" (L1060) · M14 CALIBRATION "guards over-teaching"
  (L982) · W-B GREATER RESTRAINT ON COMPETENT PERFORMANCE (L1013).
- **Why:** three restatements of "when the work already meets the objective, don't invent a gap."
- **Reasoning or communication:** **Reasoning.**
- **Keep?** W-B is the sharpest/most operational (with the "concrete textual evidence" test); it is the
  natural owner. The other two are echoes.
- **Discuss?** Optional-to-yes. Reinforcing; low risk if left, modest clarity gain if consolidated.

### F9 — TRIPLE STATEMENT: "teach, don't only ask questions"
- **Where:** Governed step 9 (L997) · CANONICAL-KNOWLEDGE GOVERNANCE "TEACH, don't only ask" (L1004) ·
  SHARED DEVELOPMENTAL RESOURCE MENU preface (L1291).
- **Why:** same instruction three times across adjacent sections.
- **Reasoning or communication:** **Reasoning.**
- **Keep?** Yes (once). Low-risk redundancy.
- **Discuss?** Optional.

### F10 — DOUBLE "SUFFICIENCY, NOT LOCAL OPTIMIZATION"
- **Where:** Constitution principle 7 (L856) · COACHING EXECUTION CONTRACT full-paragraph restatement
  with model example (L897) · plus the exit-criteria block preface operationalizes it (L143–146) and the
  schema field `sufficiency_for_next_step` records it.
- **Why:** L897 is essentially principle 7 expanded into a paragraph. Conceptually identical.
- **Reasoning or communication:** **Both** (a reasoning decision + a "release/acknowledge" communication).
- **Keep?** Keep one authoritative statement + the schema field + the exit-criteria operationalization.
  The L897 paragraph mostly duplicates principle 7 (its model example is the only unique part).
- **Discuss?** Yes (low priority).

### F11 — DUAL SELF-CHECKS "before finalizing the invitation"
- **Where:** M14 SELF-CHECK (leverage/proportion/support/appropriateness, L985) · M5A SELF-CHECK
  (writing-vs-content, L1050).
- **Why:** two distinct final self-checks defined in separate sections; a reader must remember to run both
  at the same moment. Not conflicting — but not co-located.
- **Reasoning or communication:** **Reasoning** (final gate before output).
- **Keep?** Both checks are valuable and genuinely different.
- **Discuss?** Minor — a combined "final gate" would improve legibility; content unchanged.

### F12 — SCHEMA ↔ PROSE DOUBLE-MAINTENANCE of "applies" conditions
- **Where:** each M7–M13 framework prose states its `applies=true/false` condition, and the OUTPUT schema
  (L1074–1082) **restates the same condition** for each field.
- **Why:** the condition lives in two places; editing one without the other can drift.
- **Reasoning or communication:** **Reasoning** (whether a framework fires) — but this is arguably
  *desirable* redundancy (the schema is the contract; the prose is the rationale).
- **Keep?** Keep both; just flag as a **maintenance-coupling** to keep in sync.
- **Discuss?** No action needed; awareness item.

### F13 — POTENTIAL EDGE: ANSWER-THE-ASSIGNMENT CHECK vs the anti-content boundary
- **Where:** CANONICAL-KNOWLEDGE GOVERNANCE "ANSWER-THE-ASSIGNMENT CHECK" (L1003): "name the drift plainly
  and reorient the student to the assignment."
- **Why:** reorienting a student whose *content* has drifted brushes against M5A (commenting on content).
  It is currently well-bounded (it points at the assignment, not at ideas to add), so it is not a live
  conflict — worth watching that it stays framed as a writing/assignment-fidelity move, not content advice.
- **Reasoning or communication:** **Both.**
- **Keep?** Yes.
- **Discuss?** Watch-only.

### F14 — "no stages / scores / levels" stated 3× (minor)
- **Where:** non-diagnosis paragraph (L902) · STUDENT-FACING INVITATION RULES "naming a developmental
  level" (L1044) · BREVITY "Do not store numeric scores" (L1113).
- Reinforcing; **Communication + reasoning**; keep; discuss = no.

### F15 — COSMETIC: large blank-line gaps from prior deletions
- **Where:** L899–901, L1020–1029 (several consecutive blank lines).
- Communication-only / trivial; keep-or-clean at will; not a conceptual issue.

### F16 — IMPORTANT NON-FINDING: the structural-relation fields are NOT obsolete-because-hydrated
- `hydrate_element` (L186) deterministically supplies `relationships`, `dependencies`, `exit_criterion`,
  `purpose`, `performance_structure`. It is tempting to mark the matching Stage B output fields
  (`element_relationships`, `developmental_dependencies`, `active_exit_criterion`,
  `element_communicative_purpose`, `canonical_performance_structure`) as "redundant — the KB already has
  them." **Step 3 empirically disproved that for `element_relationships`** (removing it destabilized
  `object` selection on TC37/TC49; Group 1 disproved it for purpose/performance_structure). These are
  **Mixed / reasoning-active**: articulating them is scaffolding, not just output. They should **remain in
  Stage B.** This is the single most important guardrail for any future consolidation: *hydrated ≠ removable.*

---

## 3. Summary table

| # | Issue | Type | Reasoning / Comm. | Recommendation |
|---|---|---|---|---|
| F1 | domain-independence claim vs built-in Constitution/hierarchy | **conflict** | Reasoning | **Discuss & reconcile (top priority)** |
| F2 | coaching arc stated 4× | duplication | Communication | Discuss (name one canonical arc) |
| F3 | anti-coauthoring stated ~10× (7 per-framework echoes) | duplication (safety) | Both | Discuss; treat consolidation as an experiment |
| F4 | one-target/one-invitation ~8× | reinforcement | Reasoning | Optional (M11 owns it) |
| F5 | M5 types vs M11 modes (dual taxonomy + crosswalk) | overlap/layering | Reasoning | **Discuss (unify)** |
| F6 | 3–4 parallel per-turn "loops" | overlap/clarity | Reasoning | **Discuss (nest explicitly)** |
| F7 | 4 knowledge-source vocabularies (esp. cultural_resources) | overlap/possible obsolete | Reasoning | Discuss + verify cultural_resources still used |
| F8 | restraint stated 3× | duplication | Reasoning | Optional (W-B owns it) |
| F9 | "teach don't only ask" 3× | duplication | Reasoning | Optional |
| F10 | sufficiency stated 2× (+schema) | duplication | Both | Optional |
| F11 | two final self-checks | clarity | Reasoning | Minor (co-locate) |
| F12 | applies condition in prose + schema | maintenance coupling | Reasoning | Awareness only |
| F13 | answer-the-assignment vs M5A edge | watch | Both | Watch-only |
| F14 | no-scores/levels 3× | reinforcement | Both | No action |
| F15 | blank-line gaps | cosmetic | — | No action |
| F16 | hydrated fields are reasoning-active (NON-finding) | guardrail | Reasoning | **Do NOT remove** |

---

## 4. Recommendation
Stage B's *philosophy* is coherent and self-governing (the Constitution resolves most overlaps by fiat),
so the honest answer to "is it internally coherent?" is **mostly yes — but it carries real historical
layering worth addressing intentionally.** Priorities for a future, *deliberate* (not experimental)
consolidation pass, each to be run through the Step-3 clean-control + noise-floor protocol because most
touch the output contract:

1. **F1** — reconcile the domain-independence paragraph with the built-in Constitution (only true *conflict*).
2. **F6** — make the nesting of the 3–4 per-turn loops explicit (biggest clarity win).
3. **F5** — unify the M5-intervention-type / M11-instructional-mode taxonomies.
4. **F7** — confirm whether `cultural_resources` is still live; disambiguate the knowledge vocabulary.
5. **F2/F3** — reduce the coaching-arc and anti-coauthoring restatements to one owner + deltas, *and
   benchmark behavior before/after* (do not assume the echoes are inert).

**Do not** address any of these by experimental field deletion. The Step-3 evidence (F16) shows that
apparent redundancy in the *output contract* can be reasoning-active; consolidation should be a
deliberate editorial decision, verified against the noise-floor, one change at a time.
