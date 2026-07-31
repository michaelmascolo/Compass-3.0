# CHANGELOG

## 2026-07 — Decision Engine V2 FROZEN (canonical learner-path architecture)
- **Status: ACCEPTED & FROZEN.** `consolidated_v2` (RP5 `compass_structure_engine`) is the
  canonical learner-path instructional architecture. No architectural redesign/extension
  unless a genuine architectural defect is later discovered.
- Single learner-path selector: `compass_structure_engine.select_structure`. No second engine
  re-derives, replaces, or reinterprets the target. Dialogue engine builds the fixed target only.
- Default `reasoning_mode = consolidated_v2` (env flag `COMPASS_REASONING_MODE`).
  **Rollback = set `COMPASS_REASONING_MODE=exhaustive`** — retained for ONE release cycle only.
  After successful production use, retire obsolete decision code (Stage A/B/C target selection,
  Sprint-2 bridge write, Sprint-3 `decide`, RP4 `select_response`, triage, governance).
- Retired from live learner path (kept for rollback/offline only): `_select_relevant_domains`
  (Stage A), `SYSTEM_MESSAGE`/`_run_engine` (Stage B), Stage C renderer, Sprint-3
  `decide_for_session`/`decide`, RP4 `select_response`, `triage_experimental`, `governance_v2`.
- Kept as consumers (unchanged): Sprint-1 state, evidence, audit, teacher override, Diagnostic
  Trace, Development Panel, learner workspace, preview analytics, trace/audit endpoints, harness.
- Validation: Cases 1–4 pass; 10 middle-range samples pass (no false contradictions / invented
  weaknesses); stability 5/5; regression S1 11/11, S2 12/12, S3 16/16, P4 9/9.
- Performance (per learner turn, estimates): latency ~90s→~7.3s (~12x), LLM calls 3→2,
  prompt tokens ~19k→~1.7k (~91%↓), est. cost ~$0.10→~$0.005 (~95%↓).
- Files: `server.py` (DEFAULT_REASONING_MODE, RP5_MODES, default flip, `_finalize_structure_v5`),
  `compass_structure_engine.py` (V2 selector + minimal objects + dialogue + telemetry),
  `compass_foundation.py` (additive fields `developmental_variation`, `instructional_intent` + trace),
  `tests/sprint2_bridge_test.py` (pinned to `exhaustive`, its intended path).
- Reports: `/app/memory/DECISION_ENGINE_V2_Architecture_Analysis.md`,
  `DECISION_ENGINE_V2_Execution_Path.md`, `DECISION_ENGINE_V2_Validation_Closure.md`.

### NEXT PHASE: Instructional calibration (not architecture)
Goal: a better teacher, not a different architecture. First priority = investigate the
Central-Claim selection tendency (see `CALIBRATION_01_CentralClaim.md`).
