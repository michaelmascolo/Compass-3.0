# F1 Reconciliation Proposal — "domain-independent reasoner" vs the built-in Constitution

**Date:** 2026-07-29 · **Status:** APPROVED (with owner wording revision, §6) — implementation + benchmark
in progress. Scope: exactly ONE passage (`server.py` L908). No output-schema field changes → the Stage B
output contract, the hydrator, and all downstream consumers are untouched.

---

## 1. The conflicting passages (verbatim)

### Passage A — the domain-independence paragraph (`server.py` L908)
> "You are domain-independent as a REASONER. You hold **NO built-in instructional sequence for essay
> writing**. Domain-specific writing knowledge comes **ONLY from the CANONICAL WRITING MODEL supplied in
> the request**. Keep the two forms of knowledge distinct: (1) developmental reasoning (this engine,
> domain-independent) and (2) canonical writing knowledge (structured cultural resources you consult).
> Do not collapse them."

### Passage B — the Constitution's built-in sequence + built-in canonical knowledge (L854, L858, L863–867, L886)
> **Principle 5 (L854):** "DEPENDENCY-FIRST INSTRUCTION …"
> **Default sequence (L858):** "DEFAULT GUIDED COMPOSITION INSTRUCTIONAL SEQUENCE … (1) recognize emerging
> competence … (7) return responsibility to the learner …"
> **Canonical structural hierarchy (L863–867):** "Whole Composition → Major Parts → Paragraph → Structural
> Elements → Relationships → Sentences → Words."
> **Canonical exit criteria (L886 + injected `<<CANONICAL_EXIT_CRITERIA>>`):** "CANONICAL STRUCTURAL
> ELEMENTS & DEVELOPMENTAL EXIT CRITERIA (v1.0 …)."

### Passage C — nearby, correct, must NOT be contradicted (L910)
> "CANONICAL WRITING MODEL — the supplied domains … are NOT a required sequence, NOT rigid templates.
> Never force the student through the domains in a predetermined order. Determine which domains are
> currently RELEVANT based on teacher purpose, student purpose, assignment, audience, genre, current
> writing, and interaction history."

---

## 2. Why they conflict
Passage A makes two literal claims about the system's own architecture that are no longer true:
1. **"No built-in instructional sequence"** — false: the Constitution's Default Guided Composition
   Sequence + Dependency-First ARE a built-in method.
2. **"Writing knowledge comes ONLY from the supplied model"** — false: canonical writing knowledge now
   also lives in-prompt (hierarchy + exit criteria).
Today the contradiction is *masked* by the Constitution's "highest authority" clause (the model already
sides with the Constitution), so Passage A is **dead-but-misleading text**: overridden in practice yet
still asserting a false architecture.

**Boundary with Passage C:** the coaching ARC within a cycle is built-in & canonical (Constitution);
WHICH element/domain is relevant and its order across turns is context-driven & NOT fixed (Passage C).
Passage A over-broadly denies any built-in structure and blurs these; the fix must preserve C.

---

## 3. Original proposed wording (SUPERSEDED — see §6)
The first draft framed it as canonical writing knowledge having "two authoritative sources." The owner
correctly flagged that this conflates two DIFFERENT functions. Superseded by §6.

---

## 4. Why this preserves existing behavior
1. Codifies what the model already does (Passage A was already overridden) → behavior-neutral/stabilizing.
2. No output-contract change → hydrator / Stage C / Teacher Review untouched; only `SYSTEM_MESSAGE` bytes
   change.
3. Retains the two valuable intents: keep reasoning-vs-writing-knowledge distinct; do not invent writing
   facts beyond canonical knowledge (anti-hallucination, now explicit).
4. Anti-template behavior is independently guaranteed by Passage C (L910) + every framework's "functional,
   not formulaic" rule (M6–M10) — untouched, and reinforced by the added cross-reference.
5. Introduces no new conflict — agrees with both the Constitution (B) and the Canonical Writing Model (C).

---

## 5. Verification plan
Clean-control + noise-floor protocol, one change only. Frozen baseline = current `SYSTEM_MESSAGE`
(sys-msg `1c485e2c13d7b8ff`, server.py `2cc4bdcb…`); its 12-case object noise floor is already measured at
83% (TC55/TC61 unstable) from provenance-stamped runs `stage_b_g2f1_baseline_d5686a0_run{1..5}.json`
(byte-identical code → reusable as the F1 baseline). Candidate = identical prompt with ONLY Passage A
replaced. Certify per the PER-CASE rule: the change must NOT destabilize any case the frozen baseline
holds stable (esp. TC37/TC49). Plus a qualitative anti-template eyeball on a narrative/reflective case.
Log both code hashes + verdict in `MIGRATION_LOG.md`.

---

## 6. FINAL agreed wording (owner-revised — HOW vs WHAT made explicit)
Replace Passage A (L908) with:

> "You are domain-independent as a REASONER: the developmental reasoning process itself — interpreting the
> student's participation, diagnosing the single developmental bottleneck, selecting ONE target, and
> scaffolding it — carries no subject-matter content of its own. Two DIFFERENT things operate on every
> turn and must never be collapsed: (1) HOW Compass reasons and teaches is governed by the COMPASS
> CONSTITUTION and this developmental engine — its principles and the Default Guided Composition sequence
> are your METHOD, not writing content; (2) WHAT Compass knows about writing comes ONLY from CANONICAL
> WRITING KNOWLEDGE — the canonical structural hierarchy and developmental exit criteria provided in these
> instructions, together with the canonical writing model, retrieved instructional objects, and resources
> supplied in each request. Do not invent writing facts, definitions, or rules beyond this canonical
> knowledge. Keep the two distinct: the Constitution governs HOW Compass reasons; the Canonical Writing
> Model / Knowledge Base provides WHAT Compass knows about writing. (Which writing element or domain is
> relevant this turn, and its order across turns, is not fixed — see the CANONICAL WRITING MODEL note
> below.)"

Rationale for the revision: the Constitution and the Canonical Writing Model serve different functions —
governance/method (HOW) vs writing content (WHAT). The final wording names that distinction explicitly and
does not describe the Constitution as a "source of writing knowledge." The built-in canonical structural
hierarchy and exit criteria are correctly placed on the WHAT side (they are writing knowledge that happens
to live in-prompt), while the Constitution and engine are on the HOW side.
