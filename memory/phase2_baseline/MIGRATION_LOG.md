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

Established noise floor — CORRECTED 2026-07-29 on a CLEAN, provenance-stamped control
(frozen `server.py` sha256 `2cc4bdcb…`, sys-msg `1c485e2c13d7b8ff`, two same-code 12-case runs):
object **83% (10/12)** — NOT 100% as previously assumed · dependency 50% · sequence 91% ·
sufficiency 91% · free-text (bottleneck/exit/next) Jaccard ≈ 0.07/0.38/0.15.
Baseline-noisy object cases (vary on identical code): **TC55, TC61**. Everything else stable.
⇒ Certification can NO LONGER demand 100% object agreement; the correct test is PER-CASE:
does the candidate destabilize a case the frozen baseline held STABLE? (See ATTEMPT #2.)

PROVENANCE POLICY (adopted 2026-07-29, permanent): every `stage_b_baseline.py capture` now
stamps its output + log with git commit, working-tree-dirty flag, `server.py` sha256, and the
loaded SYSTEM_MESSAGE sha256_16. `compare` prints both files' provenance and auto-flags when two
files share an identical `server.py` sha256 (⇒ that comparison is a NOISE-FLOOR, same-code run).
Every benchmark result is now permanently tied to the exact code that produced it.

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
- **Experimental change:** removed ONLY this field from the Stage B `structural_reasoning` output
  contract + reworded prompt step 5 ("use these to inform your judgment … you do NOT output them").
  Hydrator already supplies relationships downstream.
- **Controls (CLEAN, provenance-verified — the whole point of this re-run):**
  - FROZEN baseline: commit `d5686a0`, `server.py` sha256 `2cc4bdcb…`, sys-msg `1c485e2c13d7b8ff`.
    Files: `stage_b_g2f1_baseline_d5686a0_run{1..5}.json`.
  - CANDIDATE: commit `e0fa10b`, `server.py` sha256 `68ae56c7…`, sys-msg `3c72345527a89173`.
    Files: `stage_b_g2f1_candidate_e0fa10b_run{1..5}.json`.
  - (The prior session's runs were DISCARDED: they imported `server.py` while the candidate diff was
    on disk, so both "baseline" and "candidate" ran identical candidate code — ambiguous control.)
- **Noise floor (frozen run1 vs run2, 12-case):** object 10/12 (83%), dependency 6/12,
  sequence 11/12, sufficiency 11/12; free-text Jaccard 0.07/0.38/0.15. Baseline-unstable object
  cases = TC55, TC61.
- **Migration effect (frozen vs candidate, 12-case):** object agreement ~75% — near the noise
  floor in aggregate, BUT the per-case signal is decisive. Focused n=5 confirmation on the 3 suspect
  cases (frozen `run{1..5}` vs candidate `run{1..5}`):

  | Case | Frozen object (n=5) | Candidate object (n=5) | Read |
  |---|---|---|---|
  | **TC37** | `thesis` 5/5 (100% stable) | thesis **2/5** (+overall_organization×2, communicative_purpose×1) | **destabilized** |
  | **TC49** | `thesis` 5/5 (100% stable) | thesis **2/5** (+communicative_purpose×2, None×1) | **destabilized** |
  | TC66 | communicative_purpose 4/5 | communicative_purpose 4/5 | within noise (no effect) |

- **Noise-floor comparison:** TC37 and TC49 are 100% stable on frozen code (zero variance across 5
  same-code runs) yet collapse to 40% agreement with the baseline-correct object under the candidate,
  in multiple divergent directions. That is a genuine migration effect ABOVE the noise floor — not
  model stochasticity (TC66, genuinely near-noisy in baseline, is unchanged → correct control behavior).
- **Final classification:** **Mixed (deterministic-content but epistemically-active reasoning scaffold).**
  Requiring Stage B to articulate the functional RELATIONSHIPS among elements evidently stabilizes the
  foundational `object` judgment. Identical lesson to ATTEMPT #1's two fields.
- **Rationale / decision:** **NOT CERTIFIED → ROLLED BACK** (2026-07-29). `server.py` restored to
  frozen `d5686a0` (sys-msg hash back to `1c485e2c13d7b8ff`, backend health 200). KEEP
  `element_relationships` in the Stage B output; continue hydrating downstream from
  `instructional_objects[el].related_elements` for consistency. `object` selection is too foundational
  to accept destabilization of a baseline-stable case.

---

## Implication for the rest of GROUP 2
Two consecutive "looks-deterministic" fields (Group 1's pair, and now `element_relationships`) have
each turned out to be reasoning-active. Working hypothesis: the STRUCTURAL-RELATION family of fields
(relationships / dependencies) scaffolds object selection and is unlikely to be safely removable.
Before spending runs on `developmental_dependencies` / `active_exit_criterion`, expect the same result;
test one at a time against the CLEAN provenance-stamped noise floor, and apply the per-case rule
(destabilization of a frozen-stable case = fail), not aggregate percentage.

---

## ATTEMPT #3 — Architectural reconciliation F1 (prompt reword, NOT a field removal)
- **Change:** reworded ONLY the L908 "domain-independence" paragraph to reconcile it with the Constitution
  (make the HOW-vs-WHAT distinction explicit; remove the two now-false claims). Output contract UNCHANGED.
- **Controls (provenance-stamped):** FROZEN sys-msg `1c485e2c13d7b8ff` (server.py `2cc4bdcb…`); reused the
  5 byte-identical baseline runs `stage_b_g2f1_baseline_d5686a0_run{1..5}.json`. CANDIDATE sys-msg
  `0208ae9f5ffa1209` (server.py `1e15c37f…`), runs `stage_b_f1_candidate_run{1..5}.json`.
- **Result (object):** 9/12 cases preserved; TC55/TC61/TC66 within the (already-noisy) frozen floor.
  **TC37**: frozen `thesis` 5/5 → candidate `thesis` 1/5 (overall_organization 3/5, cp 1/5).
  **TC49**: frozen `thesis` 5/5 → candidate `thesis` 1/5 (cp 2/5, None 2/5).
- **VERDICT: NOT CERTIFIED → ROLLED BACK** (sys-msg restored to `1c485e2c13d7b8ff`, backend 200).
- **META-FINDING (important):** TC37 & TC49 are the SAME two cases ATTEMPT #2 (G2F1) destabilized. TWO
  UNRELATED changes — one an output-contract REMOVAL, one a pure FRAMING REWORD — both tip exactly these
  two frozen-stable cases off `thesis` (toward overall_organization / communicative_purpose). This
  indicates TC37/TC49 sit on a thesis↔organization/purpose decision BOUNDARY and are sensitive to ANY
  prompt perturbation, not to the specific semantics of a change. Implication for methodology: the
  same-bytes "noise floor" measures SAMPLING noise only; it does not bound PERTURBATION noise (a
  behavior-neutral reword still shifts token attention). For prompt REWORDINGS (vs field removals) the
  per-case rule may be near-unpassable on these borderline cases. Candidate remedy: establish a
  "perturbation noise floor" (measure TC37/TC49 jitter under a KNOWN-neutral cosmetic edit) before judging
  a reword, OR require reword candidates to be minimal-delta. DECISION DEFERRED TO OWNER.
