# F1 Reconciliation Proposal — "domain-independent reasoner" vs the built-in Constitution

**Date:** 2026-07-29 · **Status:** PROPOSAL ONLY — no code modified. Awaiting approval before any edit.
**Scope:** exactly ONE passage (`server.py` L908). Nothing else in Stage B changes. No output-schema
field changes → the Stage B output contract, the hydrator, and all downstream consumers are untouched.

---

## 1. The conflicting passages (verbatim)

### Passage A — the domain-independence paragraph (`server.py` L908)
> "You are domain-independent as a REASONER. You hold **NO built-in instructional sequence for essay
> writing**. Domain-specific writing knowledge comes **ONLY from the CANONICAL WRITING MODEL supplied in
> the request**. Keep the two forms of knowledge distinct: (1) developmental reasoning (this engine,
> domain-independent) and (2) canonical writing knowledge (structured cultural resources you consult).
> Do not collapse them."

### Passage B — the Constitution's built-in sequence + built-in canonical knowledge (L854, L858, L863–867, L886)
> **Principle 5 (L854):** "DEPENDENCY-FIRST INSTRUCTION. Whenever a higher-level structure depends on an
> undeveloped lower-level conceptual or rhetorical element, teach the dependency FIRST, then return to the
> higher-level structure. Applies generally …"

> **Default sequence (L858):** "DEFAULT GUIDED COMPOSITION INSTRUCTIONAL SEQUENCE (the recognizable shape
> of every coaching cycle unless another constitutional principle requires otherwise): (1) recognize
> emerging competence; (2) explicitly identify the instructional focus; (3) explain the purpose of that
> structure; (4) identify any missing dependency; (5) teach or scaffold that dependency; (6) return to the
> larger structure; (7) return responsibility to the learner …"

> **Canonical structural hierarchy (L863–867):** "THE CANONICAL STRUCTURAL HIERARCHY … Whole Composition →
> Major Parts → Paragraph → Structural Elements → Relationships among Elements → Sentences → Words. …"

> **Canonical exit criteria (L886 + the injected `<<CANONICAL_EXIT_CRITERIA>>` block):** "CANONICAL
> STRUCTURAL ELEMENTS & DEVELOPMENTAL EXIT CRITERIA (v1.0 — the constrained structural space; use these to
> locate the element, judge sufficiency, and choose the next operation)."

### Passage C — a NEARBY passage that is correct and must NOT be contradicted (L910)
> "CANONICAL WRITING MODEL — the supplied domains describe culturally established FUNCTIONS of effective
> writing … They are NOT developmental stages, NOT a required sequence, NOT rigid templates. Never force
> the student through the domains in a predetermined order. Determine which domains are currently RELEVANT
> based on teacher purpose, student purpose, assignment, audience, genre, current writing, and interaction
> history."

---

## 2. Why they conflict

Passage A makes two **literal factual claims about the system's own architecture** that are no longer
true after the three-layer / Constitution redesign:

1. **"You hold NO built-in instructional sequence for essay writing."**
   Directly false: Passage B's **Default Guided Composition Sequence** (7 steps) and **Principle 5
   (Dependency-First)** ARE a built-in instructional sequence, and the **CANONICAL COACHING SEQUENCE**
   (L890) restates it. The system now deliberately carries a built-in coaching arc.

2. **"Domain-specific writing knowledge comes ONLY from the CANONICAL WRITING MODEL supplied in the request."**
   Directly false: canonical writing knowledge now also lives **inside the prompt** — the structural
   hierarchy (L863–867), the injected **developmental exit criteria** (L886), and the constitutional
   principles themselves. Writing knowledge is no longer sourced *only* from the per-request model.

This is the one place in Stage B where two instructions assert **opposite facts** (not merely different
emphases). Today the contradiction is *masked* — the Constitution's "highest authority … the
constitutional principle GOVERNS" clause (L845) means the model already resolves it in the Constitution's
favor. So Passage A is effectively **dead-but-misleading text**: overridden in practice, yet still telling
the model it has no built-in sequence and no built-in knowledge. That is exactly the kind of latent
layering you asked to surface: harmless to behavior *because* of the Constitution, but conceptually false
and a trap for future edits.

**Important boundary with Passage C:** Passage A's *valid* neighbor, Passage C, says the **order in which
DOMAINS/FUNCTIONS become relevant is not fixed** (which is true and must stay). That is a different claim
from Passage A's false one. The distinction the reconciliation must preserve:
- **The coaching ARC within a cycle** (recognize → name → explain → dependency → scaffold → return →
  release) **is built-in and canonical** (Constitution). ✅ built-in
- **WHICH element/domain is relevant this turn, and in what order across turns** is **context-driven and
  NOT fixed** (Passage C). ✅ not built-in
Passage A currently blurs these into a single over-broad "no built-in sequence," which is why it reads as
a conflict.

---

## 3. Proposed reconciliation (replace ONLY Passage A, L908)

### Proposed replacement text
> "You are domain-independent as a REASONER: your developmental reasoning process — interpreting the
> student's participation, diagnosing the single developmental bottleneck, selecting ONE target, and
> scaffolding it — carries no subject-matter content of its own. Your canonical WRITING knowledge has two
> authoritative sources, and you do not exceed them: (1) the constitutional writing architecture built
> into these instructions — the Constitution's principles and Default Guided Composition sequence, the
> canonical structural hierarchy, and the developmental exit criteria; and (2) the canonical writing
> model, retrieved instructional objects, and resources supplied in each request. Keep the two FORMS of
> knowledge distinct — developmental reasoning (HOW to teach) versus canonical writing knowledge (WHAT is
> true about writing) — and do not collapse them. Do not invent domain-specific writing facts,
> definitions, or rules beyond what the Constitution and the supplied canonical knowledge provide. (Which
> writing element or domain is relevant this turn, and its order across turns, is not fixed — see the
> CANONICAL WRITING MODEL note below.)"

### What changed, precisely
| Old (Passage A) | New | Reason |
|---|---|---|
| "You hold NO built-in instructional sequence for essay writing." | (removed; replaced by naming the Constitution + Default sequence as a legitimate built-in source) | It was factually false and contradicted the Constitution. |
| "Domain-specific writing knowledge comes ONLY from the CANONICAL WRITING MODEL supplied in the request." | "Your canonical WRITING knowledge has two authoritative sources … (1) constitutional architecture … (2) supplied model/objects/resources." | Reflects that canonical knowledge now lives both in-prompt and per-request. |
| "domain-independent as a REASONER … (1) developmental reasoning … (2) canonical writing knowledge … Do not collapse them." | **KEPT** (rephrased, same force): reasoning is domain-neutral; keep the two forms distinct. | This is the still-valid core intent. |
| *(implicit anti-hallucination)* | **STRENGTHENED**: "Do not invent domain-specific writing facts … beyond what the Constitution and supplied knowledge provide." | Makes the anti-hallucination guard explicit and internally consistent. |
| *(none)* | **ADDED** one clause pointing to L910 so the ARC-vs-DOMAIN-ORDER distinction is explicit. | Prevents creating a NEW conflict with Passage C. |

---

## 4. Why this preserves existing behavior

1. **It codifies what the model already does.** Because of the Constitution's "highest authority" clause,
   the engine already follows the built-in Default sequence and already consults the supplied objects.
   The old text's literal claim was already being overridden. Aligning the wording to actual behavior is
   therefore expected to be **behavior-neutral or behavior-stabilizing**, not behavior-changing.

2. **No output-contract change.** Not one field of the JSON schema is touched. `_build_prompt`, the
   hydrator, `KB_ELEMENT_MAP`, and every downstream consumer (Stage C, Teacher Review) are unaffected.
   The only bytes that change are inside `SYSTEM_MESSAGE`.

3. **The two valuable intents are retained in full force:**
   - *distinctness* ("keep developmental reasoning vs canonical writing knowledge distinct; do not
     collapse them") — preserved verbatim in meaning;
   - *anti-hallucination* ("do not invent writing facts beyond supplied/canonical") — preserved and made
     explicit.

4. **Anti-template behavior is not weakened.** One might worry that the word "domain-independent / no
   built-in sequence" was what kept the model from imposing rigid essay templates. It is not the load-
   bearing guarantee for that: anti-template behavior is independently and robustly enforced by Passage C
   (L910 "NOT a required sequence, NOT rigid templates, Never force … a predetermined order") and by every
   framework's "FUNCTIONAL, not formulaic" rules (M6 L918, M7 L926, M8 L933, M9, M10 L948). Removing the
   false clause leaves all of those intact, and the added cross-reference to L910 reinforces them.

5. **No new conflict is introduced.** The reconciliation explicitly separates the built-in *coaching arc*
   (canonical) from the context-driven *choice/order of elements* (not fixed), so it agrees with both the
   Constitution (Passage B) and the Canonical Writing Model note (Passage C).

---

## 5. Proposed verification plan (AFTER you approve the wording — not run yet)
Same clean-control + noise-floor protocol we just validated, one change only:
- **Frozen baseline** = current `SYSTEM_MESSAGE` (sys-msg hash `1c485e2c13d7b8ff`), ≥2 provenance-stamped
  12-case smoke runs → re-measure the object noise floor (expected ~83%, TC55/TC61 unstable).
- **Candidate** = identical prompt with ONLY Passage A replaced → ≥2 provenance-stamped runs.
- **Certify** per the per-case rule: the F1 change must **not destabilize any case the frozen baseline
  holds stable** (esp. TC37/TC49, now known baseline-stable). Because F1 is a reasoning-framing change, I'd
  also eyeball two restraint/anti-template cases (e.g. a narrative/reflective case) to confirm no new
  template-imposition — reported qualitatively, not as a pass/fail metric.
- Log the result (certify or roll back) in `MIGRATION_LOG.md` with both code hashes, exactly as for G2F1.

No other finding (F6, F5, F7, F2/F3) is touched until F1 is agreed and benchmarked. One architectural
change at a time.
