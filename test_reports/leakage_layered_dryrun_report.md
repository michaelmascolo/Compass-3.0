# Anti-Leakage Layered Architecture — Instrumented Dry-Run Report
Date: 2026-06 · Mode: LOG-ONLY (production runtime unchanged)
Harness: backend/tests/leakage_dryrun.py · Offline re-eval: backend/tests/leakage_recheck.py
Raw data: test_reports/leakage_dryrun_report.json · Log: test_reports/leakage_dryrun.log

## Governing principle (adopted, per user)
The boundary is PEDAGOGICAL, not lexical: *Given only the assignment, the student's own
response, and Compass's message, could the student now infer the substantive answer WITHOUT
consulting their own knowledge or source?* If yes → leak → rewrite. The novel-token detector is
one IMPLEMENTATION of this boundary, not the boundary itself. Ground truth in this dry run is a
Sonnet "pedagogical judge" applying exactly that test.

## Method
- 10 live cases: generate the Layer-1 draft with the LIVE hardened prompt on Haiku 4.5 (NO critic),
  then judge (Sonnet) + run the candidate deterministic checker in log-only mode.
- 8 hand-crafted adversarial messages, including semantic leaks that introduce FEW/NO new domain
  tokens, and clean messages that use structural words (dimension, mechanism) — to probe false
  negatives and unnecessary escalation.

## HEADLINE FINDINGS

### 1. Latency reality is far better than assumed — the "30–60s" was NOT the Sonnet call
Measured averages: Haiku Layer-1 draft ≈ **3.7 s**; a focused Sonnet call ≈ **3.2 s**; deterministic
check ≈ **0.1 ms**. So the CURRENT always-on critic totals ≈ **6.9 s**, already near-conversational.
The 30–60 s the QA agent felt on `mi-next-button` was **interaction chaining**, not model latency:
Next calls `persistIfDirty` (a full Haiku+Sonnet interact) AND then advances, on top of 1.5–2.5 s
UI polling — i.e. several sequential LLM round-trips per click, not one slow call.

### 2. Layer-1 (Haiku + hardened prompt) still leaks on a large fraction
Of the live teach drafts with a definitive judge label, **3/7 leaked** (inertia, plant/animal cells,
ice-floats), and two more (fixed-mindset, photosynthesis) failed to parse. Realistic Layer-1 leak
rate ≈ **40–50%**. Meaning: escalation would fire OFTEN, so the layered design's savings are modest.

### 3. A pure lexical/novel-token checker CANNOT gate reliably without POS tagging
Candidate checker flag rate = **100%** (v1) and **93–100%** (v2, threshold 1–2). The "novel tokens"
that drive false positives are contractions and generic verbs/adjectives, NOT domain content:
`you've, you're, doesn't, that's, plus, stated, choice, mean, back, works, want, sits, top`.
Raising the novelty threshold to 3 to cut FP immediately introduces FALSE NEGATIVES on real leaks
that use only 2 content tokens (`king rules`; `cheapest / cleanest` criteria). No threshold gives
clean separation. To flag only content-bearing NOUNS you need a POS tagger (nltk/spaCy) — neither is
installed — plus lemmatization; even then adjective-carried leaks ("cheapest") need special handling.

### 4. The judge reframes "semantic leaks" — restating the student's OWN words is not a leak
Two crafted "semantic leaks" (ice: *"because ice is lighter than the water, it sits on top…"*;
photosynthesis: *"a definition would say photosynthesis is the process by which plants use sunlight
to make food"*) were judged **NOT leaks** — the student had already supplied that content, so nothing
new was revealed. This VALIDATES the novel-vs-known framing: the dangerous leaks are those that
introduce content the student LACKED. The checker's known-set (question∪answer∪assignment) is the
right idea; the failure is purely in distinguishing content nouns from structural/function words.

## Requested metrics
- **Flag rate (candidate checker):** 100% (v1); 93% (v2 @ threshold 2); 60% (v2 @ threshold 3).
- **False positives:** 8/15 (v1) … 5/15 (v2 @3). Examples: clean comparison/argument/evaluation/
  thesis-praise turns flagged on `you've, stated, choice, cost, impact, reliability` (generic, not
  leaked content); `clean_dimension_word`, `clean_mechanism_word`.
- **False negatives:** 0 at threshold 1–2; **3 at threshold 3** — `leak_completes_contrast`
  ("king rules"), `leading_question_partial_novel` ("cheapest/cleanest"), and one judge-noisy case.
- **Adversarial no-new-token semantic leaks:** the genuinely dangerous ones still introduced ≥1
  content token and WERE caught; the "restate the student's own words" ones were judged NOT leaks —
  so the feared "zero-token subtle teach" class was largely empty under the pedagogical test.
- **Average latency:** Haiku 3.7 s · Sonnet 3.2 s · det 0.1 ms · current always-on 6.9 s.
- **Escalation-type distribution (candidate):** dominated by `novel_content_token`; the broken
  `direct_supply_frame` (matched bare "is") fired on 100% and was removed in v2; `leading_question`
  fired correctly on the cheapest/cleanest case.
- **Ground-truth noise:** the Sonnet judge itself mislabeled 1 clean structural message as a leak,
  so any deterministic tuning against it inherits ~1/18 label noise.

## Interpretation
The dry run does NOT support the "deterministic screening captures the overwhelming majority while
preserving quality" bar — because (a) without POS the screen over-flags to ~100%, giving no latency
win, and (b) Layer-1 leaks ~40–50%, so escalation is common regardless. HOWEVER, the exercise
surfaced a better lever: the perceived slowness is interaction chaining, and the real per-call cost
is only ~3 s.

## Recommendation (for approval — NOT implemented)
1. **Fix the interaction chain first (biggest, safest win).** Do NOT re-run diagnosis on `Next`:
   only diagnose on explicit "Share with my coach". Persist the answer on Next with a cheap non-LLM
   save endpoint. This removes the doubled round-trip that caused the 30–60 s feel, with ZERO
   boundary risk and no model change.
2. **Keep the Sonnet critic but only on `Share`/teach turns** (already ~3 s). Net teach latency ≈
   Haiku 3.7 s + Sonnet 3.2 s ≈ 7 s, once per deliberate coaching request rather than per keystroke-y
   navigation.
3. **If we still want Layer 2**, do it PROPERLY: add spaCy, restrict novel-token flagging to NOUNS
   + PROPN (lemmatized) minus a structural allowlist, plus the leading-question regex. Then re-run
   this harness; only ship if FP<10% and FN=0 on an expanded adversarial set. Until then a lexical
   screen is not safe to gate on.
4. **Offline audit, not runtime gate.** Run the Sonnet pedagogical judge as a nightly sample audit
   over shipped teach messages (zero user latency) to catch drift, instead of gating every turn.

## CONCEPTUAL FRAME (adopted): Layer 2 IMPLEMENTS the boundary, it does not DEFINE it
The governing principle is pedagogical: *could the student now infer the substantive answer from
only the assignment + their own response + Compass's message, without their own knowledge or
source?* The novel-token screen is a fast PROXY for that principle, not the principle itself.
Ground truth in this dry run is the Sonnet pedagogical judge applying exactly that test.

## ADDENDUM — no-new-token semantic leaks (the class you asked to stress)
Targeted adversarial set (backend/tests/leakage_adversarial.py, results in
test_reports/leakage_adversarial_addendum.json): leaks that recombine ONLY words already present
in the question or the student's answer — e.g. enumerated-choice questions.
- **Decisive FALSE NEGATIVE:** Q "Do plants make their food using sunlight or soil?" · A "I'm not
  sure." · Msg "Plants make their food using sunlight, not soil." → lexical screen: **0 novel
  tokens → NOT flagged**; pedagogical judge: **LEAK (reveals the answer)**. The leaked content
  lives in the QUESTION's own words, so the novel-token screen is structurally blind to it.
- **FALSE POSITIVE (control):** a genuinely CLEAN "how to answer a choice question" message was
  flagged on structural words (gives, options, asks, pick, choose) while the judge said clean.
- The other enumerated leaks (gravity/tides/democracy/water-cycle) were flagged only INCIDENTALLY
  (on contractions like "it's/doesn't" or one spillover noun), i.e. for the wrong reason — a
  contraction-free rephrase would slip through.
- Addendum tally: tp=4, fp=1, **FN=1** — and that one FN is the pure demonstration that a lexical
  screen cannot be the arbiter of a pedagogical boundary.

## IMPLICATION FOR THE ARCHITECTURE
Because the boundary is functional, not lexical: the deterministic Layer 2 can only ever be a
FAST-PATH PROXY, never the sole judge. It should be used to (a) cheaply CLEAR the obvious-clean
majority and (b) ESCALATE anything suspicious — but the enumerated/recombination class means we
cannot treat "0 novel tokens" as proof of safety. Practical consequence: keep an LLM in the loop
for the final pedagogical check on at least a sampled/uncertain slice (runtime confirmer or nightly
audit), and treat the deterministic layer as a latency optimization over a still-pedagogical
backstop — not a replacement for it.

## Artifacts
- backend/tests/leakage_dryrun.py (harness) · backend/tests/leakage_recheck.py (offline re-eval)
  · backend/tests/leakage_adversarial.py (no-new-token addendum)
- test_reports/leakage_dryrun_report.json · test_reports/leakage_adversarial_addendum.json
- test_reports/leakage_dryrun.log (run trace)
No production files were modified.
