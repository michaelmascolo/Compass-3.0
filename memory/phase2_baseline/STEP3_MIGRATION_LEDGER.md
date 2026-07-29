# Step 3 — Stage B Deterministic Migration Ledger

Permanent record of every field removed from the Stage B OUTPUT contract during the
LLM-centered → three-layer migration. One row per field.

Certification thresholds (product owner): object / exit(hydrated) / canonical-explanation /
architecture-relationship / strategy-selected = **100%**; bottleneck / dependency / next = **≥98%**;
sequence / evidence = **≥95%**. Success = instructional EQUIVALENCE (not textual similarity).
Cadence: implement → 12-case smoke → full 66 → certify, one group at a time.

## Smoke set (12, stride across the 66-case corpus, spans levels)
TC01, TC07, TC13, TC19, TC25, TC31, TC37, TC43, TC49, TC55, TC61, TC66

---

## GROUP 1 — canonical element knowledge
Status: ATTEMPTED → **NOT CERTIFIED → ROLLED BACK** (2026-06-29)

| Field | Why removal was attempted | Now comes from | Equivalence evidence / VERDICT |
|---|---|---|---|
| `instructional_reasoning.element_communicative_purpose` | Looked deterministic (a fixed property of the element). | KB hydrator `['purpose']` (already wired to Stage C + Teacher Review). | **REVERTED** — see finding below. |
| `instructional_reasoning.canonical_performance_structure` | Looked deterministic (canonical construction of the element). | KB hydrator `['performance_structure']`. | **REVERTED** — see finding below. |

### Method (noise-floor–controlled, per owner: judgment not text)
- A1 = pre-edit baseline (12-case smoke). B1 = post-edit candidate. B2 = post-edit 2nd run.
- Noise floor = agreement(B1, B2) [identical code → engine's run-to-run nondeterminism].
- Migration effect = agreement(A1, B1). Equivalence-preserving iff A1↔B1 ≈ B1↔B2.

### Results (12-case smoke)
| Field | Noise floor (B1↔B2) | Migration (A1↔B1) | Read |
|---|---|---|---|
| object | **12/12 (100%)** | **10/12 (83%)** | object is run-to-run STABLE, so the 2-case shift is a REAL migration effect |
| dependency | 6/12 (50%) | 6/12 (50%) | within noise — NOT a migration effect (engine nondeterminism) |
| sequence | 10/12 (83%) | 11/12 (91%) | within noise |
| sufficiency | 9/12 (75%) | 9/12 (75%) | within noise |
| bottleneck/exit/next (Jaccard) | 0.10 / 0.48 / 0.19 | 0.12 / 0.47 / 0.18 | free-text varies run-to-run regardless of code |

### VERDICT — NOT CERTIFIED, ROLLED BACK
- The 2 shifted cases (TC49, TC66) both moved `thesis → communicative_purpose` (same direction → not random noise). Since object is the foundational judgment REQUIRED at 100%, and the shift exceeds a 0% noise floor, Group 1 as implemented FAILS certification.
- Rollback verified: SYSTEM_MESSAGE sha256_16 restored to `7ecc6056f891af30` (frozen baseline). App returned to certified state.

### KEY FINDINGS (inform all future migration)
1. **These two fields are NOT purely deterministic output — they are REASONING SCAFFOLD.** Forcing the model to articulate an element's communicative purpose / performance structure evidently STABILIZES its object selection. Removing them from the output changed the judgment. Reclassify `element_communicative_purpose` + `canonical_performance_structure` as **Mixed (reasoning-critical)** → keep in Stage B (they are still ALSO hydrated for downstream use, which is correct — the hydrator gives consistency; keeping them in-prompt gives judgment stability).
2. **Noise-floor control is mandatory.** The engine has large inherent nondeterminism (dependency 50%, sequence 83%, sufficiency 75%, free-text low). Absolute thresholds (≥98% dependency) are UNREACHABLE with zero code change; certification must compare migration divergence against the same-code noise floor, per field.
3. **Certification metric must be per-field noise-relative**, exactly as the owner cautioned ("percentage is not an automatic pass").

### Implication for GROUP 2
Test `element_relationships`, `developmental_dependencies`, `active_exit_criterion` ONE field at a time against the noise floor. These are more plausibly pure output (they are cross-references/criteria, less likely to scaffold object selection) — but verify empirically. If object stays at its 100% noise floor after removal, certify; else reclassify as reasoning-critical and keep.


---

## GROUP 2 — canonical structural relations
Status: **Field 1 ATTEMPTED → NOT CERTIFIED → ROLLED BACK** (2026-07-29). Fields 2–3 NOT STARTED.

| Field | Why removal was attempted | Now comes from | Equivalence evidence / VERDICT |
|---|---|---|---|
| `structural_reasoning.element_relationships` | Looked deterministic (cross-references from KB). | KB hydrator `instructional_objects[el].related_elements`. | **REVERTED** — reclassified **Mixed (reasoning-active)**. See below. |
| `structural_reasoning.developmental_dependencies` | Looked deterministic (KB `exit.dependencies`). | KB hydrator. | NOT STARTED — expect same result (structural-relation family). |
| `structural_reasoning.active_exit_criterion` | Looked deterministic (KB `exit.exit_criterion`). | KB hydrator. | NOT STARTED. |

### Method (CLEAN, provenance-stamped — re-run after prior session's controls were ambiguous)
- Every capture now records git commit + `server.py` sha256 + SYSTEM_MESSAGE hash (permanent policy).
- FROZEN baseline: `d5686a0` / server.py `2cc4bdcb…` / sys-msg `1c485e2c13d7b8ff` (runs 1–5).
- CANDIDATE: `e0fa10b` / server.py `68ae56c7…` / sys-msg `3c72345527a89173` (runs 1–5).
- Certification test = PER-CASE: does the candidate destabilize a case the frozen baseline held stable?

### Results (12-case smoke + n=5 focused confirmation)
- Frozen object noise floor = **83% (10/12)**; baseline-unstable cases = TC55, TC61.
- **TC37**: frozen `thesis` 5/5 → candidate `thesis` 2/5 (destabilized).
- **TC49**: frozen `thesis` 5/5 → candidate `thesis` 2/5 (destabilized).
- **TC66**: frozen 4/5 → candidate 4/5 (within noise; no effect).

### VERDICT — NOT CERTIFIED, ROLLED BACK
- Two frozen-STABLE cases (TC37, TC49) collapse to 40% under the candidate, in divergent directions
  → real migration effect above the noise floor. `element_relationships` acts as a reasoning scaffold
  that stabilizes object selection → reclassify **Mixed**; keep in Stage B; keep hydrating downstream.
- Rollback verified: SYSTEM_MESSAGE hash restored to `1c485e2c13d7b8ff`, backend health 200.

### Implication
The STRUCTURAL-RELATION family (relationships / dependencies) is likely reasoning-active, not pure
output. Test `developmental_dependencies` / `active_exit_criterion` one at a time only if pursued;
expect the same finding. Certify per-case against the clean noise floor, never on aggregate %.
