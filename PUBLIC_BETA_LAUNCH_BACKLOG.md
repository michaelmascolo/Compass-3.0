# Public Beta — Launch Backlog

> Repairs derived from `PUBLIC_BETA_STUDENT_EXPERIENCE_AUDIT.md`. **The frozen engine, prompts, evaluator, instructional objects/network, assignment-representation engine, and test harness are OUT OF SCOPE — nothing here touches them.** Effort scale: XS (very small) · S (small) · M (medium) · L (large).

## A. Beta Launch Blockers
*Only issues that prevent a smooth, credible public demonstration.*

### A1 — Beta feedback capture (form + endpoint + storage + confirmation)
- **Scope:** A "Share beta feedback" form reachable at completion (and from a persistent link). Fields: What was helpful? · What was confusing/frustrating? · Would you use this with students? (yes/maybe/no) · optional role/context · optional email. Account-free. New `POST /api/beta-feedback` persisting to a new `beta_feedback` collection (with session id + timestamp + user agent); visible success confirmation on submit.
- **Files:** `PublicPreview.jsx` (or new `BetaFeedback.jsx`), `lib/api.js` (add `submitBetaFeedback`), `backend/server.py` (new endpoint + Pydantic model + collection).
- **Acceptance:** A visitor submits feedback without an account; a confirmation appears; the record is retrievable via a simple query/endpoint (e.g. `GET /api/beta-feedback` dev-only).
- **Effort:** M · **Dependencies:** none (F5 completion flow is a natural host but not required).

### A2 — Beta identity + privacy/PII notice + data-use statement
- **Scope:** A visible "Beta" marker on the public entry and workspace; a short notice on the seed screen: "Please don't enter real or confidential student information." One-line statement of how feedback/optional email are used, shown near the feedback form.
- **Files:** `Landing.jsx`, `PublicPreview.jsx` (SeedScreen + header), feedback component.
- **Acceptance:** "Beta" is visible on arrival and in the workspace; the PII notice is visible before writing; the data-use line is visible at the feedback step.
- **Effort:** S · **Dependencies:** A1 (for the data-use line placement).

### A3 — Preview session persistence & recovery on reload
- **Scope:** Persist the preview session id to `localStorage` on start; on load, rehydrate via `GET /sessions/{id}` (restore draft from the latest student turn); clear it when the visitor finishes/starts over.
- **Files:** `PublicPreview.jsx`. **Backend:** none (uses existing `GET /sessions/{id}`).
- **Acceptance:** Beginning a preview, reloading, and returning restores the passage and coaching state; finishing/reset clears it. Satisfies Scenario 2.
- **Effort:** S · **Dependencies:** none.

### A4 — Friendly error handling in preview
- **Scope:** Replace the empty `catch` blocks with user-facing messages (toast or inline) for start/interact/reply/revision failures; keep the writing intact; offer "try again."
- **Files:** `PublicPreview.jsx` (add `sonner` `Toaster` as in `App.js`).
- **Acceptance:** A simulated failed response shows a plain-language message and preserves the draft; retry works. Satisfies items 42/43.
- **Effort:** XS · **Dependencies:** none.

### A5 — Deliberate completion → closing summary → feedback flow
- **Scope:** Add an always-available "Finish" affordance in the workspace; on finish, show a brief neutral closing screen ("What Compass was doing differently: it developed you as the writer and never wrote for you") that leads into the A1 feedback form. Keep the existing bridge CTA as an optional secondary action.
- **Files:** `PublicPreview.jsx`, reuse/adapt `PreviewBridge.jsx`, feedback component.
- **Acceptance:** A visitor can end intentionally at any point, sees the closing summary, and reaches feedback. Satisfies items 31–33.
- **Effort:** M · **Dependencies:** A1.

### A6 — Provided starter activity (remove entry friction)
- **Scope:** Offer 1–2 one-click provided sample passages (with topic pre-filled) alongside "write your own." Selecting one fills the seed and begins.
- **Files:** `PublicPreview.jsx SeedScreen` (static sample text; no backend).
- **Acceptance:** A visitor can start a meaningful interaction in one click without composing anything. Satisfies item 5 and the Scenario-1 fastest path.
- **Effort:** S · **Dependencies:** none.

## B. Strongly Preferred
*Materially strengthen the experience; do not block launch.*

- **B1 — Auto-open the coach card for a new target** (items 11, 23). Remove the marker-click step so the ask is immediately visible. *Files:* `PublicPreview.jsx`. *Acceptance:* a new coaching turn shows its card without a click. *Effort:* XS.
- **B2 — Clearer separation of coach question vs next action** (item 23). Visually distinguish the invitation from the "revise and send" instruction. *Files:* `PublicPreview.jsx`. *Effort:* XS.
- **B3 — View earlier versions** (item 30). A simple "previous versions" affordance reading `sessions.turns`. *Files:* `PublicPreview.jsx`. *Effort:* S.
- **B4 — Accessibility pass** (item 47). Label the document textarea, raise helper-text contrast, ensure keyboard access + focus rings on all controls. *Files:* `PublicPreview.jsx`, `Landing.jsx`. *Effort:* S.
- **B5 — Responsive check at tablet/small-laptop widths** (item 46). Verify and adjust the `max-w-2xl` column + action bar. *Files:* `PublicPreview.jsx`. *Effort:* XS–S.
- **B6 — Guard very long pasted text** (Scenario 3). Soft client-side length cap + friendly note. *Files:* `PublicPreview.jsx`. *Effort:* XS.
- **B7 — Canonical public link + "what is this" framing on `?preview`** (item 2). Decide whether CGI links to `/` or `/?preview`; ensure the value prop + beta line appears wherever they land. *Files:* `Landing.jsx`, `PublicPreview.jsx`. *Effort:* XS.
- **B8 — Optional own-prompt field** (item 6). A distinct "paste your assignment/prompt" input feeding session context. *Files:* `PublicPreview.jsx`. *Effort:* S. *Dependency:* confirm it maps to existing preview session context only (no engine change).

## C. Post-Beta
*Not needed for this public demonstration.*

- **C1 — Teacher authentication / accounts** (no auth exists today). *Effort:* L.
- **C2 — Class creation + roster + student join UI** (`assignments/{code}/start` exists; no UI). *Effort:* L.
- **C3 — Teacher dashboard + revision analytics** (data exists in `sessions`; no UI). *Effort:* L.
- **C4 — Assignment Representation (Question/Knowledge loops) as a public path** — powerful but heavier; keep out of the first public beta. *Effort:* M–L.
- **C5 — Admin UI for reviewing `beta_feedback`** (beyond a dev-only fetch). *Effort:* S–M.
- **C6 — Hide/guard half-built `?app` / `?teacher` / `?config` routes from public entry** (item 41 hardening). *Effort:* S.
- **C7 — Persisted end-of-session recap artifact** (from the Session Model backlog). *Effort:* M.
