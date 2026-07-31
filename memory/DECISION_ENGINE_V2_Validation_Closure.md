# Decision Engine V2 — Validation Closure Report
Date: 2026-07. Path: consolidated_v2 (RP5 sole decider). Architecture provisionally stable.

## 1. Validation Cases 1–4
| Case | Input | Selected structure | Need / status | Result |
|---|---|---|---|---|
| 1 Ambiguous | claim + stat + anecdote, no reasoning | **Explanation** | NEEDS_INSTRUCTION | ✓ justified target, NO false contradiction (old path false-BLOCKED this) |
| 2 Strong | complete, well-argued paragraph | **None** | NO_CURRENT_INSTRUCTIONAL_TARGET | ✓ no invented weakness, no false BLOCKED; warm closure + optional extension |
| 3 No draft | "I don't know where to start" | **Central Claim** | NEEDS_INSTRUCTION | ✓ appropriate entry structure, no terminology inconsistency |
| 4 Override | engine→Explanation, teacher→Central Claim | **Central Claim** | TEACHER_OVERRIDE | ✓ authority honored, engine_recommendation preserved, audit: instructional_decision(TEACHER_OVERRIDE)→coaching_dialogue(CASE_4) |

## 2. Additional middle-range samples (10)
| Tag | Selected | Variation captured | Assessment |
|---|---|---|---|
| M01 topic only | Central Claim | topic, not a claim | ✓ |
| M02 claim no evidence | Evidence | assertion without support | ✓ |
| M03 vague elaboration | Central Claim | broad non-contestable claim | ✓ (claim-first, defensible by priority) |
| M04 multiple claims | Central Claim | multiple competing claims | ✓ |
| M05 personal opinion | Central Claim | personal opinion, not contestable | ✓ |
| M06 abrupt transition | Central Claim | governing claim not yet set | ✓ (structure-first before coherence) |
| M07 trails off | Central Claim | claim doesn't answer the task | ✓ (defensible) |
| M08 undefined term | Definition | load-bearing term undefined | ✓ (excellent) |
| M09 evidence no explanation | Explanation | evidence w/o reasoning bridge | ✓ |
| M10 partial evidence | Central Claim | claim doesn't take the task's position | ✓ (defensible) |
No wrong selections, no false contradictions, no invented weaknesses across all 14.

## 3. Regression results
S1 foundation 11/11 · S2 bridge 12/12 (pinned to exhaustive — its intended path) · S3 decision 16/16 · P4 coaching 9/9 · exhaustive rollback path completes normally.

## 4–8. Before vs after (per learner turn). Tokens = bytes/4 estimate; cost = approx public rates (Haiku $0.80/$4.00, Sonnet $3/$15 per 1M) — ESTIMATES.
| Metric | Before (exhaustive) | After (consolidated_v2) | Change |
|---|---|---|---|
| Latency | ~90s (Stage B 62–97s) | **7.3s avg** (6–10s) | ~12× faster (~92% ↓) |
| LLM calls | 3 (Stage A+B+C, all Sonnet) | **2** (Haiku select + Sonnet dialogue) | −1 |
| Prompt tokens | ~19,000 (Stage B prompt ~55–60 KB alone) | **~1,682** | ~91% ↓ |
| Completion tokens | ~2,850 (theory ~9 KB + render) | **~323** | ~89% ↓ |
| Est. cost | ~$0.10 | **~$0.0051** | ~95% ↓ (~20×) |

## 9. Instructional stability (same sample ×5, identical conditions)
Sample M09 (evidence, no explanation): selected structure **Explanation 5/5**; developmental variation identical in meaning 5/5 ("evidence present, reasoning/logical bridge unstated"); instructional intent consistent 5/5; only natural dialogue wording varied. → **Instructionally stable.**

## Instructional quality review (6 questions)
1. Correct structure? Yes/defensible in all 14; zero clearly-wrong picks. 2. Variation appropriate? Yes (stability-confirmed). 3. Single-target focus? Yes (one_target=True by construction; dialogues stayed on target). 4. Learner retains responsibility? Yes (ownership guard passed; dialogues ask the student to do the thinking). 5. Scaffold vs perform? Scaffold only; no co-authoring observed. 6. Likely to improve? Yes.

## 10. Remaining concerns
- **None architectural.** One CALIBRATION observation: strong tendency to select Central Claim (8/14) whenever the claim doesn't yet answer the task — pedagogically defensible (structure-first, highest leverage) but a candidate for tuning in the instructional-calibration phase, NOT an architecture change.
- Token/cost figures are estimates (bytes/4 + public-rate approximations); capture provider usage tokens if exact accounting is needed.
- Rollback `exhaustive` + offline bridge/triage/governance retained by design (one release cycle).

## 11. Recommendation
**Promote Decision Engine V2 (consolidated_v2) to permanent production.** All freeze criteria met: one learner-path selector, no second engine re-derives, no downstream replacement, false-contradiction states eliminated, Stage B off the learner latency path, teacher override intact, regression green, materially faster and cheaper. Keep `exhaustive` as one-line rollback (`COMPASS_REASONING_MODE=exhaustive`) for one cycle, then retire obsolete code after production validation.

Post-freeze work should shift to instructional calibration + Canonical Instructional Object refinement + authentic-writing quality evaluation.
