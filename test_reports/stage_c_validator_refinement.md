# Stage C Validator Refinement — "Ready-Made Sentence" Rule (Phase II, Step 4a)

Goal: detect ACTUAL violations of the constitutional rule more precisely, without weakening it.
Constitutional rule preserved: *Compass must not produce a polished sentence that performs the
student's target writing operation for them.*

## What was wrong
The old check flagged **any** quoted clause ≥24 chars that was not (≥60% word-overlap) the
student's own words. On the same topic, legitimate scaffolds reuse the student's vocabulary, so
the rule fired on:
- quotes attributed to a **reader/skeptic** (illustrative objections),
- **sentence frames / templates** with a blank (`… because ___`),
- **revision questions** in quotes (`"What is the one idea I want my reader to accept?"`),
- **off-topic structural examples** (a thesis from a *different* essay),
and even on the **student's own recognized wording** (word-overlap, not substring, misjudged it).

## The refinement (server.py `_readymade_violation` + `_quote_is_scaffold`)
A quoted clause is an ACCEPTABLE scaffold (NOT flagged) when it is any of:
1. a **contiguous substring of the student's own text** (recognition) — substring match, not word-overlap;
2. a **revision question** (ends with `?`);
3. a **sentence frame / template** (contains a blank/placeholder: `___`, `[…]`, `your reason/claim/…`, `…`);
4. **attributed to a reader/other** (attribution cue — reader/skeptic/someone/they … think/say/ask/object — precedes the quote);
5. an **off-topic structural example** (shares no salient content noun with the student's own writing, so it cannot serve as their answer to THIS assignment).
Otherwise — an on-topic, unattributed, non-question, non-frame polished sentence — it IS flagged.
The same test applies to suggestion-framed quotes ("you could write: '…'").

## Results — labeled set (`tests/stage_c_validator_cases.py`, 10 cases)
| Metric | Before | After |
|---|---|---|
| True positives (genuine ready-made caught) | 2/2 | **4/4** |
| False negatives | 0 | **0** |
| False positives (scaffolds wrongly flagged) | **4/6** | **0/6** |
| False-positive rate | 67% | **0%** |
Categories now correctly passed: reader_attributed, sentence_frame, revision_question,
structural_example, student_quote, operation_named. Categories still caught: genuine bare answer,
genuine suggestion-framed answer.

## Results — live, identical gen1 drafts (6 preview turns, old vs new logged side-by-side)
| | Before (legacy rule) | After (refined rule) |
|---|---|---|
| Ready-made regeneration rate | **5/6 = 83%** | **1/6 = 17%** |
| False positives regenerated | 4 | 0 |
| Genuine case still caught | 1 | 1 (old=new=True) |
| Avg gen1 latency | ~7.9 s | ~7.9 s |
| **Avg Stage C latency (est.)** | **~14.7 s** | **~9.3 s** |
Estimated saving ≈ **5.4 s per turn** on average (each avoided regeneration removes one ~8 s Sonnet call).

Verification of the 4 now-accepted drafts (manual inspection of the coaching text) — all contain only
legitimate scaffolds: revision questions, a `… because ___` frame, a reader-attributed fragment, and
the student's own recognized wording. None supply a submittable answer.

## Notes
- The refined validator is deterministic and adds ~0 ms.
- A legacy comparator (`_readymade_violation_legacy`) + `[stage_c_validator] readymade_old/new` log
  are retained for ongoing monitoring; remove later if noisy.
- FALSE-NEGATIVE guard: two adversarial genuine cases (on-topic bare answer, on-topic suggestion-framed
  answer) are in the labeled set and both are still flagged.

## Next (Step 4b — GATED)
Trial Claude Haiku 4.5 for the Stage C render against Sonnet, on IDENTICAL hydrated plans and the
IDENTICAL (refined) validator, judged on the full acceptance-criteria list. Adopt only if quality
holds and latency drops meaningfully; otherwise retain Sonnet.
