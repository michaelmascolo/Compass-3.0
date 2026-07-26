# Experience Compass — Pre-Slice 2 Cleanup Validation Report
**Scope: semantic consistency + obsolete Slice 1 code only. No Slice 2 features. Frozen engine untouched.** · 2026-07-26

## Files changed
| File | Change |
|---|---|
| `backend/server.py` | (1) Removed phantom `"complete"` phase from the `interact` guard → now `phase == "reflection"` only. (2) Retired legacy `soft_cap_reached` (6-exchange) analytics; replaced with accurate `support_cap` / `support_count` / `support_cap_reached` sourced from `experience_control`. (3) Deleted dead `PREVIEW_FIXED_SELECTIONS` / `PREVIEW_FIXED_IO` + their R1 comment. (4) Removed redundant `ExperienceReflection.resolved`; documented `ExperienceControl.phase` as sole terminal authority and `.resolved` as authoritative flow flag. (5) Reflection fallback wording: humanized element names + 2–3 deterministic per-session variants; prefer engine `communication_change` / `primary_growth` / `transfer_message` when present. |
| `frontend/src/components/PreviewBridge.jsx` | Added a retention comment (retained for Slice 2 "Bring your own writing"; intentionally unlinked). No logic change. |
| `backend/tests/test_experience_control_unit.py` | Updated for removed `resolved` field and the new non-mastery wording assertions (variant-tolerant). |

## Dead code removed
- `PREVIEW_FIXED_SELECTIONS`, `PREVIEW_FIXED_IO` (unreferenced leftovers of the reverted R1 optimization) + their comment block.
- Phantom `"complete"` phase string in the `interact` guard (never set anywhere).
- Legacy `preview_analytics.soft_cap_reached = exchange_count >= 6` (contradicted the real cap; never governed flow).
- `ExperienceReflection.resolved` (redundant with `completion_reason == "resolved"`; unused by the UI).

## Terminal-state semantics
- **`ExperienceControl.phase` is the single source of truth.** `phase == "reflection"` is the **sole** completed/terminal condition — documented in the model docstring.
- No separate `complete` state, screen, or transition exists or is implied anywhere (code, tests, comments).
- `interact` continues to reject requests with **HTTP 409** once `phase == "reflection"`.
- "Try another paragraph" still creates a **completely new** preview session (client-side `restart()` → fresh `POST /api/sessions/preview`); the old session remains in `phase="reflection"`.

## Support-cap discrepancy resolution
- **Flow** is governed exclusively by `ExperienceControl.support_cap = 3` (unchanged).
- **Analytics** now records the real cap: `support_cap` (3), `support_count`, and `support_cap_reached` (true only when the reflection's `completion_reason == "support_cap"`). The 6-based `soft_cap_reached` is gone; no legacy value can influence Experience Compass flow. No separate non-preview workflow depended on the old field.

## Reflection wording changes (four-section structure preserved)
- Sections 2 & 4 **prefer engine-authored text** (`communication_change`/`primary_growth`, `transfer_message`) when available; otherwise use humanized fallbacks.
- Fallbacks now use a plain-language element name (`_humanize_element`, e.g. "Central Claim / Thesis" → "central claim") — no raw/clinical/internal terminology exposed. The product never selects or reinterprets the objective.
- **2–3 deterministic variants** per fallback (`_reflection_variant`, stable per session, varied across sessions) remove repetitive/mechanical phrasing on repeat cycles. No randomness, **no added LLM call**.
- Support-cap wording still clearly states the learner explored the objective but **did not yet revise** — never claims mastery (asserted by the unit test).

## Completion-state redundancy
- Authoritative fields documented: `ExperienceControl.phase` (terminal decisions), `ExperienceControl.resolved` (flow-layer resolution flag), `ExperienceReflection.completion_reason` (explanatory metadata: `resolved` | `support_cap`).
- Removed only the demonstrably redundant, unused `ExperienceReflection.resolved`. No broad schema refactor; no field combined for elegance. Removal is migration-safe (Pydantic ignores the stale key on any previously-stored doc).

## Test results
- **Backend unit** `test_experience_control_unit.py` — **7/7 PASS** (reflection is the only terminal phase; no code expects `"complete"`; support cap stays 3; objective-lock unchanged; canonical resolution rule unchanged; resolved→reflection; support-cap→non-mastery reflection; non-preview untouched; support counter resets).
- **Backend API** `test_experience_control_api.py` — **3/3 PASS** (preview initializes `experience_control`; non-preview `experience_control=null`; **409** after `phase=reflection`).
- **Manual** — preview init payload has no `soft_cap`; forcing `phase=reflection` then `interact` → **HTTP 409**; `grep` confirms `PREVIEW_FIXED*` and `soft_cap_reached` fully removed (only unrelated `Turn.status="complete"` remain).
- **Frontend** — compiles and renders (`?preview` seed screen present); `preview-bring-own-work` absent; completion driven only by `experience_control.phase` (no turn-count dependency, no `complete` phase reference); PreviewBridge not imported in the preview flow; 4 reflection section testids + `reflection-passage` + `reflection-try-another` present. (No frontend logic changed this pass — only a comment in the unlinked PreviewBridge — so the iteration_33 frontend verification remains valid.)

## Confirmations
- ✅ **No Slice 2 features added.** No experience redesign.
- ✅ Frozen developmental engine (`SYSTEM_MESSAGE`, reasoning, target selection, revision evaluator) **untouched**.
- ✅ `instructional_objects.json` and `canonical_writing_model.json` **untouched**.
- ✅ Anti-coauthoring logic **unchanged** (no new evaluator, no content generation, no LLM call added).
- ✅ Stage-A selection behavior **unchanged**.
- ✅ Experience Compass still completes exactly one cycle: one objective → learner revision → reflection → deliberate stop.

**Stopping here per instruction. Slice 2 not started.**
