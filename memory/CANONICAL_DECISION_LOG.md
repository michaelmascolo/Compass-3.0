# Compass — Canonical Decision Log

Adopted decisions governing the instructional engine, evaluator, benchmark suite, and beta strategy. Newest at top.

---

## ADOPTED — 2026-06 · Dependency-First Instruction (core canonical principle)

**Dependency-First Instruction** is now one of Compass's core instructional principles. It governs ALL Guided Composition coaching, not only thesis development.

**Principle:** Whenever Compass identifies a higher-level instructional goal, it first determines whether that goal depends on a lower-level conceptual or rhetorical element that has not yet been sufficiently developed. If so, it **teaches the dependency first, then returns to the higher-level structure.** Compass does not ask students to improve a structure before they possess the conceptual ingredients that structure requires (this is developmentally premature — the student does not yet understand *why* the structure is incomplete).

**Examples (general, not thesis-specific):**
- **Thesis** — instead of "strengthen your thesis," if the reader cannot yet understand what the central concept *means*, develop the concept first, then return to the thesis.
- **Topic sentence** — instead of "write a better topic sentence," if the student does not yet know the central idea it should express, develop the idea first, then return to the topic sentence.
- **Argument** — instead of "make your argument stronger," if it lacks evidence, reasoning, or conceptual clarity, teach that dependency first, then return to strengthening the argument.
- **Transitions** — instead of "write a better transition," if the relationship between the two ideas is itself unclear, help the student articulate the relationship first, then write the transition.

**Compass's core instructional principles now include:**
- Teach one structural move at a time.
- Make the instructional focus explicit.
- Preserve student authorship (never coauthor / supply copyable content).
- Strengthen emerging structures rather than replacing them.
- **Teach the missing dependency before returning to the larger structure (Dependency-First Instruction).**

**Implementation:** SYSTEM_MESSAGE refinement **W-E** in `backend/server.py` + `InstructionalReasoning` fields `required_dependency` / `dependency_status` (none|identified|being_taught|addressed) / `dependency_rationale`; reuses `continue_consolidate_release_or_shift = shift_to_prerequisite`. Coordinates with W-A (consolidate the dependency by principle), W-B (do not invent a dependency on competent work), W-C (no copyable content), and the one-target/one-invitation rules.

**Teacher visibility:** the Dev Panel surfaces the reasoning in TEACHER language only — "Current instructional focus", "Dependency currently being developed", "Why this comes first" — and NEVER exposes internal field names (`required_dependency`, `dependency_status`). The goal is to make Compass's instructional *reasoning* transparent, not its internal architecture.

---


## ADOPTED — 2026-07-20 · Expanded-suite generalization audit & beta posture

1. **Benchmark suite expanded 32 → 66 cases** to test whether the instructional architecture *generalizes* across a broad range of writing situations (genres, writing elements, learner states, proficiency levels), rather than to optimize performance on the original 32.
2. **Further benchmark expansion is DEFERRED until after the public beta.** The current 66-case suite is the frozen benchmark for the beta period.
3. **Purpose of the Expanded Suite v1 Baseline run is to identify launch-blocking weaknesses**, not to pursue perfect benchmark performance. Result: 58/8/0 (87.9%); 93.8% on the original 32 and 82.4% on the 34 new cases; **zero failures; no launch-blocking (Class A) issues.**
4. **Beta readiness is determined by instructional integrity and first-use reliability** — the anti-coauthoring/authorship boundary holding, safe and on-purpose instruction, and reliable first-use behavior — **not** by a requirement that every benchmark case pass. Under this criterion Compass is judged **beta-ready**.
5. **Engine and evaluator remain FROZEN** pending explicit approval. At most **one focused engine-refinement cycle** is permitted during beta prep unless a serious authorship, safety, or reliability problem is found (none was). Proposed (awaiting approval): R1 consolidation-by-general-principle, R2 honor explicit teacher-specified target, optional R3 AI-paste authorship prompt.

## ADOPTED — 2026-07-20 · Evaluator calibrated to Compass fidelity, then frozen
- Evaluator rewritten to judge Compass by its own philosophy (principles P1–P10: scaffolding≠coauthoring, respect competent performance, consolidate-by-principle, communicative-purpose-first, evidence-based, etc.). After calibration the evaluator is **frozen**; it will not be modified unless a later engine analysis demonstrates it is *demonstrably inconsistent* with Compass principles.

## ADOPTED — 2026-07-20 · Engine refinement cycle W-A→W-D (evaluator held constant)
- Engine improved via SYSTEM_MESSAGE-only refinements: W-A consolidation-by-principle, W-B restraint on competent performance, W-C no copyable content, W-D honor teacher purpose + developmental profile. Result on the 32-case suite: 75.0% → 90.6%, 0 fails. Deltas attributable to engine only (evaluator frozen).

---

# Benchmark Framework (canonical)

- **Suite:** `backend/test_cases/instructional_test_cases.json`, 66 cases (TC01–TC32 original essay-centric; TC33–TC66 diversity expansion). Frozen for beta.
- **Case schema:** id, name, level, assignment, pedagogical_purpose, current_writing_task, initial_draft, responses[], initial_profile[], expected_issues[], expected_primary_target, avoid_behaviors[].
- **Harness (developer-only, `?tests`):** runs each case through the REAL production engine (STAGE-A retrieval → networks → one-target → governed instruction → anti-coauthoring → developmental memory), then grades the actual decisions with a SEPARATE frozen LLM evaluator. Runs persist in Mongo `test_runs`; JSON/Markdown export; labels + rename; Compare-Two-Runs.
- **Verdict scale:** pass / partial (genuine developmental concern) / fail (hard Compass violation: coauthoring, >1 target, invented deficiency on competent work, overriding explicit genre constraint, performing the writing).
- **Grouped reporting rule (external, applied at report time — cases NOT modified):** genre = communicative purpose; writing element = primary instructional object; student state = defining learner condition (else "typical developing writer"); proficiency = `level` normalized to Middle/early-secondary (grades 7–9), High school (10–12), College, Adult/Professional. Categories with n<3 are directional only.
- **Change control:** benchmark cases are not modified during or immediately after a run; no per-case optimization to inflate score.

# Beta Strategy (canonical)

- **Launch gate:** instructional integrity (authorship boundary intact, safe/on-purpose instruction) + first-use reliability. NOT universal benchmark passing.
- **Weakness classification for launch:** A = launch-blocking (undermines trust, student authorship, instructional safety, or basic first-use); B = important but not launch-blocking (document + address post-beta or in the single permitted refinement round); C = edge case (may remain in beta if disclosed internally).
- **Current posture:** No Class A issues. Class B: W1 consolidation-by-principle, W2 target precision vs. teacher purpose, W3a AI-paste authorship surfacing. Class C: W3b parenthetical steering.
- **Refinement budget for beta:** ≤1 focused engine-refinement cycle unless a serious authorship/safety/reliability problem emerges. Every refinement must be re-benchmarked (full 66-case run) and compared against `fd0dec0c` (Expanded Suite v1 Baseline) via Compare-Two-Runs to confirm gains without regressions.

---

# CIO Distinctness Principle (canonical — adopted 2026-06)

**A developmental object is a distinct CIO only if it satisfies BOTH:**
1. It represents a genuinely distinct instructional **judgment**, AND
2. It requires a genuinely distinct instructional **intervention**.

A conceptual distinction alone is NOT sufficient. If the intervention is effectively the same as
an existing CIO, the object remains **part of that existing CIO** (as an indicator/subtype), not a
separate developmental object. Goal: preserve clean instructional boundaries; never add a CIO
merely to complete a list.

**First application — CIO #6 (Organization), single-paragraph scope (DEFERRED):**
Organization (sequence/order of ideas) IS a distinct judgment from Paragraph Unity (membership —
does every sentence serve one idea), BUT at single-paragraph scale the intervention is identical
(name the point, then keep/cut/**move**/split), and the live selector never reaches for it (deeper
gaps dominate, or Unity's "poorly-coordinated support" already catches the residue). Fails
condition 2 → NOT a distinct CIO at single-paragraph scale. Deferred until multi-paragraph
composition, where sequencing already-unified paragraphs is a genuinely distinct intervention that
Paragraph Unity cannot express. Analysis: `PHASE2_CIO06_Organization_ANALYSIS.md`. No code changed.

---

# Developmental Instruction Voice Refinement (2026-06) — first-turn dialogue only

Applied to the FIRST-TURN block of `generate_dialogue` + `_DLG_SYS` (prompt-only; no engine/CIO/
selector/sufficiency/DB/audit/UI change). Compass = developmental teacher, not writing coach.
First turn now enforces:
1. ACCOMPLISHMENT — completed achievement, definitive verbs ("You have identified/established/
   developed/distinguished"); banned "you've already…"/progress language.
2. INTRODUCE — "Your next task is to develop a [structure]"; banned sharpen/improve/strengthen/fix.
3. TEACH FUNCTION — how the structure WORKS / how to think with it (not a flat "A X is…" definition).
4. COMPARE (not critique) — "Compared with the structure we just described…" / "Your writing already
   contains the beginning of this structure…"; structure is subject, paper is evidence.
5. INVITATION — emerges from the concept, requires using it; no rhetorical/assignment-specific coaching.
6. STOP.
Validated live across all 5 calibrated CIOs (Central Claim, Explanation, Evidence, Definition,
Paragraph Main Point): 5/5 definitive accomplishment, next-task framing, function-teaching, compare-
framing, concept-dependent invitation. Continuation mode unchanged. Harness: /tmp/wt/validate_voice_all5.py

---

# Constraints-Before-Strategies: DISCOVERY vs RESCUE (2026-06) — first-turn/continuation dialogue

Default DISCOVERY withholds solution strategies; teaches structure + function + constraints only.
Removed the default "different writers satisfy this in different ways…+examples" from the first turn.
RESCUE (adaptive) may offer strategies AS POSSIBILITIES (never recommendations) only when the learner
is stuck after attempts or explicitly asks.
Wiring (minimal, additive): new state field InstructionalState.current_target_attempts (int, default 0),
incremented on same-target continuation, reset to 0 on a new/first target. generate_dialogue gained a
`rescue` param. run() sets rescue = (continuation AND (current_target_attempts>=2 OR _wants_help(text))).
_wants_help = regex on learner message for explicit example/help/stuck signals.
Validated live: T1 first=DISCOVERY(no strategies); T2 1st continuation=DISCOVERY; T3 2nd continuation=RESCUE;
explicit-request on a continuation turn=RESCUE. Signal detector accurate.
WATCH: a pure help-only 'answer' turn with no draft content can route to the closure path (selector
returns no target, frozen behavior) and thus bypass continuation/RESCUE — selector-owned, out of scope.
Harness: /tmp/wt/validate_rescue.py, /tmp/wt/validate_rescue2.py
