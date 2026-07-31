# Canonical Manual Test Path — how to run one end-to-end paragraph episode
Status: READY (2026-06). Isolated to a TEST session; default learner path unchanged; legacy retained.

## 1. URL to open
```
<PREVIEW_BASE>/?preview=writing&canon=1
```
- `?preview=writing` → genuine student Composition entry (paragraph development).
- `&canon=1` → creates the preview session with CANONICAL selection active
  (session `reasoning_mode = "canonical_v2"`, still routed through the structure engine).
- Without `&canon=1`, the preview uses the normal (legacy) selector — proves isolation.

## 2. Confirm CANONICAL_SELECTION is active
After you begin (any turn exists), open the read-only trace:
```
<PREVIEW_BASE>/api/sessions/<SESSION_ID>/canonical-trace
```
Look for `"canonical_active": true`, `"reasoning_mode": "canonical_v2"`, and per turn
`"canonical_selection": true`. (`SESSION_ID` is created when you click "Continue to Writing" →
submit your first paragraph; you can also read it from the network call to `/sessions/preview`.)

## 3. Fresh session / reset (no contamination)
- Each visit to `?preview=writing&canon=1` and clicking through Assignment → Writing creates a NEW
  session. To force a clean start: open the URL in a new tab, or clear the key
  `compass_student_session` in localStorage, then reload. Do not reuse an old `SESSION_ID`.

## 4/5. Selected structure + variation + sufficiency after each turn
All visible in the trace `turns[]`: `selected_structure`, `structure_status`,
`developmental_variation`, `developmental_sufficiency` (+ `sufficiency_reasoning`), `confidence`,
`next_objective`, and the full `provisional_judgment` (observed / hypothesized / unknown /
plausible_alternative / next_response_would_reveal / invitation_intent / integration_signal).
`current_state` shows the latest target, variation, and `current_target_attempts`.

## 6. Export / copy the full interaction + diagnostic trace
- Learner-facing conversation: `GET <BASE>/api/sessions/<SESSION_ID>/export?format=json` (or `markdown`).
- Diagnostic canonical trace: `GET <BASE>/api/sessions/<SESSION_ID>/canonical-trace` (copy the JSON).

## Expected trajectory (typical, NOT a fixed sequence)
weak paragraph → Thesis → Elaboration → Evidence / Example (if needed) → Conclusion → closure
(sufficiency=reached). Smoke-verified: T1 Thesis(Underdeveloped) → T2 Elaboration(Minimal) after the
thesis was integrated; strong paragraphs reach closure rather than an invented weakness.

## Scope / safety
- Only the five canonical primaries are selectable (Opening/Thesis/Elaboration/Evidence-Example/
  Conclusion). Explanation/Definition/Transition/Sentence/Qualification/Comparison/Analogy and
  Paragraph Main Point are NOT canonical primaries here and cannot override them.
- Flag OFF for all non-`canon` sessions; legacy selector retained; `COMPASS_REASONING_MODE=exhaustive`
  global rollback intact. No change to dialogue, Teacher Review, interim cards, UI visuals, DB
  schema, audit architecture, or OT. Frontend touch = one non-visual query-param passthrough.
