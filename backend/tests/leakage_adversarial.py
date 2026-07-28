"""Targeted adversarial addendum: semantic leaks that introduce NO new domain
tokens (they recombine words already in the QUESTION or the student's ANSWER,
e.g. enumerated-choice questions). These are the class the deterministic
novel-token screen structurally CANNOT catch. Ground truth = the pedagogical
Sonnet judge (the governing principle). LOG-ONLY; no production change."""
import asyncio, json
from tests.leakage_dryrun import det_check, judge

# (assignment, question, answer, message, note)
CASES = [
    ("Explain how plants get food.",
     "Do plants make their food using sunlight or soil?",
     "I'm not sure.",
     "Plants make their food using sunlight, not soil.",
     "enumerated-choice leak: answer words all appear in the question"),
    ("Explain why objects fall.",
     "Do objects fall because of gravity or because of air?",
     "I don't really know.",
     "It's because of gravity, not air — that's what pulls them down.",
     "enumerated-choice leak (+ 'pulls/down' minor)"),
    ("Identify the cause of the tides.",
     "What causes the tides — the moon or the wind?",
     "Maybe the wind?",
     "Actually it's the moon, not the wind, that causes the tides.",
     "corrects the student toward the enumerated answer, no new nouns"),
    ("Compare two governments.",
     "How do a democracy and a monarchy differ in who holds power?",
     "They are just different.",
     "In a democracy the people hold power, while in a monarchy one ruler holds power.",
     "recombines question words into the full comparison"),
    ("Explain the water cycle step.",
     "After water evaporates, does it condense or freeze to form clouds?",
     "Not sure.",
     "After it evaporates it condenses to form the clouds — it doesn't freeze.",
     "enumerated-choice leak using only question tokens"),
    # control: a genuinely CLEAN structural message on an enumerated question
    ("Explain how plants get food.",
     "Do plants make their food using sunlight or soil?",
     "I'm not sure.",
     "This question gives you two options and asks you to pick one and say why. Which of the two does your source support, and what makes you choose it?",
     "CLEAN control — teaches how to answer a choice question, reveals nothing"),
]


async def main():
    print("=== NO-NEW-TOKEN ADVERSARIAL ADDENDUM ===")
    fn = tp = fp = tn = 0
    rows = []
    for a, q, ans, msg, note in CASES:
        flagged, types, novel = det_check(a, q, ans, msg)
        j, _ = await judge(a, q, ans, msg)
        leak = j.get("leak")
        rows.append((note, flagged, types, novel, leak, j.get("reveals", "")))
        if flagged and leak: tp += 1
        elif flagged and leak is False: fp += 1
        elif not flagged and leak: fn += 1
        elif not flagged and leak is False: tn += 1
        print(f"\n- {note}")
        print(f"  MSG: {msg}")
        print(f"  det_flagged={flagged} types={types} novel={novel[:6]}")
        print(f"  JUDGE leak={leak} reveals={j.get('reveals','')!r}")
    print(f"\nSUMMARY  tp={tp} tn={tn} fp={fp} FALSE_NEGATIVES={fn}  (FN = pedagogical leaks the lexical screen missed)")
    json.dump([dict(zip(['note','det_flagged','types','novel','judge_leak','reveals'], r)) for r in rows],
              open('/app/test_reports/leakage_adversarial_addendum.json', 'w'), indent=2)


if __name__ == "__main__":
    asyncio.run(main())
