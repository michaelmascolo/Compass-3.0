# Experience Compass — Build Slice 1 Architectural Review
**Design review only. No code was modified.** · 2026-07-26

Scope: the implementation exactly as it exists in `backend/server.py`
(`ExperienceControl`, `ExperienceReflection`, `_experience_objective_id`,
`_experience_reader_effect`, `_build_experience_reflection`,
`_update_experience_control`, `_finalize_turn`, `interact`, `create_preview_session`)
and `frontend/src/components/PublicPreview.jsx` + `ExperienceReflection.jsx`.

---

## 1. Experience Compass State Diagram (as implemented)

```
                        POST /api/sessions/preview
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ SESSION CREATED │  experience_control = {phase:"active",
                          │  (phase=active) │   objective_locked:false, support_count:0,
                          └─────────────────┘   support_cap:3, revision_count:0}
                                   │
                                   │ learner submits seed passage
                                   │ (interact kind="writing")
                                   ▼
                          ┌─────────────────┐
                          │     WRITING     │  (first turn only)
                          └─────────────────┘
                                   │ AI turn completes → _finalize_turn →
                                   │ _update_experience_control:
                                   │   objective LOCKED (from
                                   │   instructional_reasoning.active_instructional_element)
                                   ▼
                    ┌───────────────────────────────┐
        ┌──────────►│           TEACHING            │◄─────────────┐
        │           │  (phase=active, one coaching  │              │
        │           │   card shown; objective fixed)│              │
        │           └───────────────────────────────┘              │
        │              │            │             │                 │
        │  learner     │            │ learner     │ learner submits │
        │  answers/    │            │ revises     │ revision that   │
        │  explains    │            │ (substantive│ is NOT          │
        │ (answer/     │            │  change)    │ substantive     │
        │  explain)    │            ▼             │ (no-op)         │
        │              │    ┌───────────────┐     │                 │
        │              │    │   REVISION    │     └── UI blocks send │
        │              │    │ revision_count│         (dirty guard);  │
        │              │    │  +1; support  │         no interact,     │
        │              │    │  _count = 0   │         stays TEACHING   │
        │              │    └───────────────┘                         │
        │              │       │          │                           │
        │              │  objective    objective                      │
        │              │  NOT resolved  resolved                      │
        │              │  (dd≠"yes" &   (dd starts "yes" OR            │
        │              │   cycle∉{stop, cycle∈{consolidate_and_return, │
        │              │   consolidate})     stop})                    │
        │              │       │          │                           │
        │              │       └──────────┼──── returns to ───────────┘
        │              │                  │      TEACHING (unresolved)
        │              ▼                  │
        │      ┌──────────────┐           │
        │      │   SUPPORT    │           │
        │      │   EXCHANGE   │  support_count += 1                    
        │      │ (answer/     │           │
        │      │  explain)    │           │
        │      └──────────────┘           │
        │         │        │              │
        │  support_count  support_count   │
        │   < 3           == 3            │
        │   │             (cap reached)   │
        └───┘             │               │
                          ▼               ▼
                   ┌────────────────────────────┐
                   │         REFLECTION          │  phase="reflection" (TERMINAL)
                   │  reflection = 4 sections    │  completion_reason =
                   │  editing controls hidden;   │   "support_cap"  or  "resolved"
                   │  passage read-only          │
                   └────────────────────────────┘
                          │                 │
             interact →   │                 │ "Try another paragraph"
             HTTP 409     │                 │ (frontend restart())
             (session     │                 ▼
              frozen in   │        ┌────────────────────┐
              reflection) │        │ TRY ANOTHER (NEW    │  POST /api/sessions/preview
                          │        │ SESSION)            │  → brand-new SESSION CREATED;
                          │        └────────────────────┘   old session stays phase=
                          │                 │               "reflection" forever
                          └── (no legal      └──► back to SESSION CREATED (top)
                               forward path)
```

**Legal paths (every one that exists):**
1. Created → Writing → Teaching → *(answer/explain ×1–2)* → Support Exchange → Teaching → … → Support Exchange (3rd) → **Reflection(support_cap)** → Try Another → new Created.
2. Created → Writing → Teaching → Revision *(unresolved)* → Teaching → … → Revision *(resolved)* → **Reflection(resolved)** → Try Another → new Created.
3. Created → Writing → Teaching → Revision *(resolved on first revision)* → **Reflection(resolved)** → Try Another.
4. Any Teaching/Reflection state + `interact` while `phase="reflection"` → **HTTP 409** (no state change).

**Accuracy note on the requested "Complete" state:** the code has **no distinct `complete` state**. `interact` guards `phase in ("reflection","complete")`, but nothing ever sets `"complete"` — it is aspirational/dead. **Reflection is the terminal state.** "Try Another Paragraph" does not transition the old session to Complete; it abandons it client-side (the old doc remains `phase="reflection"`) and creates a *new* session. The diagram reflects this truth rather than inventing a Complete node.

---

## 2. Engine / Product Boundary

### A. Frozen Developmental Engine (sole authority — unchanged)
- Developmental diagnosis, target selection, instructional reasoning (`scaffolding_control`, `instructional_reasoning`).
- Whether a revision represents growth: `revision_development.development_detected`, `primary_growth`, `communication_change`, `transfer_message`.
- Cycle control signal: `scaffolding_control.cycle_status`.
- The instructional invitation text (student-facing coaching).
- Canonical writing knowledge (`instructional_objects.json`, `canonical_writing_model.json`).

### B. Experience Compass Product Layer (session flow only)
- Session lifecycle / phase machine (`ExperienceControl`, `_update_experience_control`).
- Counting support exchanges and revisions; enforcing the **support cap (3)** and the **stop**.
- Reading the engine's completion signals and deciding **when to stop** (it does not decide *whether the learner improved* — it *reads* the engine's judgment).
- Reflection **presentation** (4-section assembly) and UI (hide controls, read-only passage, "Try another").
- 409 enforcement.

### Boundary findings
- ✅ **Stopping / counting / phase** are pure product concerns — clean.
- ✅ **Completion rule** *consumes* engine outputs (`development_detected`, `cycle_status`) rather than re-judging — correct; no second evaluator.
- ✅ **Reader effect** (`_experience_reader_effect`) reads `communicative_purpose` from the canonical KB — that is *data lookup*, not an instructional decision — acceptable.
- ⚠️ **One soft leak — reflection prose authorship.** `_build_experience_reflection` sometimes *authors pedagogical language* rather than surfacing the engine's:
  - Section 2 "How your writing changed": uses the engine's `primary_growth`/`communication_change` **when present**, but on the **support-cap** path (and when those fields are empty) the product writes its own sentence ("You explored this writing idea through the coaching conversation…").
  - Section 4 "Carry it forward": uses the engine's `transfer_message` when resolved, otherwise the product writes a **generic transfer sentence** ("When you write your next paragraph, look for another opportunity…").
  These fallbacks are *descriptions of the learner's activity and generic transfer advice*, not developmental diagnosis, so they do not corrupt the engine's authority — but they are the **only place** the product layer emits learner-facing pedagogical wording.

  **Recommendation (Slice 2, non-blocking):** treat engine-authored text as the *preferred* source for sections 2 and 4 in all cases; keep product fallbacks (i) clearly generic, (ii) centralized as named constants, and (iii) explicitly non-diagnostic. If richer consolidation is ever wanted on the support-cap path, request it from the engine (it already produces consolidation language) rather than growing product-side prose. Do **not** let the fallback library expand into anything that asserts *what the learner learned*.

**Verdict:** the boundary is clean except for the intentional, contained reflection-fallback prose. No target selection, diagnosis, or progress judgment has leaked into the product layer.

---

## 3. Reflection Audit

Current four sections: (1) The one thing you worked on, (2) How your writing changed, (3) Why it helps your reader, (4) Carry it forward. `completion_reason ∈ {resolved, support_cap}`.

| Criterion | Assessment |
|---|---|
| Accurately represents progress | **Yes.** Resolved path uses engine `primary_growth`; support-cap path explicitly states the learner *has not revised yet*. |
| Avoids exaggerated claims | **Yes.** Support-cap wording refuses to imply change. |
| Avoids false mastery | **Yes.** `resolved` flag gates any "you strengthened…" language; unit test asserts the support-cap text says "haven't revised". |
| Sounds natural | **Mostly.** Resolved section 2 can surface **raw engine phrasing** (e.g. `primary_growth` may read like internal notes / contain a capacity label) — occasionally clinical. |
| Reinforces learning | **Partially.** Section 3 ("Why it helps your reader") reinforces communicative function; but on the fallback it is generic. |
| Supports transfer | **Yes on resolved** (engine `transfer_message`); **generic on support-cap** (fixed sentence). |

**Repetitive / mechanical wording to watch:**
- Sections 2 and 4 fallbacks both open with "When you write your next paragraph…" style phrasing; if `transfer_message` is empty on a resolved turn, sections could feel echoey.
- Section 3 fallback string is a single fixed sentence — will read identically on every fallback session (mechanical if hit often).
- The support-cap section 2 sentence is fixed verbatim — a returning learner who hits the cap twice sees the exact same line.

**Improvements (within the fixed 4-section structure):**
1. Prefer the engine's own consolidation/`transfer_message`/`primary_growth` for sections 2 & 4 in *all* completion reasons; only fall back when genuinely empty.
2. If a section must fall back, lightly humanize the raw engine capacity label (e.g. map "evidence-interpretation gap" → "connecting your evidence to your point") rather than printing the internal phrase.
3. Provide a *small rotation* (2–3 variants) for each fallback sentence so repeat cycles don't read identically — presentation-only, no new pedagogy.
4. Section 3: when the locked element resolves to a KB object, its `communicative_purpose` is good; ensure the element-name match rate is high (see §4) so the generic fallback is rarely used.

None of these require changing the four-section contract.

---

## 4. Complexity Audit

**Dead / obsolete code:**
- `PREVIEW_FIXED_SELECTIONS` (server.py ~1005) and `PREVIEW_FIXED_IO` (~1010) are **defined but referenced nowhere** — leftover from the reverted R1 preview optimization. Safe to delete.
- `interact` guards `phase in ("reflection","complete")` but **`"complete"` is never set** anywhere — dead branch value. Either implement a real Complete state or drop the string.
- `PreviewBridge.jsx` is no longer imported by `PublicPreview.jsx` but remains reachable via the `?bridge` route in `App.js`. Intentional per Slice 1 spec ("remove from reflection, not delete"), but it is currently orphaned from any linked path.

**Redundant state:**
- Completion is encoded **three times**: `ExperienceControl.resolved` (bool), `ExperienceReflection.resolved` (bool), and `ExperienceReflection.completion_reason` (str). `completion_reason` alone is sufficient; the two booleans are derivable. Not harmful, but three sources of one truth.
- `preview_analytics.soft_cap_reached = exchange_count >= 6` now **coexists with, and contradicts, `support_cap = 3`**. Two different "cap" notions (analytics soft cap at 6 exchanges vs. product hard stop at 3 support exchanges) will confuse future readers. Reconcile or clearly namespace them.

**Branching / logic:**
- `_update_experience_control` is a single, readable state function — good. The only implicit decision beyond the literal spec is **resetting `support_count` to 0 on a substantive revision** (a reasonable interpretation of "3 support exchanges *without* a revision"); worth documenting as an explicit product decision.
- Frontend: `reviseCount`, `completedAi`, `activeCoaching` are all still used (labels / coaching card) — not dead.

**Maintainability opportunities (defer, non-blocking):**
- The four Experience-Compass helpers + models live inside a 3,300-line `server.py`. Extracting them into `experience_compass.py` would isolate the product layer from the frozen engine and make the boundary physically visible. Recommended before the layer grows in Slice 2.

---

## 5. Product Experience Review

**Flow:** Seed screen → begin → single coaching card (one target) → revise-in-place or ask → reflection → "Try another." Coherent and document-centered (not a chatbot).

- **Pacing:** dominated by **engine latency (~60–120s/turn)**. A learner who asks for support up to the cap can experience ~3–6 minutes of waiting across turns before the deliberate stop. The single-target design keeps *cognitive* load low, but *temporal* load is the real UX cost and is inherited from the frozen engine (not a Slice-1 defect).
- **Stopping point:** clear and deliberate; the 409 makes the stop authoritative server-side, and the UI removes editing affordances so the learner is not left hunting for a next action.
- **Cognitive load:** low — one objective, one card, one passage, four short reflection sections.
- **Clarity:** strong; the reflection explicitly names *what* was worked on and *why it matters to a reader*.
- **Feels complete?** Yes — the four sections + a single clear CTA give a genuine sense of closure rather than an abrupt cut-off.
- **Encourages another cycle?** *Weakly.* "Try another paragraph" is the only CTA and is presented neutrally. There is no motivational bridge ("try a different kind of passage", "see how Compass handles a conclusion"). This is appropriate restraint for Slice 1 but is the obvious place Slice 2 can lift re-engagement.

---

## 6. Readiness Assessment

- **Internally consistent?** ✅ Yes. The state machine has one entry, one terminal state (Reflection), well-defined transitions, and a server-enforced stop. Behavior is covered by 7 offline unit tests + API tests + a live lock test.
- **Engine/product boundary clean?** ✅ Substantially. Diagnosis, target selection, progress judgment, and invitations remain solely the engine's; the product only counts, stops, and presents. The single contained exception is **reflection fallback prose** (§2), which is descriptive/generic, not diagnostic.
- **Appropriate foundation for Slice 2?** ✅ **Yes — architecturally stable.** No blocking defects.

**Recommended (non-blocking) clean-ups before layering Slice 2 features:**
1. Delete dead `PREVIEW_FIXED_SELECTIONS` / `PREVIEW_FIXED_IO`.
2. Resolve the phantom `"complete"` phase (drop it, or make Reflection→Complete a real, explicit terminal transition when "Try another" is chosen).
3. Reconcile `preview_analytics.soft_cap_reached` (6) with `support_cap` (3) so there is one cap concept.
4. Collapse the triple completion state to `completion_reason` (derive the booleans) — or document why all three exist.
5. Prefer engine-authored text for reflection sections 2 & 4 in *all* paths; keep fallbacks generic, centralized, and non-diagnostic.
6. (Optional, recommended before the layer grows) extract the Experience-Compass product layer into its own module to make the frozen-engine boundary physical.

**Confirmations:** frozen engine, instructional objects, and canonical writing knowledge are untouched; anti-coauthoring is unchanged; Experience Compass completes exactly one developmental cycle (one objective → revision → reflection → deliberate stop).

**Bottom line:** Build Slice 1 is a **stable, internally consistent foundation** with a clean engine/product boundary. Proceed to Slice 2; address the six clean-ups opportunistically (items 2 and 3 first, since they touch semantics future features will build on).
