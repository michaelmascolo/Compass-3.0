# Experience Compass — Build Slice 1 Validation Report
**One Objective → Learner Revision → Reflection → Deliberate Stop** · 2026-07-26

## Files changed
| File | Change |
|---|---|
| `backend/server.py` | Added `ExperienceControl` + `ExperienceReflection` models; `Session.experience_control` field; `create_preview_session` initializes `ExperienceControl()`; helpers `_experience_objective_id`, `_experience_reader_effect`, `_build_experience_reflection`, `_update_experience_control`; hook into `_finalize_turn`; persist in `_run_reasoning` `$set`; 409 guard in `interact`. |
| `frontend/src/components/ExperienceReflection.jsx` | **New.** Four-section reflection + read-only passage + sole "Try another paragraph" action. |
| `frontend/src/components/PublicPreview.jsx` | Completion now driven only by `experience_control.phase`; removed turn-count `canBridge` and `PreviewBridge`; reflection branch hides editing controls; `restart()` starts a fresh session. |
| `backend/tests/test_experience_control_unit.py` | **New.** 7 offline state-machine tests. |
| `backend/tests/test_experience_control_api.py`, `test_experience_control_live.py` | **New** (testing agent). API + live-lock tests. |

## Summary of each change
- **Single locked objective** — locked on the first completed AI turn from `instructional_reasoning.active_instructional_element`; never changes afterward.
- **Support cap = 3** — three `answer`/`explain` exchanges without a substantive revision → deliberate stop into reflection; a substantive revision resets the counter; an unresolved substantive revision returns to teaching.
- **Completion rule** — resolved when `revision_development.development_detected` starts with "yes" OR `scaffolding_control.cycle_status` ∈ {`consolidate_and_return`, `stop`}. No new evaluator; existing engine only.
- **Reflection (exactly 4 sections)** — (1) The one thing you worked on, (2) How your writing changed (evidence-only; support-cap case never claims mastery), (3) Why it helps your reader (communicative function from `_IO_BY_NAME`, string fallback), (4) Carry it forward (transfer).
- **Deliberate stop** — `interact` returns HTTP 409 once phase is `reflection`.
- **Frontend** — phase-driven completion; editing controls disappear during reflection; passage stays visible; "Try another paragraph" begins a **completely new** preview session; `PreviewBridge` removed from the preview.

## Backend test results
- `test_experience_control_unit.py` — **7/7 PASS** (lock-once, support-cap→reflection, resolved-via-"yes", resolved-via-cycle_status, unresolved-revision-stays-active, support-counter-resets, non-preview-untouched).
- `test_experience_control_api.py` — **3/3 PASS** (preview initializes `experience_control`; non-preview session has `experience_control=null`; **409** after phase=reflection).
- `test_experience_control_live.py` — **PASS** (live engine ~60s: objective locked = "Thesis"; phase stays `active` after first turn).

## Frontend test results (testing agent iteration_33)
- Seed screen + begin flow: **PASS**.
- Completion controlled only by `experience_control.phase`, never turn count: **PASS**.
- `preview-bring-own-work` / PreviewBridge absent from preview: **PASS** (0 elements).
- `ExperienceReflection` shape (4 sections, `reflection-passage`, `reflection-try-another`): **VERIFIED** (component code + testids).

## Failures encountered / fixes applied
- None. Zero critical or minor issues reported by the testing agent.

## Confirmations
- ✅ The frozen developmental engine (`SYSTEM_MESSAGE`, reasoning architecture, M1–M14) was **NOT** modified.
- ✅ Instructional-object data (`instructional_objects.json`) was **NOT** modified.
- ✅ Canonical writing knowledge (`canonical_writing_model.json`) was **NOT** modified.
- ✅ Anti-coauthoring behavior remains unchanged (no new evaluator, no content generation).
- ✅ Experience Compass now completes exactly **one developmental cycle**: one objective → learner revision → reflection → deliberate stop.

## Note
The 3-support-turn reflection path was validated by the offline unit test (deterministic) rather than a live 3–6 minute LLM drive, to conserve engine time. The live path exercised the first-turn objective lock; the transition logic that follows is identical code covered by the unit suite.
