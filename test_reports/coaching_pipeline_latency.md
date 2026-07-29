# Coaching Pipeline Latency Profile

Measured on a representative live **student composition** preview turn (`?preview=writing`).
Assignment: *"Should schools require students to wear uniforms?"* — a 4-sentence student draft.
Session `af6679b5…`, 2026-07-29. Model: Claude Sonnet 4.6 (Stage A/B/C), Claude Haiku 4.5 (acknowledgement).

All numbers from server-side `[latency]` instrumentation (`time.perf_counter`) plus client-observed round trips.

## Per-stage timing

| # | Stage | What happens | Time | Notes |
|---|-------|--------------|------|-------|
| 1 | **Submission received** | `POST /interact` appends student turn + a `processing` placeholder, returns immediately | **0.13 s** | Client-observed round trip; DB write < 1 ms |
| 2 | **Immediate acknowledgement** | `POST /noticing` (Haiku) — grounded "I'm reading your writing" observations | **1.9 s** | Side channel; runs in parallel with Stage A/B. Now instrumented (`acknowledgement_noticing`). Client round trip ≈ 2.0 s |
| 3 | **Stage A — domain/instructional-object selection** | selector LLM call | **3.92 s** | Preview R1 can skip this for a fixed-selection path; this run used the selector |
| 4 | **Prompt assembly** | build the reasoner prompt (~69 KB) | **0.001 s** | Negligible, pure string work |
| 5 | **Stage B — developmental reasoner** | the frozen engine produces the full structured diagnosis + plan | **46.83 s** | Dominant cost (~78 % of the visible wait) |
| 6 | **Teacher Review generation** | `_curate_case` transforms the SAME Stage B plan into the teacher-facing four-question mirror | **0.14 s** | Pure transform, **off the student's critical path** (rendered on demand via `GET /teacher-reflection`); does not delay coaching |
| 7 | **Stage C — coaching renderer + validator** | renders the student-facing coaching from the plan; deterministic leak/target validation (regenerate once if needed) | **16.65 s** | Second Sonnet call |
| 8 | **Rendering / persistence** | `_finalize_turn` + single Mongo write of the completed turn | **0.001 s** (`db_write`) | DB read at task start also 0.001 s |
| — | **Student sees coaching** | durable polling (2.5 s interval) surfaces the completed turn | +0 – 2.5 s | Poll detection lag only |

**End-to-end (submission → coaching visible): ≈ 67 s** (`TOTAL=67.4 s`).
Time-to-first-instruction for the student is far shorter: the **immediate acknowledgement appears at ≈ 2 s**, and the **writer-metacognition orientation fills the wait** from then until the coaching lands.

## Where the time goes

```
Stage B reasoner   46.83 s  ██████████████████████████████████████  ~70%
Stage C renderer   16.65 s  ██████████████                          ~25%
Stage A selector    3.92 s  ███                                     ~6%
Acknowledgement*    1.90 s  (parallel — not additive to the wait)
Submission/DB/build  <0.2 s (negligible)
Teacher Review gen   0.14 s (off critical path)
```
\* The acknowledgement is a parallel side channel; it is now its own measured stage because it is part of the instructional experience (point 1 + 5).

## Observations

- **Stage B dominates (~47 s).** Inherent to the frozen engine generating the full structured theory + plan. Not changed here (engine is frozen).
- **Stage C adds ~17 s.** The second Sonnet call that renders coaching. Candidate future optimization: a faster model or a slimmer render prompt for preview (gated — would need re-validation).
- **Everything else is effectively free** (< 0.2 s combined): submission, prompt build, DB read/write, and Teacher Review generation.
- **Teacher Review costs nothing extra** for the student — it is derived from the same in-memory Stage B plan and only materialized when a teacher opens the review.
- **Perceived experience is now front-loaded with instruction, not silence:** acknowledgement at ~2 s → writer-metacognition orientation → coaching at ~67 s.

## Instrumentation reference (server logs)
```
[latency] acknowledgement_noticing=1.9s
[latency] stage_a_selector=3.92s prompt_build=0.001s stage_b_reasoner=46.83s stage_c_renderer=16.65s reasoner_prompt_bytes=69685
[latency] db_read=0.001s db_write=0.001s stage_a=3.92s stage_b=46.83s TOTAL=67.4s
```
