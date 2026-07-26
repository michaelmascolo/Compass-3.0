"""Chapter 6 — Pedagogical Noticing validation harness (Level 3).

Validates the ADDITIVE noticing generator (frozen engine untouched). Per the
Ch6 spec + approval refinements, each generated noticing must satisfy:

  1. UNDERSTANDING is genuinely GROUNDED in the learner's actual meaning — it
     demonstrates real comprehension, NOT a surface paraphrase of wording, and
     NOT something that could be said about almost any response.
  2. RECOGNITION is AUTHENTIC when present — specific to THIS response, never
     generic praise; and it is acceptable for it to be ABSENT (null) when there
     is nothing honest to recognize (never manufactured).
  3. NO TEACHING LEAKAGE — no instructional targets, deficiencies, corrections,
     advice, diagnoses, element-to-fix, comparisons, or scores.
  4. LATENCY within the intended fast range.

A SEPARATE LLM evaluator (claude-sonnet-4-6) grades authenticity — we are testing
instructional authenticity, not grammatical correctness. Runs the real generator
`_pedagogical_noticing` directly (no session / no frozen-engine involvement).
"""
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
import server  # noqa: E402

OUT_JSON = "/app/test_reports/chapter6_noticing_results.json"
OUT_MD = "/app/test_reports/chapter6_noticing_review.md"

# Diverse cases: strong/weak/minimal/off-topic/narrative/argumentative/reflective/
# ELL-surface-errors/very-confident/very-tentative — to probe grounding + honest
# (sometimes absent) recognition + zero teaching leakage.
CASES = [
    ("strong_explanatory", "Explain why regular exercise improves mental health.",
     "Regular exercise improves mental health because it releases endorphins that reduce stress and improve mood. When people exercise, their bodies produce chemicals that make them feel happier and more relaxed. This is why doctors often recommend physical activity for people dealing with anxiety or depression."),
    ("weak_vague", "Explain why regular exercise improves mental health.",
     "Exercise is good for you. It makes you feel better and healthy. Everyone should exercise because it is important for the body and mind."),
    ("minimal", "Argue whether homework helps students learn.",
     "Homework is bad because it takes too much time and stresses kids out."),
    ("off_topic", "Explain how photosynthesis works.",
     "My favorite subject is science because my teacher is really nice and we do fun experiments in class every Friday afternoon."),
    ("narrative", "Describe a moment when you learned something about yourself.",
     "The rain hadn't stopped for three days. I sat by the window watching the water pool in the street, and for the first time I realized I actually liked being alone with my thoughts instead of always needing someone around."),
    ("argumentative_strong", "Should schools start later in the morning?",
     "Schools should start later because teenagers' biological clocks shift during adolescence, making it hard for them to fall asleep before 11pm. Forcing them to wake at 6am creates chronic sleep deprivation, which research links to lower grades and higher rates of depression."),
    ("reflective_tentative", "Reflect on what makes a good friend.",
     "I think maybe a good friend is someone who listens? I'm not totally sure. Sometimes I feel like the best friends are the ones who are just there even when nothing is happening, but I haven't fully worked out why that matters to me."),
    ("ell_surface_errors", "Explain why learning a second language is valuable.",
     "Learning second language is very valuable because open your mind for new culture and peoples. When you speak another language you can understand how other person is thinking and see the world different way. Also is good for the brain and for find job."),
    ("confident_unsupported", "Argue whether social media is harmful to teenagers.",
     "Social media is completely destroying an entire generation. It is obviously the worst thing to ever happen to young people and anyone who disagrees simply hasn't been paying attention."),
    ("descriptive", "Describe a place that feels like home to you.",
     "My grandmother's kitchen always smelled like cardamom and warm bread. The yellow curtains were faded from years of sun, and the wooden table had a crack down the middle that she refused to fix because, she said, it gave the table a story."),
    ("compare_contrast", "Compare living in a city to living in a small town.",
     "Cities and small towns are different. Cities have more things to do and more people. Small towns are quieter and everyone knows each other. Both have good things and bad things depending on what you like."),
    ("cause_effect", "Explain the causes of the American Civil War.",
     "The Civil War happened mostly because of slavery, but it was also about states wanting the power to make their own rules against the federal government. Economic differences between the industrial North and the agricultural South made these tensions even worse over time."),
    ("process", "Explain how to study effectively for an exam.",
     "To study well you should start early and not wait until the night before. Break the material into small parts and review a little each day. Testing yourself works better than just rereading because it shows you what you actually don't know yet."),
    ("literary_analysis", "Analyze the role of the green light in The Great Gatsby.",
     "The green light represents Gatsby's hope and his longing for Daisy. It sits across the water so he can never quite reach it, which is kind of the point — it stands for a dream that stays just out of reach no matter how hard he tries."),
    ("very_short_idea", "What is courage?",
     "Courage is doing something even when you are scared."),
    ("dense_but_unclear", "Explain the importance of the water cycle.",
     "The water cycle is important and involves evaporation condensation precipitation collection and it keeps going around and around forever which is why water is never really used up it just moves through different states and places on earth all the time constantly."),
]

EVAL_SYSTEM = """You are a strict evaluator of a writing teacher's OPENING move — the moment, before any teaching, when the teacher shows a learner "I understand you." You are given: the assignment, the learner's first draft, and the teacher's noticing (an UNDERSTANDING statement, an optional RECOGNITION, and an optional BRIDGE).

Judge instructional AUTHENTICITY, not grammar. Apply these tests:

GROUNDED_UNDERSTANDING (pass|fail): PASS only if the understanding demonstrates genuine comprehension of what THIS learner actually means/intends — the substance of their idea. FAIL if it merely reshuffles or lightly rewords their surface wording without showing comprehension, OR if it is so generic it could be said about almost any response to almost any assignment.

AUTHENTIC_RECOGNITION (pass|fail|na): If recognition is null/absent → "na" (absence is acceptable and correct when nothing genuine is present). If present → PASS only if it names something SPECIFIC and real about THIS response that could NOT be honestly said about just any piece of writing. FAIL if it is generic praise, flattery, or could apply to nearly any submission.

NO_TEACHING_LEAKAGE (pass|fail): PASS only if the noticing contains NO instructional target, NO deficiency/weakness, NO correction, NO advice ('you should' / 'try' / 'consider adding' / 'to improve'), NO diagnosis, NO naming of a writing element to fix, NO comparison to others, NO score/evaluation. The bridge may warmly open collaboration but must NOT name anything to work on. FAIL if any teaching, evaluation, or fix leaks in.

Respond with ONLY this JSON (no prose, no fences):
{"grounded_understanding":"pass|fail","authentic_recognition":"pass|fail|na","no_teaching_leakage":"pass|fail","notes":"one sentence justification quoting the deciding phrase"}"""


async def evaluate(assignment, response, noticing):
    prompt = (
        f"ASSIGNMENT:\n{assignment}\n\nLEARNER FIRST DRAFT:\n{response}\n\n"
        f"TEACHER NOTICING:\nunderstanding: {noticing.get('understanding')}\n"
        f"recognition: {noticing.get('recognition')}\n"
        f"bridge: {noticing.get('bridge')}\n\nGrade with ONLY the JSON object."
    )
    chat = LlmChat(
        api_key=server.EMERGENT_LLM_KEY,
        session_id=f"noticing-eval-{time.time()}",
        system_message=EVAL_SYSTEM,
    ).with_model("anthropic", "claude-sonnet-4-6")
    raw = await chat.send_message(UserMessage(text=prompt))
    return server._extract_json(raw)


async def main():
    results = []
    for cid, assignment, response in CASES:
        t0 = time.time()
        noticing = await server._pedagogical_noticing(assignment, response, f"eval-{cid}")
        latency = round(time.time() - t0, 2)
        if not noticing:
            results.append({"id": cid, "generated": False, "latency": latency,
                            "overall": "fail", "reason": "generator returned None"})
            print(f"[{cid}] GENERATOR FAILED ({latency}s)")
            continue
        try:
            ev = await evaluate(assignment, response, noticing)
        except Exception as e:  # noqa: BLE001
            ev = {"grounded_understanding": "error", "authentic_recognition": "error",
                  "no_teaching_leakage": "error", "notes": str(e)}
        gu = ev.get("grounded_understanding")
        ar = ev.get("authentic_recognition")
        nl = ev.get("no_teaching_leakage")
        overall = "pass" if (gu == "pass" and nl == "pass" and ar in ("pass", "na")) else "fail"
        results.append({
            "id": cid, "generated": True, "latency": latency,
            "understanding": noticing.get("understanding"),
            "recognition": noticing.get("recognition"),
            "bridge": noticing.get("bridge"),
            "eval": ev, "overall": overall,
        })
        print(f"[{cid}] {overall.upper()} lat={latency}s GU={gu} AR={ar} NL={nl} rec={'Y' if noticing.get('recognition') else 'null'}")

    passed = sum(1 for r in results if r["overall"] == "pass")
    total = len(results)
    lats = [r["latency"] for r in results if r.get("generated")]
    summary = {
        "total": total, "passed": passed, "failed": total - passed,
        "pass_rate": round(100 * passed / total, 1) if total else 0,
        "latency_min": min(lats) if lats else None,
        "latency_max": max(lats) if lats else None,
        "latency_avg": round(sum(lats) / len(lats), 2) if lats else None,
        "recognition_present": sum(1 for r in results if r.get("recognition")),
        "recognition_absent": sum(1 for r in results if r.get("generated") and not r.get("recognition")),
    }
    os.makedirs("/app/test_reports", exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    lines = [f"# Chapter 6 — Pedagogical Noticing Validation\n",
             f"- Cases: {total} · Pass: {passed} · Fail: {total - passed} · Pass rate: {summary['pass_rate']}%",
             f"- Latency (s): min {summary['latency_min']} · avg {summary['latency_avg']} · max {summary['latency_max']}",
             f"- Recognition present: {summary['recognition_present']} · honestly absent: {summary['recognition_absent']}\n",
             "| Case | Overall | Lat | Grounded | Recognition | No-leak | Notes |",
             "|---|---|---|---|---|---|---|"]
    for r in results:
        ev = r.get("eval", {})
        lines.append(f"| {r['id']} | {r['overall']} | {r.get('latency')}s | {ev.get('grounded_understanding','-')} | {ev.get('authentic_recognition','-')} | {ev.get('no_teaching_leakage','-')} | {(ev.get('notes','') or '')[:120]} |")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))

    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"\nReports: {OUT_JSON} , {OUT_MD}")


if __name__ == "__main__":
    asyncio.run(main())
