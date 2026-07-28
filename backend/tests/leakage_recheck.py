"""Offline re-evaluation of refined deterministic checkers against the saved
dry-run labels (Sonnet judge = ground truth). NO new LLM calls."""
import json, re
from pathlib import Path

R = json.load(open("/app/test_reports/leakage_dryrun_report.json"))

WORD = re.compile(r"[a-zA-Z][a-zA-Z'-]*")
STOP = set("""a an the of to and or in on at for is are was were be been being it its
this that these those you your yours we our they their them he she his her him i me my
with as by from into about over under not no yes do does did done have has had will would
can could should may might must if then than so but which who whom whose what when where
why how there here all any some each more most much many few less least very too also
one two three first second because since while during before after up down out off into
""".split())

# Structural / instructional / generic vocabulary that is SAFE even when novel.
STRUCTURAL = set("""
definition define defines defining defined comparison compare compares compared comparing
dimension dimensions criterion criteria mechanism mechanisms process processes reason reasons
evidence claim claims feature features concept concepts structure structural outcome outcomes
cause causes effect effects relationship relationships measure measures standard standards
judgment judge judges evaluate evaluation evaluates argument argue argues describe description
describes describing explain explanation explains explaining identify identifies distinguish
distinguishes distinguishing example examples difference differences differ differs different
kind kinds type types form forms general specific part parts element elements point points idea
ideas meaning means contrast contrasts position stance
answer answers question questions response responses sentence sentences statement statements
source sources notes note textbook reading readings material materials class teacher revise
revises rewrite rewrites state states restate restates examine examines examining inspect look
looks show shows showing tell tells make makes made happen happens happening occur occurs occurring
connect connects connecting support supports supporting detail details own words current yet
actually itself something someone person people student thing things way ways both same single
shared between start starting begin beginning step steps just only right good notice notices
consider considers think thinks believe believes ask asks asking name names names becoming become
becomes changes change changing find finds finding need needs needed using use uses used decide
decides key common pick picks handle handles gives give giving given put puts said says saying
see seen along instead exactly natural option options available help helps helping able require
requires said close correct clear specific enough real really genuine along toward towards
""".split())

WORD_STEM_SUF = ("ing", "ies", "ied", "es", "ed", "s")


def stem(w):
    w = w.lower()
    for suf in WORD_STEM_SUF:
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def content_tokens(text):
    toks = [t.lower() for t in WORD.findall(text or "")]
    return [t for t in toks if len(t) >= 3 and t not in STOP and t not in STRUCTURAL]


def known_set(a, q, ans):
    s = set()
    for src in (a, q, ans):
        for t in content_tokens(src):
            s.add(stem(t))
    return s


# refined leading-question frames: require a '?' in the message
LEAD = [
    re.compile(r"\bwhat (?:does|do|is|are|would|might) .{0,50}\?", re.I),
    re.compile(r"\bis it (?:because|that)\b.{0,50}\?", re.I),
    re.compile(r"\bdoes (?:it|the|that|this) .{0,50}\?", re.I),
    re.compile(r"\b(?:such as|for example|e\.g\.|like how|like when)\b", re.I),
]


def checker_v2(a, q, ans, msg, min_novel=1):
    known = known_set(a, q, ans)
    novel = []
    for t in content_tokens(msg):
        if stem(t) not in known:
            novel.append(t)
    seen = set(); novel = [x for x in novel if not (x in seen or seen.add(x))]
    types = []
    if len(novel) >= min_novel:
        types.append("novel_content_token")
    if "?" in (msg or "") and any(r.search(msg or "") for r in LEAD[:3]):
        types.append("leading_question")
    if LEAD[3].search(msg or ""):
        types.append("for_example")
    return bool(types), types, novel


def evaluate(name, min_novel):
    rows = []
    for r in R["results"]["live"]:
        rows.append(("live-" + str(r["i"]), R["results"]["live"][r["i"]], r))
    cases = []
    # rebuild (a,q,ans) is not stored for live; reconstruct from known LIVE order
    from tests.leakage_dryrun import LIVE_CASES, SYNTHETIC  # reuse definitions
    tp = fp = fn = tn = 0; flagged = 0; total = 0
    fps = []; fns = []
    for i, r in enumerate(R["results"]["live"]):
        gt = r["judge_leak"]
        if gt is None:
            continue
        a, q, ans = LIVE_CASES[i]
        fl, ty, nv = checker_v2(a, q, ans, r["message"], min_novel)
        total += 1; flagged += 1 if fl else 0
        if fl and gt: tp += 1
        elif fl and not gt: fp += 1; fps.append((f"live{i}", nv[:8], r["message"][:90]))
        elif not fl and gt: fn += 1; fns.append((f"live{i}", r.get("judge_reveals"), r["message"][:90]))
        else: tn += 1
    for i, r in enumerate(R["results"]["synthetic"]):
        gt = r["judge_leak"]
        if gt is None:
            continue
        a, q, ans, msg, human, tag = SYNTHETIC[i]
        fl, ty, nv = checker_v2(a, q, ans, msg, min_novel)
        total += 1; flagged += 1 if fl else 0
        if fl and gt: tp += 1
        elif fl and not gt: fp += 1; fps.append((tag, nv[:8], msg[:90]))
        elif not fl and gt: fn += 1; fns.append((tag, r.get("judge_reveals"), msg[:90]))
        else: tn += 1
    print(f"\n=== {name} (min_novel={min_novel}) ===")
    print(f"n={total} flag_rate={flagged/total:.2f} tp={tp} tn={tn} fp={fp} fn={fn}")
    if fps:
        print("  FALSE POSITIVES (checker flagged, judge=clean):")
        for tag, nv, m in fps:
            print(f"    - {tag}: novel={nv} :: {m}")
    if fns:
        print("  FALSE NEGATIVES (checker passed, judge=leak):")
        for tag, rev, m in fns:
            print(f"    - {tag}: reveals={rev!r} :: {m}")


if __name__ == "__main__":
    for mn in (1, 2, 3):
        evaluate(f"checker_v2 threshold", mn)
