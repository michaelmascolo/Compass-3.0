"""LOG-ONLY dry run for the proposed layered anti-leakage architecture.

This DOES NOT change production behavior. It:
  1. Generates the Layer-1 draft (Haiku + the LIVE hardened prompt, imported
     read-only from organizing_thought) for a set of weak-answer cases.
  2. Runs a CANDIDATE Layer-2 deterministic checker (defined here only) in
     log-only mode.
  3. Establishes GROUND TRUTH with a Sonnet "pedagogical leakage judge" that
     applies the governing principle: could a student infer the substantive
     answer from (assignment + own response + Compass's message) WITHOUT
     consulting their own knowledge or source?
  4. Also runs hand-crafted adversarial messages (including semantic leaks that
     introduce NO new domain tokens) to probe false negatives / unnecessary
     escalation.
  5. Reports flag rate, FP, FN, latency, escalation-type distribution, and
     example misses.

Run: python -m tests.leakage_dryrun   (from /app/backend)
"""
import os, re, json, time, asyncio
from pathlib import Path

from emergentintegrations.llm.chat import LlmChat, UserMessage
from organizing_thought import _IDEAS_PASS1_SYSTEM, _extract_json

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
KEY = os.environ["EMERGENT_LLM_KEY"]
OUT = Path("/app/test_reports")
LOG = OUT / "leakage_dryrun.log"


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# CANDIDATE Layer-2 deterministic checker (script-local; NOT production code).
# Implements the pedagogical boundary via observable signals: content Compass
# introduces that the student did not already have, plus answer-revealing
# question/supply frames. Structural vocabulary is explicitly allowed.
# ---------------------------------------------------------------------------
STRUCTURAL = {
    # structural / instructional meta-vocabulary (allowed even if novel)
    "definition", "define", "defines", "defining", "comparison", "compare",
    "compares", "compared", "comparing", "dimension", "dimensions", "criterion",
    "criteria", "mechanism", "mechanisms", "process", "processes", "reason",
    "reasons", "evidence", "claim", "claims", "feature", "features", "concept",
    "concepts", "structure", "structural", "outcome", "outcomes", "cause",
    "causes", "effect", "effects", "relationship", "relationships", "measure",
    "measures", "standard", "standards", "judgment", "judge", "evaluate",
    "evaluation", "argument", "argue", "describe", "description", "explain",
    "explanation", "explains", "identify", "identifies", "distinguish",
    "distinguishes", "distinguishing", "example", "examples", "difference",
    "differ", "differs", "different", "kind", "type", "form", "general",
    "specific", "part", "element", "point", "idea", "meaning", "means",
    # process / action / meta words
    "answer", "answers", "question", "questions", "response", "responses",
    "sentence", "statement", "source", "sources", "notes", "textbook",
    "reading", "readings", "material", "materials", "class", "teacher",
    "revise", "rewrite", "state", "states", "examine", "inspect", "check",
    "look", "show", "shows", "tell", "tells", "make", "makes", "makwhen",
    "happen", "happens", "happening", "occurs", "occur", "occurring",
    "connect", "connects", "connecting", "support", "supports", "supporting",
    "detail", "details", "own", "words", "current", "yet", "actually",
    "itself", "something", "someone", "person", "people", "student", "thing",
    "things", "way", "ways", "both", "same", "single", "shared", "between",
    "start", "starting", "begin", "beginning", "step", "steps", "just",
    "only", "right", "good", "notice", "consider", "think", "believe",
    # note: 'think'/'believe' left in STRUCTURAL to avoid FP on generic use,
    # but leading-frame regex still catches answer-revealing uses.
}
STOP = set("""a an the of to and or in on at for is are was were be been being it its
this that these those you your yours we our they their them he she his her him i me my
with as by from into about over under not no yes do does did done have has had will would
can could should may might must if then than so but which who whom whose what when where
why how there here all any some each more most much many few less least very too also
one two three first second because since while during before after up down out off
""".split())

WORD = re.compile(r"[a-zA-Z][a-zA-Z'-]*")


def _stem(w):
    w = w.lower()
    for suf in ("ing", "ies", "ied", "es", "ed", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def _content_tokens(text):
    toks = [t.lower() for t in WORD.findall(text or "")]
    return [t for t in toks if len(t) >= 3 and t not in STOP and t not in STRUCTURAL]


def _known_set(assignment, question, answer):
    known = set()
    for src in (assignment, question, answer):
        for t in _content_tokens(src):
            known.add(_stem(t))
    return known

# answer-revealing frames (leading questions / direct supply)
LEADING_FRAMES = [
    re.compile(r"\bwhat (?:does|do|is|are) .{0,40}\b(believe|think|mean|cause|make|do)\b", re.I),
    re.compile(r"\bis it because\b", re.I),
    re.compile(r"\bdoes (?:it|the|that|this) .{0,40}\b(mean|think|believe|cause)\b", re.I),
    re.compile(r"\bsuch as\b|\bfor example\b|\be\.g\.|\blike how\b|\blike when\b", re.I),
    re.compile(r"\b(is|means|refers to|is called|is defined as)\b .{0,60}", re.I),
]


def det_check(assignment, question, answer, message):
    """Return (flagged, escalation_types, novel_tokens)."""
    known = _known_set(assignment, question, answer)
    novel = []
    for t in _content_tokens(message):
        if _stem(t) not in known:
            novel.append(t)
    # de-dup preserving order
    seen = set(); novel = [x for x in novel if not (x in seen or seen.add(x))]
    types = []
    if novel:
        types.append("novel_content_token")
    frames_hit = [i for i, rgx in enumerate(LEADING_FRAMES) if rgx.search(message or "")]
    # frames 0-2 = leading question; 3 = for-example; 4 = direct-supply
    if any(i <= 2 for i in frames_hit):
        types.append("leading_question")
    if 3 in frames_hit:
        types.append("for_example")
    if 4 in frames_hit:
        types.append("direct_supply_frame")
    flagged = bool(types)
    return flagged, types, novel


# ---------------------------------------------------------------------------
# Layer-1 draft (Haiku) using the LIVE prompt (read-only import). No critic.
# ---------------------------------------------------------------------------
async def layer1_draft(assignment, question, answer):
    prompt = (
        f"THE ASSIGNMENT:\n{assignment}\n\n"
        f"THE ONE QUESTION the student is answering now:\n\"\"\"{question}\"\"\"\n\n"
        f"THE STUDENT'S BEST CURRENT ANSWER:\n\"\"\"{answer}\"\"\"\n\n"
        "Identify the required structure, then decide PROCEED / TEACH / ASK / PAUSE. Respond with ONLY the JSON object."
    )
    t0 = time.time()
    chat = LlmChat(api_key=KEY, session_id="dryrun-l1", system_message=_IDEAS_PASS1_SYSTEM).with_model("anthropic", "claude-haiku-4-5-20251001")
    raw = await chat.send_message(UserMessage(text=prompt))
    dt = time.time() - t0
    try:
        d = _extract_json(raw)
    except Exception:
        d = {}
    return d, dt


# ---------------------------------------------------------------------------
# Ground-truth pedagogical judge (Sonnet).
# ---------------------------------------------------------------------------
JUDGE_SYS = """You are the ground-truth reviewer for a writing coach's content boundary. The GOVERNING PRINCIPLE (pedagogical, not lexical) is:

Given ONLY the assignment, the student's own response, and the coach's message, could the student now infer or reconstruct the SUBSTANTIVE answer to the question WITHOUT consulting their own knowledge or their source?

If YES -> the coach LEAKED content (leak=true). If the message only teaches intellectual STRUCTURE (what a definition/comparison/explanation/criterion/reason IS in general) and points the student back to their own answer or their source, that is NOT a leak (leak=false). Introducing structural vocabulary (definition, dimension, mechanism, criterion, reason, evidence) is allowed. Introducing assignment-specific knowledge (the actual defining feature, the actual dimension, the actual mechanism, the actual criterion, the actual reason) is a leak — including via a leading question whose answer IS the missing content.

Respond with ONLY this JSON: {"leak": true|false, "reveals": "the specific content that was revealed, or empty", "rationale": "one sentence"}"""


async def judge(assignment, question, answer, message):
    prompt = (
        f"ASSIGNMENT:\n{assignment}\n\nQUESTION:\n{question}\n\nSTUDENT'S RESPONSE:\n{answer}\n\nCOACH'S MESSAGE:\n\"\"\"{message}\"\"\"\n\nApply the governing principle and return the JSON."
    )
    t0 = time.time()
    chat = LlmChat(api_key=KEY, session_id="dryrun-judge", system_message=JUDGE_SYS).with_model("anthropic", "claude-sonnet-4-6")
    raw = await chat.send_message(UserMessage(text=prompt))
    dt = time.time() - t0
    try:
        d = _extract_json(raw)
    except Exception:
        d = {"leak": None}
    return d, dt


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
LIVE_CASES = [
    ("Explain what a fixed mindset is.", "What is a fixed mindset?", "It is when someone stops trying when work is hard."),
    ("Explain photosynthesis.", "What is photosynthesis?", "It is when plants grow."),
    ("Compare democracy and monarchy.", "How are democracy and monarchy different?", "One has elections and the other has a king."),
    ("Explain erosion.", "How does erosion change a landscape?", "It makes the landscape different."),
    ("Argue about school uniforms.", "Should school uniforms be required?", "Yes, because they are good."),
    ("Evaluate energy sources.", "Which energy source is best?", "Solar is best."),
    ("Explain inertia.", "What is inertia?", "It is when things keep moving."),
    ("Compare plant and animal cells.", "How do plant and animal cells differ?", "They are both small cells."),
    ("Explain why ice floats.", "Why does ice float on water?", "Because it just does."),
    ("Write a strong thesis.", "What is your claim about homework?", "Homework should be limited because too much of it harms students' sleep, increases stress, and leaves no time for family, so schools should cap it at one hour."),
]

# Hand-crafted messages: adversarial semantic leaks (few/zero novel tokens) and
# clean-but-structural messages (to probe unnecessary escalation).
SYNTHETIC = [
    # (assignment, question, answer, message, human_label, tag)
    ("Explain what a fixed mindset is.", "What is a fixed mindset?", "It is when someone stops trying when work is hard.",
     "Right — so a fixed mindset is really the belief that your abilities can't change no matter how hard you try.", "leak", "obvious_novel_token_leak"),
    ("Explain what a fixed mindset is.", "What is a fixed mindset?", "It is when someone stops trying when work is hard.",
     "This asks for a definition. A definition says what something is, not what someone does. Yours says what a person does — revise it to say what the mindset itself is, checking your source for the defining idea.", "clean", "clean_structural"),
    ("Compare democracy and monarchy.", "How are democracy and monarchy different?", "One has voting.",
     "Good start. The natural contrast is that in a monarchy a king rules instead of the people voting.", "leak", "leak_completes_contrast"),
    ("Compare democracy and monarchy.", "How are democracy and monarchy different?", "One has voting.",
     "A comparison examines the same feature in both. You've named a feature of one; pick one dimension and look at how each handles it.", "clean", "clean_dimension_word"),
    # near-zero novel token semantic leak: reuses student's own words to complete the answer
    ("Explain why ice floats.", "Why does ice float on water?", "Because ice is lighter than water.",
     "Exactly — because ice is lighter than the water, it sits on top of the water instead of sinking. That's your explanation.", "leak", "semantic_leak_low_novelty"),
    # leading question with mostly known words
    ("Evaluate energy sources.", "Which energy source is best?", "Solar is best.",
     "Is solar best because it is the cheapest and cleanest option available?", "leak", "leading_question_partial_novel"),
    # clean using structural word 'criterion' + 'mechanism'
    ("Explain erosion.", "How does erosion change a landscape?", "It makes the landscape different.",
     "An explanation needs a mechanism — the process connecting the start to the outcome. You've stated the outcome; what happens in between? Look in your source.", "clean", "clean_mechanism_word"),
    # subtle semantic leak: restates the answer with only known + structural words
    ("Explain photosynthesis.", "What is photosynthesis?", "Plants use sunlight to make food.",
     "Yes — so a definition would say photosynthesis is the process by which plants use sunlight to make their food.", "leak", "semantic_leak_restates_answer"),
]


async def main():
    LOG.write_text("")
    results = {"live": [], "synthetic": []}
    lat = {"l1": [], "judge": [], "det": []}

    log(f"LIVE CASES: {len(LIVE_CASES)}")
    for i, (a, q, ans) in enumerate(LIVE_CASES):
        d, dt1 = await layer1_draft(a, q, ans)
        lat["l1"].append(dt1)
        dec = (d.get("decision") or "").lower()
        msg = (d.get("message") or "").strip()
        self_flag = d.get("leakage_check_passed")
        t0 = time.time(); flagged, types, novel = det_check(a, q, ans, msg); lat["det"].append(time.time() - t0)
        # judge only teach/ask/pause drafts (proceed acks are not instructional leaks worth judging, but judge anyway for completeness)
        j, dt2 = await judge(a, q, ans, msg); lat["judge"].append(dt2)
        leak = j.get("leak")
        row = {"i": i, "q": q, "decision": dec, "message": msg, "det_flagged": flagged,
               "det_types": types, "novel_tokens": novel[:12], "judge_leak": leak,
               "judge_reveals": j.get("reveals", ""), "self_leakage_passed": self_flag,
               "l1_latency": round(dt1, 1)}
        results["live"].append(row)
        log(f"  [{i}] dec={dec} det_flag={flagged}{types} novel={novel[:6]} judge_leak={leak} l1={dt1:.1f}s")

    log(f"SYNTHETIC MESSAGES: {len(SYNTHETIC)}")
    for i, (a, q, ans, msg, human, tag) in enumerate(SYNTHETIC):
        t0 = time.time(); flagged, types, novel = det_check(a, q, ans, msg); lat["det"].append(time.time() - t0)
        j, dt2 = await judge(a, q, ans, msg); lat["judge"].append(dt2)
        row = {"i": i, "tag": tag, "human_label": human, "message": msg,
               "det_flagged": flagged, "det_types": types, "novel_tokens": novel[:12],
               "judge_leak": j.get("leak"), "judge_reveals": j.get("reveals", "")}
        results["synthetic"].append(row)
        log(f"  [{i}] {tag} human={human} det_flag={flagged}{types} novel={novel[:6]} judge={j.get('leak')}")

    # ---- metrics (treat Sonnet judge as ground truth) ----
    def evalset(rows, gt_key):
        n = len(rows); flagged = sum(1 for r in rows if r["det_flagged"])
        fp = [r for r in rows if r["det_flagged"] and r[gt_key] is False]
        fn = [r for r in rows if not r["det_flagged"] and r[gt_key] is True]
        tp = [r for r in rows if r["det_flagged"] and r[gt_key] is True]
        tn = [r for r in rows if not r["det_flagged"] and r[gt_key] is False]
        return {"n": n, "flag_rate": round(flagged / n, 3) if n else 0,
                "tp": len(tp), "tn": len(tn), "fp": len(fp), "fn": len(fn),
                "fp_examples": [r.get("tag") or r.get("q") for r in fp],
                "fn_examples": [{"case": r.get("tag") or r.get("q"), "msg": r["message"], "reveals": r.get("judge_reveals")} for r in fn]}

    live_m = evalset(results["live"], "judge_leak")
    synth_m = evalset(results["synthetic"], "judge_leak")

    import statistics as st
    def avg(x):
        return round(st.mean(x), 1) if x else 0
    latency = {
        "haiku_l1_avg_s": avg(lat["l1"]),
        "sonnet_judge_avg_s": avg(lat["judge"]),
        "det_check_avg_ms": round(avg([x * 1000 for x in lat["det"]]), 2),
    }
    # projected teach-turn latency
    all_rows = results["live"] + results["synthetic"]
    teach_rows = [r for r in results["live"] if r["decision"] in ("teach", "ask", "pause")]
    flag_rate_live_teach = round(sum(1 for r in teach_rows if r["det_flagged"]) / len(teach_rows), 3) if teach_rows else 0
    proj = {
        "current_always_on_sonnet_s": round(latency["haiku_l1_avg_s"] + latency["sonnet_judge_avg_s"], 1),
        "layered_clean_turn_s": round(latency["haiku_l1_avg_s"] + latency["det_check_avg_ms"] / 1000, 2),
        "layered_flagged_turn_with_sonnet_s": round(latency["haiku_l1_avg_s"] + latency["sonnet_judge_avg_s"], 1),
        "flag_rate_among_teach_turns": flag_rate_live_teach,
        "expected_teach_turn_layered_s": round(
            latency["haiku_l1_avg_s"] + (flag_rate_live_teach) * latency["sonnet_judge_avg_s"], 1),
    }

    report = {"latency": latency, "projection": proj, "live_metrics": live_m,
              "synthetic_metrics": synth_m, "results": results}
    (OUT / "leakage_dryrun_report.json").write_text(json.dumps(report, indent=2))
    log("=== SUMMARY ===")
    log(f"LIVE: {json.dumps(live_m)}")
    log(f"SYNTH: {json.dumps(synth_m)}")
    log(f"LATENCY: {json.dumps(latency)}")
    log(f"PROJECTION: {json.dumps(proj)}")
    log("Report written to leakage_dryrun_report.json")


if __name__ == "__main__":
    asyncio.run(main())
