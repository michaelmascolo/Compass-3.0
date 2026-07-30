# Sprint 1 — Closure Report: Instructional State, Evidence & Audit Foundation

**Date:** 2026-07-30 · **Status:** ALL TESTS A–G PASS → **CERTIFIED (FROZEN)**
**Governing sources:** Compass Operational Specification v0.9 + Architecture Audit & Implementation
Package v0.95. *These documents were NOT present in the workspace* (only the logo + Writing Elements
Chart are attached). Implemented strictly to the self-contained Sprint 1 brief; the requirement IDs
(VA-05, DS-01, DS-02, TC-01, VA-06, VA-07) come from that brief. If the specs contain additional
requirement IDs or field names, they can be layered onto this foundation without rework.

---

## 1. Files & components changed
**New (additive, isolated):**
- `backend/compass_foundation.py` — the entire foundation: models, persistence, six validation guards,
  append-only audit, migration, and the FastAPI router (`/api/instructional-state/*`,
  `/api/admin/foundation/migrate`). Uses its own Mongo handle from `MONGO_URL`/`DB_NAME`.
- `frontend/src/components/DiagnosticTrace.jsx` — minimal read-only diagnostic trace panel.
- `backend/tests/sprint1_foundation_tests.py` — the A–G acceptance suite (also covers DS-02, the auth
  gate, the happy-path advance, and append-only correction).

**Edited (2 additive lines each, no behavior change to existing features):**
- `backend/server.py` — `import compass_foundation` + `app.include_router(_foundation.foundation_router)`.
- `frontend/src/App.js` — `import DiagnosticTrace` + a `?trace=<state_id>` route branch.

**Explicitly NOT touched:** the frozen Stage B/C instructional engine, the CIO/dialogue logic, Organizing
Thought, teacher configs, sessions, or any existing route. Verified: Stage B `SYSTEM_MESSAGE` hash is
still `1c485e2c13d7b8ff` (frozen) after the sprint.

---

## 2. Database / schema changes
Three NEW collections (no changes to existing collections):
- `instructional_states` — one persistent, versioned state per (student, assignment). Distinguishes
  epistemic status via separate lists: `observed_strengths` / `observed_evidence` (OBSERVED),
  `provisional_hypotheses` (HYPOTHESIZED), `unknowns` (UNKNOWN). Stores identity, assignment framing,
  student text + revision history, current instructional object (nullable), dialogue state, scaffolding
  (support) level, exit-criterion status, teacher constraints/overrides, advancement decision, and
  version/timestamps.
- `evidence_records` — id, state/assignment/revision links, exact text span, category (OBSERVED /
  HYPOTHESIZED / UNKNOWN — enforced), description, candidate instructional object, confidence, source
  (student_text / student_response / teacher_input / system_state), timestamp.
- `audit_events` — append-only. Requirement IDs, input state, evidence reviewed, decision, rationale,
  generated response, learner action, teacher override, output state, validation results, application
  version, timestamp, and a `supersedes`/`superseded_by` correction chain.

No existing document is migrated in place; UUID string ids + `{_id:0}` projection follow the codebase
convention.

---

## 3. Migration behavior
`POST /api/admin/foundation/migrate` (authorized) scans `sessions` **read-only** and creates one
instructional state per legacy session that lacks one (idempotent via `migrated_from_session_id`).
Mapping: assignment purpose ← `telos.governing_pedagogical_purpose`; intended reader ←
`telos.audience_or_communicative_purpose`; current text ← last student turn; instructional object ←
`theory.scaffolding_control.primary_target`. Any field the legacy record cannot populate becomes
`UNKNOWN`/`null` and is recorded in `migration_limitations` **and** in a `migration` audit event. It never
deletes or edits student writing, assignments, teacher settings, or interaction records. First run on this
environment: **created=50, skipped=0, limitations logged=150** (genre + grade_level are not present on
legacy sessions → correctly UNKNOWN).

---

## 4. Diagnostic trace (screenshot description)
`?trace=<state_id>&role=teacher` renders a minimal, read-only panel (screenshot captured during testing):
header "Compass · Diagnostic Trace" + a `teacher / admin · read-only` badge, and a caption "This is an
interpretive trace, not a score." Rows: **Current target** (Thesis), **Observed strength**, **Evidence
used (OBSERVED)**, **Provisional interpretation (HYPOTHESIZED)**, **Uncertainty (UNKNOWN)**, **Current
support level** (guided_practice), **Exit criterion status** (met), **Most recent advancement decision**
(advance), **Teacher overrides** (shows `scaffolding_level: "UNKNOWN" → "guided_practice" (new to
op-eds)`), **Applicable requirement IDs** (VA-05, DS-02, VA-07, VA-06). Every row carries a `data-testid`.
The epistemic separation (OBSERVED vs HYPOTHESIZED vs UNKNOWN) is explicit on the face of the panel. No
numeric score is shown. A student role receives HTTP 403.

---

## 5. Test results (A–G + guards) — 11/11 PASS, against the external API URL logic
| Test | Result | Evidence |
|---|---|---|
| **A** revision persists across refresh | PASS | after save+GET: version=2, revision_history=2 |
| **B** OBSERVED vs HYPOTHESIZED stored separately | PASS | observed_evidence=1, provisional_hypotheses=1, categories distinct |
| **C** missing evidence → UNKNOWN (not fabricated) | PASS | stored with category=UNKNOWN |
| **D** teacher override recorded + visible after refresh | PASS | trace shows support=guided_practice + 1 override |
| **E** audit event links requirement IDs | PASS | 7 events, all carry requirement_ids (e.g. ['VA-05']) |
| **F** contradictory state blocks advancement | PASS | advance with exit=met + no OBSERVED evidence → HTTP 409, decision=blocked, VA-07 in failed_requirements, visible diagnostic notice |
| **G** existing records remain accessible after migration | PASS | migrate created=50, skipped=0, limitations=150; sessions untouched |
| DS-02 prohibited attribution rejected as OBSERVED fact | PASS | "lazy…not a writer" as OBSERVED → HTTP 422, requirement DS-02 |
| trace restricted from student | PASS | student role → HTTP 403 |
| advance happy-path with observed support | PASS | HTTP 200, decision=advance |
| audit append-only correction | PASS | correction adds event (7→9); original preserved with `superseded_by` set |

Guard coverage: **VA-05** (persistence), **DS-01** (category integrity — enforced at write + in guard),
**DS-02** (no prohibited attribution as fact), **TC-01** (overrides logged + visible in trace),
**VA-06** (audit carries requirement IDs), **VA-07** (conflict/missing → blocked + uncertain, not invented).
On failure, advancement is prevented and a visible diagnostic (not a stack trace) is returned to authorized
users only.

Re-run: `cd /app/backend && API_URL=http://localhost:8001 python3 tests/sprint1_foundation_tests.py`

---

## 6. Known limitations
- Governing specs v0.9 / v0.95 were unavailable; requirement IDs and field names follow the sprint brief.
  Any additional spec requirements can be added without rework.
- Authorization is a minimal role gate (`viewer_role=teacher|admin`); no full identity/session auth was in
  scope for this sprint (the brief asked to keep the interface minimal and not redesign UX).
- DS-02 uses a curated prohibited-attribution word/pattern list; it is conservative and extensible, not an
  exhaustive classifier.
- Legacy `genre` and `grade_level` are not present on old sessions → migrated as UNKNOWN (logged).
- The trace panel is intentionally minimal and not yet wired into the teacher navigation (reached by URL).

## 7. Out-of-scope confirmation
No instructional dialogue, CIO logic, Stage B/C reasoners, or Knowledge Base hydration was changed. The
frozen engine hash is unchanged (`1c485e2c13d7b8ff`). Only additive foundation code + one read-only panel
were introduced.

---

## FREEZE
All Sprint 1 tests pass without regression → the state / evidence / audit foundation is **CERTIFIED and
FROZEN**. Later sprints may consume its interfaces (`/api/instructional-state/*`, the trace, the audit log)
but must not rewrite it without an explicit failed requirement or a dependency change.
