# Experience Compass — Canonical Implementation Specification (synchronized)
Source of truth = the user's approved chapters. This file tracks the approved spec + implementation status. Do not redesign; extend only.

## Architecture / principles (Ch1–2, approved)
- ~5-minute guided front door to full Compass; educator temporarily becomes the learner. Nonprofit (Common Ground Institute), relational-developmental. No pricing/subscriptions/upgrade/donation/scarcity/sales/account-gate before meaningful exploration. Teaching before technology; learner remains the author; teach, don't edit.
- Journey: Welcome → Assignment → Writing → Compass thinking → Developmental response → Revision → Reflection → Feedback request → Transition into Compass. No extra stages without approval.
- Frozen: M1–M14 engine, instructional objects, canonical model, Stage-A, coaching, reflection, experience_control, anti-coauthoring.

## Chapter 3 — Welcome Screen — APPROVED & IMPLEMENTED (frozen 2026)
- First surface before the assignment screen. Exact copy: title "Welcome to Experience Compass" + 3-sentence body + "Begin". One calm centered area; header hidden here only. Begin → assignment screen (no account/pricing/tour/modal/role/demographics).
- File: `frontend/src/components/WelcomeScreen.jsx`; gate in `PublicPreview.jsx` (`entered` state). Restart does NOT re-show Welcome; reappears on fresh reload.

## Chapter 4 — Assignment Screen (+ minimal interim Writing Screen) — APPROVED & IMPLEMENTED
- Assignment Screen (adapted from old SeedScreen): exact copy — heading "Create a brief assignment", intro text, label "Your assignment", the example placeholder, supporting line "Keep the assignment brief. You will respond to it yourself in the next step.", "Continue", "Help me create one". One dominant textarea; no subject/grade/standard/type required; no rubric/criteria asked.
  - Validation: Continue disabled until trimmed length ≥ 10 chars (blocks empty/whitespace/single-punct). Nonjudgmental hint "Please enter the assignment you would like to respond to." No red banner.
  - Help me create one: DISPLAY-ONLY inline list (8 starters) + "Choose one beginning and complete it in your own words." No wizard, no auto-fill, no generation.
  - Privacy line (subtle): "Please do not include a student's name or other identifying information."
  - Back control (subtle, subordinate to Continue): returns to Welcome, preserves assignment text.
- Minimal interim Writing Screen (provisional until Ch5): read-only assignment display + one response textarea + one submit ("Share with Compass"). Submit creates the session and posts the writing turn. No unapproved instructional copy.
- Restart ("Try another paragraph"): returns to a CLEARED Assignment Screen (clears assignment + response + session), never Welcome, same visit.
- Session timing: created ONLY on Writing-Screen submit (not on assignment entry). Assignment is never evaluated/rewritten/analyzed before the learner writes.
- Target-learner framing = "an intelligent high school graduate" (NOT grade-agnostic, NOT Grade 9).

### Backend narrow changes (preview wrapper only — approved)
`backend/server.py`:
- `PREVIEW_TEACHER_NOTES` clause 1 → "The educator is testing Compass by responding, as a learner, to an authentic assignment they created. They will write one thoughtful paragraph at approximately the level expected of an intelligent high school graduate." Clause 2 → "Treat the response as developing writing produced at approximately the level expected of an intelligent high school graduate." All other instructional rules verbatim (one target/turn, anti-coauthoring, meaning-before-convention, invite revision, fade support).
- `PreviewStart.assignment` (optional) added; `essay_about`/`passage_type` retained but unused.
- `create_preview_session`: when `assignment` provided → `session.assignment` + `telos.assignment_context` = exact assignment; notes get "THE ASSIGNMENT THE LEARNER IS RESPONDING TO: <assignment>". No evaluation/rewrite/reinterpretation.
- `PREVIEW_BOOTSTRAP.assignment` fallback → "Respond in one thoughtful paragraph to the assignment provided, writing at approximately the level expected of an intelligent high school graduate." (used only when no assignment supplied).
- "ESSAY CONTEXT" and essay-component PASSAGE TYPE hint removed (no essay/intro/body/conclusion presumption).
- No engine/instructional-object/Stage-A/coaching/reflection/experience-control changes.

Files (Ch4): `frontend/src/components/PublicPreview.jsx` (AssignmentScreen + WritingScreen in-file, state/handlers/gate, `beginPreview`→`submitResponse`, restart), `backend/server.py` (above).

## Chapter 5 — Writing Screen — APPROVED & IMPLEMENTED
- Copy: heading "Write your response"; intro "Respond to your assignment in one thoughtful paragraph. Write a genuine first draft. Do not try to make it perfect before Compass sees it."; label "Your assignment" + read-only exact display; response label "Your first draft"; placeholder "Write one paragraph in response to your assignment."; supporting "Stop when you have expressed your main idea. Compass will work with what you have written."; primary "Share with Compass"; Back control "Back to assignment" (subordinate).
- Large resizable textarea (min-h 220px, resize-y); no word processor/rubric/score/timer/counter/grammar/autocomplete/live-AI.
- Validation: submit disabled until trimmed length ≥ 15 (accidental-entry guard only; never judges adequacy/grammar/brevity/first-person/form/viewpoint). Gentle hint "Please write enough for Compass to understand the idea you are trying to express." (no red banner).
- EXACT response preserved: validate on trimmed, but send + set draft to the EXACT untrimmed response (no change to spacing/spelling/grammar/punctuation/capitalization/wording/structure).
- Back preserves response (parent state); editing the assignment does NOT erase/rewrite the response; revised assignment shown on return.
- Duplicate session prevention: `starting` guard + disabled button; on success the screen unmounts. Session created ONLY on submit.
- Handoff: `interact` returns immediately with a processing AI turn (background `_run_reasoning`); render moves to coaching branch showing the existing `<Thinking/>` + polling. Developmental response appears only after reasoning completes. Ch6 owns the visible thinking; unchanged here.
- File: `frontend/src/components/PublicPreview.jsx` (WritingScreen + submitResponse). No backend change; authentic-assignment handling + intelligent-high-school-graduate target from Ch4 remain operative.

## Chapter 6 — pre-noted (DO NOT implement until Ch6 spec is approved)
- Terminology cleanup owned by Ch6: the downstream Thinking + coaching/Developmental Response surface still uses essay/"passage" language that predates the assignment→response architecture. When Ch6 is implemented, review ALL visible language there and make it consistently refer to the learner's assignment / response / first draft (not "essay" or "passage"). Known instances: "YOUR PASSAGE" label; the Thinking lines ("Reading your passage as a reader would…", etc.); the "Reading…" submit label; likely others in the coaching card / revision controls. Leave unchanged until Ch6.

## Chapter 6 — ARCHITECTURAL DECISION (approved direction; NOT yet implemented)
- Compass Thinking + Developmental Response = ONE continuous instructional encounter, sequenced: **Understanding → Recognition → Invitation → Teaching**. The invitation must feel like the natural continuation of having first been understood.
- REJECTED: streaming the Stage-B invitation immediately (even though it is produced first) — it would improve latency but violate the instructional sequence.
- Provisional architecture (leading candidate, NOT approved for build): Submission → fast pedagogical-noticing process (establishes the relationship: "I see your main idea as…", "I notice…", "I'm considering…") → existing frozen Stage-B engine → developmental invitation → remaining DevelopmentalTheory completes in background. The noticing process does NOT replace the frozen engine; it establishes the instructional relationship before teaching.
- Hard constraints reaffirmed: do NOT stream the invitation, reorder the Stage-B schema, modify prompts, or modify the frozen engine until the complete Chapter 6 instructional architecture is finalized.
- Investigation facts feeding this (from COMPASS_PERFORMANCE_AUDIT.md addendum): latency is a serialization/transport artifact, not reasoning; prompt caching NOT available via the client/proxy; token streaming IS supported (used in triage_experiment); Stage-B emits student_facing_invitation FIRST and reader_understanding late.
- OPEN design questions to resolve before implementation: (1) source of the noticing judgments (a new fast LLM call vs. an early slice of the same engine call) and its cost/latency/load; (2) keeping noticing truthful/grounded without exposing chain-of-thought or revealing the withheld target; (3) the terminology cleanup (assignment/response/first draft, not "passage"/"essay") folds into this chapter.

## Pending
- Chapter 6 instructional architecture to be finalized before build. Chapters 7–9 not yet specified. Do not implement ahead.
