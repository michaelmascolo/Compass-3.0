# Phase II Canonical Baseline — MANIFEST (rollback point for Step 3)

Frozen: 2026-06-29. This is the permanent rollback point BEFORE any Stage B output-contract change.
Compass state: KB + deterministic hydrator + deterministic Orientation Plan + six-function
orientation validator + refined ready-made validator. Stage C render model = Sonnet 4.6.

## Version hashes (sha256, first 16 hex)
| Artifact | Hash | Size |
|---|---|---|
| server.SYSTEM_MESSAGE (Stage B reasoner) | `7ecc6056f891af30` | 77,871 chars |
| server.COACHING_RENDERER_SYSTEM (Stage C) | `52e0cce17ce8f70c` | 7,091 chars |
| server.NOTICING_SYSTEM_MESSAGE (acknowledgement) | `3f237b093e386697` | 2,848 chars |
| instructional_objects.json | `b9f9e2ba8ba1246d` | 381,884 bytes |
| developmental_exit_criteria.json | `5d8874b6a6791a3f` | 12,396 bytes |
| canonical_writing_model.json | `c01a78f7cb2b4358` | 84,237 bytes |
| ot_curriculum.json | `a3b1cbd69585b7d0` | 13,410 bytes |

## Benchmark corpus
`backend/test_cases/instructional_test_cases.json` — 66 cases (levels, purposes, expected targets).

## Preserved outputs (to be captured by `tests/stage_b_baseline.py capture`)
- `phase2_baseline/stage_b_baseline.json` — per-case instructional JUDGMENT (object, bottleneck,
  evidence, strategy, dependency, sequence, exit, next) + rendered coaching.
- Representative coaching examples: Step-4b A/B report (`test_reports/stage_c_model_ab_report.md`)
  + `/tmp/ab_results.json` (Sonnet renders on 5 drafts).
- Representative Teacher Review: derived deterministically from the theory via `_curate_case`
  (see `test_reports/kb_instructional_completeness_audit.md` + live checks in PRD).

## How to certify a Stage B change (Phase D)
1. `python3 tests/stage_b_baseline.py capture /tmp/candidate.json`
2. `python3 tests/stage_b_baseline.py compare phase2_baseline/stage_b_baseline.json /tmp/candidate.json`
3. Require judgment equivalence (object / dependency / exit exact; sequence / sufficiency soft) at
   the agreed threshold. Roll back on regression. (Exit is hydrated → must be identical.)

## Rollback
Restore this repository state (before the Stage B output-contract edits). No KB/prompt hash above
should change during Group 1+2 migration except the SYSTEM_MESSAGE (which drops deterministic
OUTPUT fields only — reasoning guidance unchanged).
