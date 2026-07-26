# Public Beta — Minimum Build Plan

> The smallest coherent batch that turns the existing `?preview` experience into a credible public beta. **Additive UI + one small backend endpoint only. The engine, prompts, evaluator, instructional objects/network, assignment-representation engine, and test harness are untouched.** No redesign, no speculative features, no teacher workflow.

## Design principle
The coaching moment already works. We are wrapping it with the missing beta shell: **immediate entry → persistent visible writing → clear revision → concise interaction → session recovery → easy feedback → beta/privacy notice → graceful errors.** Every task is small and independent enough to ship within 1–2 weeks.

## Recommended batch (in build order)

**Step 1 — Safety shell (A2, A4).** `Effort S+XS`
Add the "Beta" marker, the "don't enter real student information" notice, and a one-line data-use statement; wire `sonner` into `PublicPreview` and replace empty `catch` blocks with friendly messages that preserve the draft.
- *Covers:* beta privacy notice, graceful error handling. *Files:* `PublicPreview.jsx`, `Landing.jsx`.
- *Why first:* pure additive safety; unblocks a public link immediately and de-risks everything after.

**Step 2 — Session recovery (A3).** `Effort S`
Persist the preview session id to `localStorage`; rehydrate draft + coaching from `GET /sessions/{id}` on load; clear on finish/reset.
- *Covers:* session recovery; fixes Scenario 2 and item 14.
- *Files:* `PublicPreview.jsx`. *Backend:* none.

**Step 3 — Entry & clarity (A6, B1, B7).** `Effort S+XS`
Add 1–2 one-click provided starter passages next to "write your own"; auto-open the coach card for a new target; ensure the value-prop + beta line shows wherever CGI links (decide `/` vs `?preview`).
- *Covers:* immediate entry, "understand in ~20s / begin in ~30–60s," persistent visible writing (already fine), clearer interaction.
- *Files:* `PublicPreview.jsx SeedScreen`, `Landing.jsx`.

**Step 4 — Feedback capture (A1).** `Effort M`
New `beta_feedback` Pydantic model + collection; `POST /api/beta-feedback` (account-free; stores answers + optional role/email + session id + timestamp); `submitBetaFeedback` in `api.js`; a feedback form component with visible success confirmation; dev-only `GET /api/beta-feedback` to review responses.
- *Covers:* easy feedback collection, retrievable storage, confirmation.
- *Files:* `backend/server.py`, `lib/api.js`, `PublicPreview.jsx` / new `BetaFeedback.jsx`.

**Step 5 — Completion flow (A5).** `Effort M`
Add an always-available "Finish" control; on finish show a brief neutral "what Compass was doing differently" summary that leads into the Step-4 feedback form; keep the existing bridge CTA as a secondary option.
- *Covers:* intentional completion, closing explanation → feedback (items 31–33).
- *Files:* `PublicPreview.jsx`, adapt `PreviewBridge.jsx`, feedback component.
- *Dependency:* Step 4.

## What this batch delivers against the Beta Success Standard
1. Understand Compass in ~20s → Steps 1/3 (framing + beta line).
2. Begin in ~30–60s → Step 3 (one-click starter, no account).
3. Meaningful interaction in 5–10 min → already works (frozen engine); unchanged.
4. Revise without losing the writing → already works; hardened by Steps 1–2.
5. Understand Compass develops the writer → Step 5 closing summary (+ existing Landing/bridge copy).
6. Submit useful feedback easily → Steps 4–5.

## Explicitly deferred (not in this batch)
- Auth, classes, student join, teacher dashboard, analytics (Post-Beta C1–C3).
- Assignment Representation as a public path (C4).
- Earlier-version viewer (B3), full accessibility/responsive pass (B4–B6), own-prompt field (B8) — Strongly Preferred, ship if time remains but not required for launch.

## Sequencing & effort
- **Critical path:** Step 1 → Step 2 → Step 3 (independent) → Step 4 → Step 5.
- **Total effort:** ~1 M (feedback) + 1 M (completion) + 3 S + 2 XS ≈ a **single ~1-week implementation batch** for one developer, with Strongly-Preferred polish in a second few days.
- **Only backend change:** one additive `beta_feedback` endpoint + collection. No change to any frozen component.

## Guardrails for implementation (when approved)
- Do not modify `SYSTEM_MESSAGE`, reasoning architecture, instructional selection, instructional objects, instructional network, anti-coauthoring rules, the assignment-representation engine, the evaluator, or the test harness.
- Do not link the half-built `?app` / `?teacher` / `?config` routes from the public beta (optionally hard-guard them — C6).
- Additive only; preserve all existing `data-testid`s and add new ones for every new control.

---
**Status:** audit + backlog + plan complete. **Awaiting review before any implementation.**
