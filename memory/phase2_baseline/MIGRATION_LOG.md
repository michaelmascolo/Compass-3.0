# Compass — Permanent Migration Log (Stage B deterministic migration)

A permanent, append-only record of EVERY migration attempt — including failed ones. Failed
migrations are part of the architecture: they document how we learned what each component does.

Field roles: **Judgment** (student-dependent) · **Deterministic-communicative** (student-independent,
only communicates a decision → safe to hydrate) · **Mixed** (deterministic content but
epistemically active during reasoning → keep in Stage B, also hydrate downstream).

Method: noise-floor–controlled smoke (12 cases) → if `object` stays at its noise floor, run the
full 66-case benchmark → certify or roll back. Certification compares INSTRUCTIONAL JUDGMENT
(categorical exact) and free-text CONTENT SIMILARITY (Jaccard), never textual identity, and always
relative to the same-code noise floor.

Established noise floor (12-case smoke, same code): object ≈ 100% (stable) · dependency ≈ 50% ·
sequence ≈ 83% · sufficiency ≈ 75% · free-text (bottleneck/exit/next) Jaccard ≈ 0.10/0.48/0.19.
(Being widened to 2–3 same-code runs.)

---

## ATTEMPT #1 — Group 1: `element_communicative_purpose` + `canonical_performance_structure`
- **Original classification:** Deterministic (assumed pure output).
- **Experimental change:** removed both from Stage B `instructional_reasoning` output + dropped the
  "(→ field)" hints in prompt step 4 (reasoning guidance otherwise unchanged). Hydrator already
  supplies both downstream.
- **Benchmark outcome (12-case smoke):** object 10/12 (83%); dependency 6/12; sequence 11/12;
  sufficiency 9/12; free-text Jaccard ~0.12/0.47/0.18.
- **Noise-floor comparison:** noise floor object = 12/12 (100%); dependency/sequence/sufficiency and
  free-text all matched the migration numbers (→ that variation is stochastic, not migration). The
  ONLY signal above noise was `object` (100% → 83%), with both shifts `thesis→communicative_purpose`
  (same direction → not random).
- **Final classification:** **Mixed (deterministic-but-epistemically-active).** The fields are
  reasoning scaffolds; articulating them stabilizes object selection.
- **Rationale / decision:** object is the foundational judgment required at 100%; a real shift above
  a 0% noise floor is unacceptable → **ROLLED BACK** (SYSTEM_MESSAGE hash restored to
  `7ecc6056f891af30`, verified). KEEP both in Stage B; continue hydrating downstream for consistency.

---

## ATTEMPT #2 — Group 2 Field 1: `structural_reasoning.element_relationships`
- **Original classification:** Deterministic-communicative (KB `io.related_elements`).
- **Experimental change:** (in progress) remove ONLY this field from Stage B output.
- **Benchmark outcome:** (pending)
- **Noise-floor comparison:** (pending)
- **Final classification:** (pending)
- **Rationale / decision:** (pending)
