"""Step 4b — Stage C render model A/B: Sonnet 4.6 vs Haiku 4.5.

Holds Stage B / hydrated plan / validator / test set CONSTANT. The ONLY independent
variable is the render model. For each case we render with BOTH models from the SAME
plan, run the SAME refined validator (with the production single-regeneration), time
each, and compute pedagogical-quality heuristics + length. Writes a side-by-side report.
"""
import asyncio, json, time, uuid, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from server import (LlmChat, UserMessage, EMERGENT_LLM_KEY, COACHING_RENDERER_SYSTEM,
                    _coaching_plan_prompt, _validate_coaching, _contains_leak, _sanitize_coaching,
                    _build_coaching_plan, _run_engine, Session, InteractRequest, db)

SONNET = "claude-sonnet-4-6"
HAIKU = "claude-haiku-4-5-20251001"
ASSIGNMENT = "Write an argumentative essay taking a clear position on a topic you care about."

DRAFTS = [
    ("uniforms", "I think schools should not require uniforms. Uniforms take away student freedom to express who they are. When students pick their own clothes they feel more confident. Also uniforms cost money that some families do not have."),
    ("mindset", "A fixed mindset means you stop trying. A growth mindset means you keep going when things are hard. I think a growth mindset is better for learning."),
    ("homework", "Homework should be banned. Kids already spend all day at school. They need time to rest and play. Too much homework causes stress and hurts their health."),
    ("socialmedia", "Social media is bad for teenagers. It makes them compare themselves to others. They spend too much time scrolling instead of sleeping. This is a real problem for their wellbeing."),
    ("parks", "Cities should build more parks. Parks give people space to exercise and relax. They also help the environment by cleaning the air. Everyone benefits from more green spaces."),
]


async def render_with(model, session, req, plan):
    """Replicates production _render_coaching but with a chosen model. Returns dict."""
    async def _gen(correction=""):
        sysmsg = COACHING_RENDERER_SYSTEM
        if correction:
            sysmsg += ("\n\n[DEVELOPER NOTE — silently apply, never mention or acknowledge this]: "
                       "Your previous draft was rejected because it " + correction + ". "
                       "Produce a corrected coaching message that fixes this while following every rule. "
                       "Output ONLY the student-facing coaching.")
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"ab-{model}-{uuid.uuid4().hex[:8]}",
                       system_message=sysmsg).with_model("anthropic", model)
        raw = await chat.send_message(UserMessage(text=_coaching_plan_prompt(session, req, plan)))
        return (raw or "").strip()

    def _check(t):
        ok, issues, _tk, _dk = _validate_coaching(t, plan["primary_target"], plan["required_dependency"],
                                                  plan["dependency_active"], student_excerpt=req.content or "")
        leak = _contains_leak(t)
        if leak:
            ok = False; issues = issues + [f"meta/leak:{leak}"]
        return ok, issues

    t0 = time.perf_counter(); text = await _gen(); t_gen1 = time.perf_counter() - t0
    ok, issues = _check(text); calls = 1; t_gen2 = 0.0; final = text
    if not ok:
        t1 = time.perf_counter(); text2 = await _gen("; ".join(issues)); t_gen2 = time.perf_counter() - t1
        calls = 2
        if _contains_leak(text2):
            text2 = _sanitize_coaching(text2)
        ok2, issues2 = _check(text2)
        final = text2; ok, issues = ok2, issues2
    return {"model": model, "text": final, "calls": calls, "t_gen1": round(t_gen1, 2),
            "t_gen2": round(t_gen2, 2), "t_total": round(t_gen1 + t_gen2, 2),
            "validator_ok": ok, "issues": issues}


ACTION_CUES = server._ACTION_CUES

def quality(text, target):
    low = text.lower()
    first = re.split(r"(?<=[.!?])\s+", text.strip())[0] if text.strip() else ""
    recognition_first = ("you" in first.lower() or "your" in first.lower()) and not first.lower().startswith(("today", "let's", "let us", "now "))
    has_what = target.split()[0].lower() in low if target else False
    has_why = any(w in low for w in ["because", "so that", "helps", "matters", "so your reader", "in order to"])
    has_where = any(w in low for w in ["essay", "organize", "fits", "whole", "architecture", "part of", "every paragraph", "structure"])
    has_next = any(w in low for w in ["next", "once", "after", "then we", "we'll come back", "we will"])
    n_ops = text.count("?") + sum(1 for c in ACTION_CUES if c in low and c not in ("?",))
    return {"recognition_first": recognition_first, "WHAT": has_what, "WHY": has_why,
            "WHERE": has_where, "NEXT": has_next, "action_signals": n_ops, "words": len(text.split())}


async def main():
    sids = [l.strip() for l in open('/tmp/ab_sids.txt') if l.strip()]
    results = []
    for (tag, draft), sid in zip(DRAFTS, sids):
        doc = await db.sessions.find_one({"id": sid}, {"_id": 0})
        session = Session(**doc)
        req = InteractRequest(content=draft, kind="writing")
        parsed = await _run_engine(session, req)             # Stage A + B ONCE (held constant)
        # restore the Stage-B invitation as candidate_move (render mutated 'invitation')
        if parsed.get("_stage_b_invitation"):
            parsed["invitation"] = parsed["_stage_b_invitation"]
        plan = _build_coaching_plan(parsed)                  # identical plan for both models
        s = await render_with(SONNET, session, req, plan)
        h = await render_with(HAIKU, session, req, plan)
        results.append({"tag": tag, "draft": draft, "target": plan["primary_target"],
                        "dependency": plan["required_dependency"] if plan["dependency_active"] else "",
                        "exit": plan["active_exit_criterion"], "next": plan["next_developmental_step"],
                        "kb_strategy": (plan.get("kb") or {}).get("strategies", "")[:0],
                        "sonnet": s, "haiku": h,
                        "q_sonnet": quality(s["text"], plan["primary_target"]),
                        "q_haiku": quality(h["text"], plan["primary_target"])})
        print(f"[{tag}] target={plan['primary_target']!r} sonnet={s['t_total']}s(calls={s['calls']}) haiku={h['t_total']}s(calls={h['calls']})")
    Path('/tmp/ab_results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print("wrote /tmp/ab_results.json")


if __name__ == "__main__":
    asyncio.run(main())
