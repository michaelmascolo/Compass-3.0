# Stage C Render Model A/B — Sonnet 4.6 vs Haiku 4.5 (Phase II, Step 4b)

**Recommendation: RETAIN SONNET 4.6.** Haiku is 2.5× faster with identical instructional
fidelity and identical validator performance, BUT it systematically flattens the *orientation* —
the most instructionally distinctive part of Compass. Per the decision rule (instructional quality
over speed, any recurring orientation regression is disqualifying), Sonnet stays.

## Method — only the render model varied
For each of 5 representative drafts: Stage A + Stage B were run ONCE and the hydrated instructional
plan built once; BOTH models then rendered from the **identical plan**, through the **identical
COACHING_RENDERER_SYSTEM**, checked by the **identical refined validator** (with the production
single-regeneration). Harness: `tests/stage_c_model_ab.py`. Raw: `/tmp/ab_results.json`.

Because object/strategy/canonical-explanation/architecture/exit/next all come from the shared plan
+ KB, **instructional fidelity is identical by construction** — every case rendered the same
target (Thesis), same canonical explanation, same exit criterion, same next step for both models.

## Aggregate results (5 cases)
| Metric | Sonnet 4.6 | Haiku 4.5 |
|---|---|---|
| Avg render latency | **8.13 s** | **3.28 s** (2.5× faster) |
| Regeneration rate | 0/5 | 0/5 |
| Validator pass | 5/5 | 5/5 |
| Prompt leakage / target drift / ready-made | none | none |
| Recognition-first | 5/5 | 5/5 |
| WHAT / WHERE / NEXT present | 5/5 | 5/5 |
| One learner operation present | 5/5 | 5/5 |
| **Explicit essay-architecture framing in orientation** | **4/5** | **0/5** |
| Avg length | 244 words | 188 words (−23%) |

## Instructional fidelity — EQUIVALENT
Identical by design (shared plan). Both models named the same instructional object, used the same
canonical thesis explanation, and pointed to the same next step. No target drift in either. ✅

## Pedagogical quality — the orientation regression
The orientation is supposed to move: recognition → **essays are built from interacting structural
elements** → named object → canonical explanation → transferable strategy → architecture
connection → next. Haiku reliably delivers recognition, object, explanation, strategy, an
end-of-message architecture *connection*, and next — but it **omits the opening architecture
FRAMING** ("an essay is built from a claim, the reasons that support it, and how they connect")
in **all 5 cases**, jumping from recognition straight to the object. Sonnet includes it in 4/5.

This is precisely the element flagged as "most instructionally distinctive," and its loss is a
systematic (5/5) reduction, not noise.

### Side-by-side — CASE: uniforms (Thesis)
**Sonnet (8.8s, 260w):**
> Your opening already does something strong: you've staked out a clear position *and* lined up
> three distinct reasons behind it — expression, confidence, and cost … **an essay is built
> around a claim, the reasons that support it, and the way those reasons connect back to a central
> idea. Today we're working on your thesis** — the single sentence that tells a reader the one
> main idea your whole essay exists to establish and defend. A thesis isn't just a position you
> hold; it's a focused, arguable statement … One strategy writers use … *What is the most
> important thing I want someone who disagrees with me to walk away convinced of?* … Once you can
> name that stake … we'll come back and arrange those reasons so they build toward it together.

**Haiku (3.3s, 185w):**
> You've got a clear position here and three solid reasons to back it up—that's a strong
> foundation. **Now we're going to strengthen your thesis, which is the single sentence that tells
> your reader the main idea …** [no "an essay is built from …" framing] Right now you've stated
> that schools shouldn't require uniforms, but a reader finishes that sentence wondering: why does
> this actually matter? … One move writers use is to ask … Once you nail that core idea, we'll use
> it to reshape your thesis so every sentence in your essay points back to it.

**Comparison:** Haiku is warm, clear, and correctly scaffolds ONE operation — but it drops the
"essays are built from interacting parts" framing and gives a less specific recognition (Sonnet
names expression/confidence/cost; Haiku says "three solid reasons").

### Side-by-side — CASE: mindset (Thesis)
**Sonnet (9.3s, 282w):** includes "**In an essay, there are a few parts that work together: a
central claim, the reasons behind it, and the evidence that supports those reasons.**" then quotes
the student's own "I think a growth mindset is better for learning" and shows why "I think" softens
it — rich orientation + precise application.
**Haiku (3.2s, 171w):** recognition + "your last sentence … is doing the job of a thesis, which is
the one main idea …" — canonical explanation, strategy, and next all present, but again **no
essay-architecture framing**.

## Writing quality
Both: natural teacher voice, warm, clear, developmentally appropriate. Sonnet is slightly more
precise (names the specific reasons; quotes the student's sentence). Haiku is crisp and friendly.
Neither is mechanically worse in tone.

## Does Haiku produce shorter responses? Economy vs substance loss
Yes — Haiku is ~23% shorter (188 vs 244 words). The reduction is **mixed**: much of it is genuine
economy (tighter phrasing, less repetition — a positive), BUT a meaningful part is **loss of
instructional substance** — specifically the opening architecture framing (0/5) and less specific
recognition. So the shorter length is NOT purely economy; it removes a distinctive orientation move.

## Decision
- Instructional quality equivalent? **No** — orientation framing regresses 4/5 → 0/5.
- Latency improves meaningfully? Yes (2.5×).
- Validator performance unchanged? Yes (0 regen, 5/5 pass, both).
- Recurring reduction in instructional quality? **Yes (orientation).**
→ **RETAIN SONNET 4.6** for the Stage C render. Instructional quality takes precedence over speed.

## Follow-ups worth considering (not adopted here)
1. **Make the framing enforceable:** add a deterministic validator check that the orientation
   contains the essay-architecture framing. This would (a) harden Sonnet and (b) let us re-run the
   Haiku trial fairly — if a framing check forces Haiku to include it and quality then holds, Haiku
   could be reconsidered. (Would be a Haiku-specific prompt/validator change, i.e. a *new* trial,
   not this identical-conditions one.)
2. Sonnet's ~8 s render is now the largest remaining Stage-C cost; the biggest overall win still
   lives in Step 3 (slim Stage B), which remains gated.
