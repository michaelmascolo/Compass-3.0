# Compass — Performance Audit (Time to First Developmental Response)
**Audit only. No code changed. Measured from real runs + backend latency instrumentation.** · 2026-07-26

## 1. Three-run timing table (fresh, current assignment flow — fired concurrently)

| Run | Session | Stage-A selector | Prompt build | Stage-B reasoner | DB read+write | Reasoner prompt bytes | **TOTAL (submit→turn complete)** |
|----|---------|-----------------|--------------|------------------|---------------|----------------------|-----------------------------------|
| 1 | 0c8c1a34 | 3.90s | 0.001s | 42.92s | ~0.002s | 67,893 | **46.82s** |
| 2 | 901a65af | 3.88s | 0.001s | 49.32s | ~0.002s | 66,246 | **53.21s** |
| 3 | f22059d5 | 4.49s | 0.001s | 49.77s | ~0.002s | 69,811 | **54.26s** |

Corroborating earlier preview runs (sequential): TOTAL 48.14 / 49.61 / 50.62s (Stage-B 40.9 / 46.6 / 45.1s).
Non-preview (full serialized output) runs: Stage-B **59.4–69.9s**.

**Reading:** Stage-B reasoner is **~91–93% of total**. Stage-A ~7–9%. Prompt build, DB read/write, parsing, assembly = **negligible (~1–4 ms each)**.

## 2. LLM-call inventory (per learner submission)

**Exactly TWO calls, both `anthropic/claude-sonnet-4-6`, run SEQUENTIALLY.**

| # | Call | Purpose | Model | Input size | Output | Latency | Required before 1st teaching? | Parallel? | Notes |
|---|------|---------|-------|-----------|--------|---------|-------------------------------|-----------|-------|
| 1 | Stage-A selector (`_select_relevant_domains`) | Pick 1–3 domains + 1–3 instructional objects from compact indexes | claude-sonnet-4-6 | small (~1-line system + compact index + student text) | small JSON | **3–7s** | Yes (its output builds retrieval + Stage-B prompt) | No (blocks B) | Simple classification on a frontier model; can use a smaller/faster model, be merged into B, or cached per session |
| 2 | Stage-B reasoner (`_run_engine`) | Full developmental reasoning → structured theory + the single `student_facing_invitation` | claude-sonnet-4-6 | **system 56,618 chars (~14K tok) + user 40–72 KB (~10–18K tok)** ≈ 25–33K input tok | **large structured JSON** (~10–15K output tok; preview trims serialized fields) | **41–70s** | Only the `student_facing_invitation` (+ `reader_understanding`) is needed for the first move; the rest is storage/later turns | No | **The bottleneck.** Output-token-bound (see §5/§6) |

- **No JSON-repair loop.** `_extract_json` parses once; a parse failure raises and the outer `for attempt in range(2)` re-issues the **entire ~50s call** — rare but catastrophic when hit.
- **No retries** on the successful runs. **No `max_tokens`, no `thinking`/extended-reasoning params, no elevated reasoning setting.**
- **Duplication:** Stage-A is a lightweight pre-pass; it does not duplicate Stage-B, but its job (choosing domains/objects) could be folded into Stage-B or done by a cheaper model.

## 3. Sequential dependency map

**Current:**
```
Frontend submit → session create → interact() persists student turn + processing placeholder → returns (fast)
   → [background] _run_reasoning:
        DB read (1ms)
        → Stage-A selector call (3–7s)          [LLM #1]
        → instructional-object retrieval (in-memory, ~0ms) + prompt build (1ms)
        → Stage-B reasoner call (41–70s)        [LLM #2]
        → parse (ms) → DB write (1ms)
   → frontend polls every 1.5s → renders when status=complete
```
Genuine dependency: Stage-B needs Stage-A's selected objects. **A→B is a real data dependency** (cannot be naively parallelized). The only safe restructures are: (a) make A cheaper/faster, (b) merge A into B (one call), or (c) stream B's invitation first so the learner doesn't wait for the full object.

## 4. M1–M14 necessity classification

M1–M14 are **not** separate services or separate calls — they are **layers of instruction inside the single Stage-B system message + one model call**, all produced together as one JSON object. So "which modules must finish first" maps to **which OUTPUT FIELDS are needed for the first visible move**, not to separable execution stages:

| Output concern | Classification |
|---|---|
| `student_facing_invitation` (the one teaching move) | **Required before first response** |
| `reader_construction.reader_understanding` (Ch6 understanding judgment) | **Required before first response** (Ch6) |
| `scaffolding_control` (target, postponed, cycle_status) | Needed for later coaching / stop logic — deferrable from first paint |
| `revision_development` | Needed only for **revision analysis** (revise turns) |
| `integration_calibration`, `candidate_invitations`, `selected_invitation` rationale | Useful/bookkeeping — deferrable |
| `instructional_reasoning` full block | Needed for later coaching + storage — deferrable from first paint |
| Reader-model sub-fields (likely_reader_questions, precision_risk, …) | Needed only for later turns / storage — deferrable |

**Note:** the frozen engine intentionally *reasons through all layers internally* to produce a valid single invitation. Deferral must apply to **serialization/return**, not to the internal reasoning that guarantees validity. (This is exactly what the existing `preview_output` trim does — and it already cut Stage-B ~30%.)

## 5. First-response minimum

The smallest trustworthy packet for the first developmental move = **`student_facing_invitation` + `reader_understanding`** (+ enough of `scaffolding_control` to know cycle_status/target for the next turn, which can arrive slightly later). Everything else supports later coaching, revision analysis, and storage.

**Evidence this is achievable without shallow output:** enabling `preview_output` (serialize fewer fields, identical reasoning) dropped Stage-B from **~60–70s → ~41–49s (~30%)** with no change to the decision. Output volume — not reasoning depth — is the dominant, reducible cost. Emitting/serializing the invitation FIRST (and streaming it) lets the learner see valid teaching while the full theory finishes behind the scenes.

## 6. Primary latency causes (ranked, with evidence)

1. **Stage-B output size (largest, reducible).** Generating a huge nested theory JSON. Evidence: preview trim cut ~30% of Stage-B time. Output-token-bound.
2. **Stage-B input size / no prompt caching.** 56,618-char system message + 40–72 KB user (incl. ~27 KB of retrieved instructional objects) re-sent every turn; **no Anthropic prompt caching** on the static system message / objects. Raises TTFT and cost every call.
3. **Frontier model for the trivial Stage-A selection** (3–7s that a smaller model could do in ~1s).
4. **Sequential A→B round trip** adds 3–7s of pure latency.
5. **No streaming on the main path** — nothing is shown until the *entire* JSON completes; the single teaching sentence is buried in a large object.
6. **Polling at 1.5s** — completed results wait up to 1.5s (avg ~0.75s) for the next poll. Minor.
7. **Parse-failure re-call** — a malformed JSON costs a full second ~50s call. Rare.
8. **Provider queue / concurrency** — modest inflation under concurrent load (fresh 3 concurrent runs slightly higher than sequential). Not primary.
9. **Cold start** — not observed as primary.

## 7. Streaming

- The main exhaustive path uses `LlmChat.send_message` **non-streaming** (awaits the full JSON).
- **Streaming-over-polling already exists** in the codebase: `triage_experiment.run_triage_pipeline_streaming` writes partial invitation text to the placeholder turn with `status="streaming"`, and the **frontend already understands `status="streaming"`** (PublicPreview/interact guards handle it). So streaming *learner-facing* text is technically supported today.
- **Opportunity:** stream **only** the `student_facing_invitation` (a learner-facing conclusion — not hidden reasoning) so the first teaching appears in seconds. Chain-of-thought / internal fields must never be streamed.
- **To confirm:** whether `emergentintegrations.LlmChat` exposes token streaming for the exhaustive path the same way the triage helper uses it.

## 8. Caching & precomputation

- **Static, resent every call (candidates for Anthropic prompt caching / load-once):** the 56,618-char `SYSTEM_MESSAGE`, the retrieved instructional-object text (static, ~9 KB each), schema boilerplate, grade/hs-grad framing. These never change between turns.
- Instructional objects and canonical model are already loaded once in memory (`INSTRUCTIONAL_OBJECTS`, `_IO_BY_NAME`); the cost is **re-sending them to the model**, not recomputation.
- **Do not** alter canonical instructional content to save tokens. The lever is **prompt caching** (provider-side reuse of the static prefix) + not re-sending unchanged objects, not editing the content.
- **To confirm:** prompt-caching support through the emergent integration layer.

## 9. Polling & frontend delay

- Poll interval: **1500 ms** (`PublicPreview.jsx`); `<Thinking/>` rotates copy every 4000 ms.
- Completed results wait up to one poll (≤1.5s) to surface. **No artificial minimum display time** exists.
- SSE/websockets or shorter polling (or the existing streaming-status transport) would improve *perceived* latency; but with a ~45s output-bound backend, frontend transport is a minor factor until the backend streams.

## 10. Options

### OPTION A — Minimal engineering change (no reasoning-logic change)
- Enable provider **prompt caching** for the static `SYSTEM_MESSAGE` + instructional-object prefix (confirm support).
- Move Stage-A selection to a **smaller/faster model** (e.g., Claude Haiku) — trivial classification.
- Extend the existing `preview_output` **output trim** (serialize fewer fields) and **emit `student_facing_invitation` first**.
- Shorten polling to ~800 ms.
- **Expected:** Stage-A ~1–2s; Stage-B TTFT lower (caching) + ~10–20s off from output trim → **TOTAL ≈ 30–40s** (still output-bound; does NOT alone hit the 8–15s target).
- **Files:** `server.py` (Stage-A model string, cache flags, schema emit order/trim), `PublicPreview.jsx` (poll interval). **Instructional-validity risk:** low (reasoning unchanged). **Frozen-engine risk:** low–moderate (touches output serialization, precedented by `preview_output`). **Effort:** low–moderate. **Cost:** ↓ (caching + Haiku). **Reversible:** yes.

### OPTION B — Staged instructional execution (first valid move fast, defer the rest) — *recommended core*
- Keep the full internal reasoning, but **stream the `student_facing_invitation` first** to the placeholder turn (reuse the existing `status="streaming"` transport), then complete/persist the full theory in the background for later turns/storage.
- Guarantee validity with the existing **66-case regression harness** before enabling.
- **Expected first meaningful (streamed) instruction: ~8–20s**; full analysis finishes behind it (~30–45s) but is hidden.
- **Files:** `server.py` (`_run_engine`/`_run_reasoning`, schema emit order, partial-parse), `PublicPreview.jsx` (render streamed invitation — status already handled), possibly `triage_experiment.py` (reuse streaming helper). **Instructional-validity risk:** moderate (must prove streamed invitation == full-schema invitation via harness). **Frozen-engine risk:** moderate (output contract/ordering, not the reasoning). **Effort:** moderate. **Cost:** ~flat. **Reversible:** yes (feature flag).

### OPTION C — Larger orchestration redesign
- Merge Stage-A into Stage-B (drop the separate selector round trip) or run a cheap Stage-A in parallel with cache warming; adopt end-to-end **streaming (SSE/websocket)**; distilled preview system message; re-evaluate model allocation.
- **Expected:** first meaningful instruction **~8–15s**; full analysis ~20–35s.
- **Files:** `server.py` (orchestration, models, streaming endpoint), `PublicPreview.jsx` (SSE client), possibly `triage_experiment.py`. **Instructional-validity risk:** higher (needs full regression). **Frozen-engine risk:** high (restructure). **Effort:** high. **Cost:** likely ↓ (caching) net. **Reversible:** with flags/branch.

## Recommended approach
**A + B, in that order, behind a feature flag, gated by the 66-case regression harness.**
1. Ship **A** first (prompt caching, Haiku for Stage-A, output-first-invitation trim, faster poll) — pure-latency/cost wins with no reasoning change. Measure.
2. Add **B** (stream the single learner-facing invitation first; complete the theory in the background) — this is what actually moves *time-to-useful-instruction* into the **~8–20s** range, because the bottleneck is output generation and B stops making the learner wait for the whole object.
3. Hold **C** unless A+B prove insufficient.

## Estimated first-response time after optimization
- **A only:** ~30–40s total (better, still above target — output-bound).
- **A + B:** **first streamed teaching ~8–20s** (target-aligned); full theory ~30–45s, hidden behind the streamed invitation.
- Honest caveat: total *full-analysis* time stays tens of seconds with the current single-frontier-model design; the target is met by **streaming valid teaching first**, not by making the whole theory instant.

## Exact files that would change (if approved — NOT changed in this audit)
- `backend/server.py` — `_select_relevant_domains` (model), `_run_engine`/`_run_reasoning` (streaming + emit order + partial parse + optional prompt-cache flags), `_build_prompt`/system-message handling (caching; optional preview-distilled prefix), `_compact_theory`/output-trim.
- `frontend/src/components/PublicPreview.jsx` — poll interval; render streamed invitation (streaming status already handled).
- Possibly `backend/triage_experiment.py` — reuse its streaming pipeline helper.
- **Unchanged:** `instructional_objects.json`, `canonical_writing_model.json`, and all reasoning-logic content in `SYSTEM_MESSAGE` (only caching/serialization-order/what-is-returned would change, never the instructional reasoning).

*No implementation performed. Awaiting approval before any change.*
