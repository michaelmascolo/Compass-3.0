# Public Beta — Student Experience Audit

> **Scope:** audit the public-facing student experience surrounding the FROZEN engine + Knowledge Base v1.0, for a public beta linkable from the Common Ground Institute site. **No code was changed.** Assessed by reading the implementation and running the live UI (`/` and `/?preview`); the developmental interaction itself is engine-driven (~75s/turn) and already verified by the 66-case suite, so items 15–20/28–29 are assessed from the frozen engine + component structure rather than re-graded here.

## Components & endpoints in scope
- **Frontend:** `Landing.jsx` (`/`), `PublicPreview.jsx` (`?preview`), `PreviewBridge.jsx` (`?bridge` / reached from preview), `StudentWorkspace.jsx` + `App.js StudioApp` (`?app`), `lib/api.js`.
- **Backend:** `POST /api/sessions/preview`, `POST /api/sessions/{id}/interact` (409 double-submit guard), `GET /api/sessions/{id}`, `POST /api/sessions/{id}/preview-continue`, `GET /api/sessions/{id}/preview-analytics`.
- **DB:** `sessions` (`is_preview`, `preview_analytics`, `turns[]`). **No feedback collection exists.**

## Executive summary
The **core coaching moment is strong and credible**: the `?preview` experience is a document-centered workspace (not a chatbot), the writing stays visible and editable, revisions are deliberate (`Send revision`), and the frozen engine delivers one concise, jargon-free, non-co-authoring invitation at a time. Landing communicates the differentiator well ("It never writes a word for them").

However, the experience is **not yet a public beta**. Four things are missing or broken that block a credible public launch:
1. **No feedback capture at all** (the primary purpose of a beta) — no UI, no endpoint, no storage.
2. **No beta identity and no privacy/PII notice** — required for an education-facing public page.
3. **Preview session is lost on reload** — the id lives only in React state (never `localStorage`), so a refresh drops the visitor back to the start screen; Scenario 2's "reload and continue" fails.
4. **Preview errors fail silently** — all `catch` blocks are empty, so a failed start/response leaves the visitor stuck with no message.

Secondary gaps: no "provided activity" quick-start (entry asks the visitor to invent a Grade-9 passage), no deliberate "end the demo → closing summary → feedback" flow (the only exit is a marketing "continue with a real assignment" CTA), no UI to view earlier versions, and partial accessibility.

**The engine is sound; the beta shell around it is incomplete.** The build required is small, additive, and does not touch the frozen system.

## The 47-item audit

### A. Arrival
| # | Item | Status | Detail (if not COMPLETE) |
|---|---|---|---|
| 1 | Reaches a public Compass page | **COMPLETE** | `Landing.jsx` at `/`. |
| 2 | Immediately understands what / what they'll do / won't write for them / it's a beta | **PARTIAL** | Landing conveys "what" + "never writes for them" well, but **nothing anywhere says "beta"**. If CGI links directly to `?preview`, the seed screen lacks the value prop entirely. *File:* `Landing.jsx`, `PublicPreview.jsx SeedScreen`. *Fix:* add a beta line; decide the canonical link target. *Beta Launch.* |
| 3 | One visually dominant "begin" action | **COMPLETE** | Landing "Try the Preview" is primary; a secondary "Understand an assignment" slightly competes (minor). |

### B. Entry
| # | Item | Status | Detail |
|---|---|---|---|
| 4 | Begin with no account / class / code / jargon / long instructions | **COMPLETE** | `?preview` requires none. |
| 5 | Choice: short provided activity **or** paste own prompt | **MISSING** | Preview offers only "write/paste your own passage." No provided starter activity and no distinct prompt field. *File:* `PublicPreview.jsx SeedScreen`. *Fix:* add 1–2 provided sample passages as one-click starters. *Beta Launch.* |
| 6 | Optionally paste existing writing | **PARTIAL** | You paste a passage as the seed (≈ existing writing), but it's framed as "role-play a Grade-9 passage," not "paste your own." No separate prompt+writing. *File:* `PublicPreview.jsx`. *Strongly Preferred.* |
| 7 | Fastest path ≤ 1–2 decisions | **COMPLETE** | Type a passage → Try Compass; the two selects are optional. |

### C. Writing workspace
| # | Item | Status | Detail |
|---|---|---|---|
| 8 | Writing area is the visual center | **COMPLETE** | Document textarea is the centerpiece. |
| 9 | Full current writing visible & editable | **COMPLETE** | `preview-document` holds the full draft, editable in place. |
| 10 | Not a vertical chatbot | **COMPLETE** | Document canvas + a single anchored coach card. |
| 11 | User always knows where to write / what Compass asks / how to submit | **PARTIAL** | The coach's ask is hidden behind a marker dot that must be clicked to open the card; before opening, the question isn't visible. *File:* `PublicPreview.jsx` (marker → `openCoachingId`). *Fix:* auto-open the card for a new target. *Strongly Preferred.* |
| 12 | Text stays inside the writing area | **COMPLETE** | Reply box is separate and does not alter the draft. |
| 13 | Writing preserved while interacting | **COMPLETE** | Draft held in local state across coach turns. |
| 14 | Reload doesn't destroy the session | **BROKEN** (preview) | Preview stores the session id only in React state — never `localStorage`. A refresh returns to the seed screen and the session is unreachable (though it exists in the DB). *File:* `PublicPreview.jsx`. *Backend:* `GET /sessions/{id}` (works). *Fix:* persist preview id to `localStorage` + rehydrate on load. *Beta Launch.* (`?app` already persists via `dws_session_id` — COMPLETE there.) |

### D. Developmental interaction (frozen engine)
| # | Item | Status | Detail |
|---|---|---|---|
| 15 | Responds to the user's actual writing | **COMPLETE** | Engine reasons on the submitted draft. |
| 16 | One high-leverage target at a time | **COMPLETE** | M11 controller; verified by suite. |
| 17 | Explains unfamiliar concepts before applying | **COMPLETE** | Governed canonical instruction. |
| 18 | Asks the user to perform the thinking/writing | **COMPLETE** | Invitation requires one student act. |
| 19 | Does not provide the substantive answer | **COMPLETE** | Anti-coauthoring boundary (foothold caveat logged separately). |
| 20 | Does not rewrite the target passage | **COMPLETE** | M5A boundary. |
| 21 | Responses concise enough for a first-time public user | **PARTIAL** | `PREVIEW_OUTPUT_OVERRIDE` slims output, but invitations can still run long for a cold visitor. *File:* engine (frozen) — do **not** change; mitigate in UI presentation only. *Strongly Preferred.* |
| 22 | Understandable without framework jargon | **COMPLETE** | Preview override strips internal terminology. |
| 23 | Distinguish coach's explanation/question vs the user's writing vs the next action | **PARTIAL** | Card shows invitation + "Revise your passage above, then send it back," but explanation and question are one block and the marker step adds friction. *File:* `PublicPreview.jsx`. *Strongly Preferred.* |

### E. Revision loop
| # | Item | Status | Detail |
|---|---|---|---|
| 24 | Revise directly in the workspace | **COMPLETE** | Edit the document textarea. |
| 25 | Autosave does not trigger an AI response | **COMPLETE** | Only `Send revision` calls `interact`; a `dirty` guard blocks no-op sends. |
| 26 | Clear deliberate "Submit Revision" button | **COMPLETE** | `preview-send-revision` ("Send revision"). |
| 27 | Analyzes the latest revision | **COMPLETE** | Sends the current draft as `kind:"revise"`. |
| 28 | Recognizes meaningful improvement | **COMPLETE** | Engine. |
| 29 | Consolidates or selects one next move | **COMPLETE** | Engine. |
| 30 | Earlier versions preserved / recoverable | **PARTIAL** | Every submitted draft is stored in `sessions.turns`, but there is **no UI to view/restore** prior versions; the textarea overwrites. *File:* `PublicPreview.jsx`. *Strongly Preferred / Later.* |

### F. Completion & beta feedback
| # | Item | Status | Detail |
|---|---|---|---|
| 31 | End the demonstration intentionally | **PARTIAL** | The only exit is a small header link "Bring your own writing →" → `PreviewBridge`, a marketing "continue with a real assignment" CTA — not a neutral "I'm done." *File:* `PublicPreview.jsx`, `PreviewBridge.jsx`. *Beta Launch.* |
| 32 | Closing screen explains what Compass did differently | **PARTIAL** | `PreviewBridge` says "You just taught yourself… no one wrote it for you" (good differentiator) but is a conversion screen, not a neutral closing summary, and is only reachable via the small link. *Beta Launch.* |
| 33 | Invited to provide feedback | **MISSING** | No feedback affordance anywhere. *Beta Launch.* |
| 34 | Feedback fields (helpful / confusing / use-with-students / role / email) | **MISSING** | No form. *Beta Launch.* |
| 35 | Feedback without creating an account | **MISSING** (feature absent) | To be built account-free. *Beta Launch.* |
| 36 | Told how comments / contact info will be used | **MISSING** | No notice. *Beta Launch.* |
| 37 | Visible success confirmation | **MISSING** | No submit flow. *Beta Launch.* |
| 38 | Feedback stored retrievably | **MISSING** | No endpoint, no `feedback` collection (the only `feedback*` in code is teacher-config instructional priorities). *Backend:* new `POST /api/beta-feedback`. *DB:* new `beta_feedback` collection. *Beta Launch.* |

### G. Public-beta safety & clarity
| # | Item | Status | Detail |
|---|---|---|---|
| 39 | Page identifies the experience as a beta | **MISSING** | No "beta" label on Landing or preview. *Beta Launch.* |
| 40 | Told not to enter confidential / student PII | **MISSING** | No privacy notice. *File:* `PublicPreview.jsx SeedScreen`. *Beta Launch.* |
| 41 | Doesn't imply a complete classroom-management system | **COMPLETE** | Preview makes no management claim. (Note: `?app`/`?teacher`/`?config` are reachable and half-built — should not be linked publicly.) |
| 42 | Error messages written for ordinary users | **BROKEN** (preview) | Every `catch` in `PublicPreview.jsx` is empty — start/response failures produce **no message**; the button just stops spinning. (`?app` has `sonner` toasts.) *Fix:* add friendly error toast/inline message. *Beta Launch.* |
| 43 | Failed AI doesn't erase the visitor's writing | **COMPLETE** | Draft is in local state and survives a failed call (but with no notification — see #42). |
| 44 | Loading states clearly indicate Compass is responding | **COMPLETE** | `Thinking` component + "Reading…" button state. |
| 45 | Can't accidentally submit repeatedly while processing | **COMPLETE** | Buttons disabled on `busy`; backend returns **409** if a turn is already processing. |
| 46 | Works at desktop & tablet widths | **PARTIAL** | `max-w-2xl` centered column reads well on desktop/tablet; not verified on narrow tablet portrait / small laptops. *Strongly Preferred.* |
| 47 | Basic accessibility (text size, contrast, keyboard, focus, labels) | **PARTIAL** | Some focus rings (Landing/Bridge) and a few `aria-label`s, but the document textarea has no label, low-contrast `stone-400` helper text, and the marker-gated card is awkward for keyboard/screen-reader users. *File:* `PublicPreview.jsx`. *Strongly Preferred.* |

**Tally:** COMPLETE 24 · PARTIAL 12 · BROKEN 2 (#14, #42) · MISSING 8 (#5, #33–#38-ish, #39, #40) · N/A 0.

## Real-use scenario results

> The live seed screen was captured and verified. Full multi-turn coaching was assessed from the frozen engine + component code (each engine turn is ~75s; behavior is already suite-verified). Findings below combine the live UI with code inspection.

**Scenario 1 — Provided activity.** *Partially blocked.* There is **no provided activity** (item 5) — the visitor must invent a Grade-9 passage. Once a passage is entered, begin → coach invitation → edit in place → `Send revision` works as designed. **Feedback submission is impossible** (items 33–38 missing). Net: the core loop works; entry friction + no feedback.

**Scenario 2 — Own prompt + existing writing, reload, continue.** *Blocked at reload.* The visitor can paste a passage (≈ existing writing) but there is **no separate prompt field** (items 5/6). After beginning, **reloading the page loses the session** (item 14 BROKEN — id never stored). Continuing after reload is therefore impossible in the preview. Feedback also missing.

**Scenario 3 — Failure & recovery.**
- Delayed response: **handled** — `Thinking` + polling every 1.5s; durable background reasoning.
- Failed response: **writing preserved (good) but silent (bad)** — empty `catch`; no user message (item 42).
- Repeated click: **handled** — button disabled on `busy` + backend 409 (item 45).
- Reload during processing: **BROKEN in preview** — session id lost (item 14); (`?app` recovers via `localStorage`).
- Empty submission: **handled** — begin/send buttons disabled while empty/not-dirty.
- Very long pasted text: **no explicit guard** — textarea accepts unbounded text; no client length cap or friendly warning (note; likely low risk but unhandled).

## Five largest obstacles to a successful public beta
1. **No feedback capture (items 33–38).** A beta with no way to collect feedback cannot meet its own purpose. Needs a form + `POST /api/beta-feedback` + `beta_feedback` collection + confirmation.
2. **No beta identity + no PII/privacy notice (items 39, 40).** An education-facing public page must say "beta" and "don't enter real student information," with a one-line data-use statement.
3. **Preview session lost on reload (item 14, Scenario 2).** One line of `localStorage` + rehydrate; the DB already persists the session.
4. **Silent error handling in preview (item 42).** Empty `catch` blocks must surface a friendly message so failures aren't dead ends.
5. **No deliberate completion → closing summary → feedback flow (items 31–32).** Replace/extend the conversion-only bridge with an explicit "Finish" that shows a short "what Compass was doing differently" summary and the feedback form. (Plus: add a provided starter activity, item 5, to remove entry friction.)
