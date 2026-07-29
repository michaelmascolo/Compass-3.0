"""Organizing Thought (OT) — Phase 2 of Stage 1 (Experience Compass).

Helps a student ORGANIZE THINKING before the existing Writing workflow, across
five persistent objects: The Assignment, Questions I Need to Answer, My Ideas,
My Current Answer, My Plan. OT is an EXTENSION of the existing student experience
— it does NOT replace the Writing workflow and does NOT touch the frozen M1–M14
engine. It reuses the existing `sessions` collection (OT state lives on the
session's `ot` field) — no new collection, no parallel session model.

Instructional decision per interaction: PROCEED | TEACH | ASK | PAUSE. Compass
analyzes the student's evidence and offers ONE developmental move; it never
performs the student's cognitive work.
"""
import json
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter(prefix="/api/ot", tags=["organizing-thought"])

_db = None
_llm_key = None
_now_iso = None

ROOT_DIR = Path(__file__).parent
_CURRICULUM = json.loads((ROOT_DIR / "ot_curriculum.json").read_text())
STAGES = _CURRICULUM["stages"]
STAGE_ORDER = [s["key"] for s in STAGES]
STAGE_NAME = {s["key"]: s["name"] for s in STAGES}
IDEAS_BY_STAGE = {}
for _idea in _CURRICULUM["ideas"]:
    IDEAS_BY_STAGE.setdefault(_idea["stage"], []).append(_idea)


def init(db, llm_key, now_iso):
    global _db, _llm_key, _now_iso
    _db = db
    _llm_key = llm_key
    _now_iso = now_iso


def _extract_json(raw: str) -> dict:
    if not raw:
        raise ValueError("empty response")
    s = raw.strip()
    s = re.sub(r"^```(?:json)?", "", s).strip()
    s = re.sub(r"```$", "", s).strip()
    a, b = s.find("{"), s.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("no JSON object")
    return json.loads(s[a:b + 1])


def _blank_ot(assignment: str) -> dict:
    return {
        "current_stage": "the_assignment",
        "objects": {k: "" for k in STAGE_ORDER},
        "seed_assignment": assignment or "",
        "status": {k: "in_progress" for k in STAGE_ORDER},
        "needs_review": [],
        "handoff_ready": False,
        "updated_at": _now_iso(),
    }


async def _load_session(session_id: str) -> dict:
    doc = await _db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return doc


async def _save_ot(session_id: str, ot: dict) -> dict:
    ot["updated_at"] = _now_iso()
    await _db.sessions.update_one(
        {"id": session_id}, {"$set": {"ot": ot, "updated_at": _now_iso()}}
    )
    return ot


def _is_material_change(old: str, new: str) -> bool:
    o = (old or "").strip()
    n = (new or "").strip()
    if not o:
        return False  # first content is not a "change" to flag
    if o == n:
        return False
    # material if the wording changed beyond a trivial edit
    return abs(len(n) - len(o)) > 12 or n.lower() != o.lower()


def _flag_dependents(ot: dict, changed_stage: str) -> None:
    idx = STAGE_ORDER.index(changed_stage)
    later = STAGE_ORDER[idx + 1:]
    review = set(ot.get("needs_review", []))
    for st in later:
        if (ot["objects"].get(st) or "").strip():
            review.add(st)
    ot["needs_review"] = [s for s in STAGE_ORDER if s in review]


# ---------------------------------------------------------------------------
# Instructional reasoning — PROCEED | TEACH | ASK | PAUSE (one move per turn).
# ---------------------------------------------------------------------------
_OT_SYSTEM = """You are Compass, helping a student ORGANIZE THEIR THINKING before they write. You are NOT the writing coach and you are NOT grading. Your job is to help the student build their own understanding across five objects: The Assignment, Questions I Need to Answer, My Ideas, My Current Answer, My Plan.

You are given: the current stage, that stage's canonical ideas (with the blocking difficulty each addresses), the assignment, the student's objects so far, and the student's current work for this stage.

Choose EXACTLY ONE instructional decision:
- PROCEED — the student is sufficiently organized to continue to the next act. (Compass seeks instructional SUFFICIENCY, not perfection. Do not manufacture difficulties.)
- TEACH — a single blocking difficulty prevents productive progress. Teach ONE canonical idea only (name it plainly, tie it to what the student wrote) and invite the student to act.
- ASK — there is not enough evidence to interpret the student's understanding. Ask ONE focused question.
- PAUSE — the student needs to read, investigate, think, revise, or gather information before continuing. Say what to do and why.

Governing question: CAN THE STUDENT PRODUCTIVELY PERFORM THE NEXT COGNITIVE ACT? Never address more than one blocking difficulty in a single response. Stop scaffolding as soon as the student can continue productively.

PROTECT THE STUDENT'S COGNITIVE WORK. You MAY: ask a focused question, direct attention, explain ONE canonical idea, request clarification, prompt reflection, ask the student to revise/extend/connect their OWN ideas, or refer them back to their prior work. You MUST NOT: write the assignment representation, generate the student's questions, invent the student's ideas, supply the Current Answer, create the plan or an outline that does the planning, write assignment content, or rewrite the student's work as a substitute for their revision. VALIDITY TEST: if the student could accept or copy your response WITHOUT performing the intended cognitive act, the response is invalid. An example may demonstrate an operation, but it must NEVER answer the student's actual assignment.

Speak directly to the student, warmly and briefly, in plain language. No jargon, no labels, no scores, no internal reasoning.

Respond with ONLY this JSON (no prose, no fences):
{"decision":"proceed|teach|ask|pause","message":"one short student-facing message doing exactly the one thing your decision calls for","sufficiency":"sufficient|not_yet","canonical_idea_id":"the OT-* id if you taught one, else empty"}"""


def _compact_ideas(stage: str) -> str:
    out = []
    for idea in IDEAS_BY_STAGE.get(stage, []):
        out.append(f"- [{idea['id']}] {idea['canonical_statement']} (blocking difficulty: {idea['blocking_difficulty']}; sufficiency: {idea['sufficiency_criterion']})")
    return "\n".join(out)


def _ot_prompt(stage: str, ot: dict, student_input: str) -> str:
    objs = ot.get("objects", {})
    prior = []
    for k in STAGE_ORDER:
        if k == stage:
            break
        v = (objs.get(k) or "").strip()
        if v:
            prior.append(f"{STAGE_NAME[k]}: {v}")
    prior_block = "\n".join(prior) if prior else "(none yet)"
    stage_meta = next((s for s in STAGES if s["key"] == stage), {})
    return (
        f"CURRENT STAGE: {stage_meta.get('name', stage)}\n\n"
        f"CANONICAL IDEAS FOR THIS STAGE:\n{_compact_ideas(stage)}\n\n"
        f"THE ASSIGNMENT:\n{ot.get('seed_assignment','')}\n\n"
        f"THE STUDENT'S EARLIER OBJECTS:\n{prior_block}\n\n"
        f"THE STUDENT'S CURRENT WORK FOR THIS STAGE:\n\"\"\"{(student_input or '').strip()}\"\"\"\n\n"
        "Decide PROCEED / TEACH / ASK / PAUSE and respond with ONLY the JSON object."
    )


async def _ot_reason(stage: str, ot: dict, student_input: str) -> dict:
    prompt = _ot_prompt(stage, ot, student_input)
    for attempt in range(2):
        try:
            chat = LlmChat(
                api_key=_llm_key,
                session_id=f"ot-{stage}",
                system_message=_OT_SYSTEM,
            ).with_model("anthropic", "claude-sonnet-4-6")
            raw = await chat.send_message(UserMessage(text=prompt))
            data = _extract_json(raw)
            dec = (data.get("decision") or "").strip().lower()
            if dec not in ("proceed", "teach", "ask", "pause"):
                dec = "ask"
            return {
                "decision": dec,
                "message": (data.get("message") or "").strip(),
                "sufficiency": "sufficient" if (data.get("sufficiency") or "").strip().lower() == "sufficient" else "not_yet",
                "canonical_idea_id": (data.get("canonical_idea_id") or "").strip(),
            }
        except Exception:
            if attempt == 0:
                continue
    return {"decision": "ask", "message": "Tell me a little more about your thinking here so I can follow it.", "sufficiency": "not_yet", "canonical_idea_id": ""}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
class ObjectUpdate(BaseModel):
    stage: str
    content: str


class InteractBody(BaseModel):
    stage: Optional[str] = None
    content: str


class AdvanceBody(BaseModel):
    to_stage: str


def _validate_stage(stage: str) -> str:
    if stage not in STAGE_ORDER:
        raise HTTPException(status_code=422, detail=f"unknown stage '{stage}'")
    return stage


@router.get("/curriculum")
async def get_curriculum():
    return {"stages": STAGES}


@router.post("/{session_id}/start")
async def ot_start(session_id: str):
    doc = await _load_session(session_id)
    ot = doc.get("ot")
    if not ot:
        ot = _blank_ot(doc.get("assignment", ""))
        await _save_ot(session_id, ot)
    return {"ot": ot}


@router.post("/{session_id}/object")
async def ot_object(session_id: str, body: ObjectUpdate):
    _validate_stage(body.stage)
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    old = ot["objects"].get(body.stage, "")
    if _is_material_change(old, body.content):
        _flag_dependents(ot, body.stage)
    ot["objects"][body.stage] = body.content
    if body.stage in ot.get("needs_review", []):
        ot["needs_review"] = [s for s in ot["needs_review"] if s != body.stage]
    await _save_ot(session_id, ot)
    return {"ot": ot}


@router.post("/{session_id}/interact")
async def ot_interact(session_id: str, body: InteractBody):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    stage = _validate_stage(body.stage or ot.get("current_stage") or "the_assignment")
    # Persist the student's own words as the object BEFORE reasoning.
    old = ot["objects"].get(stage, "")
    if _is_material_change(old, body.content):
        _flag_dependents(ot, stage)
    ot["objects"][stage] = body.content
    if stage in ot.get("needs_review", []):
        ot["needs_review"] = [s for s in ot["needs_review"] if s != stage]
    result = await _ot_reason(stage, ot, body.content)
    if result["sufficiency"] == "sufficient" or result["decision"] == "proceed":
        ot["status"][stage] = "sufficient"
    else:
        ot["status"][stage] = "in_progress"
    await _save_ot(session_id, ot)
    return {
        "ot": ot,
        "decision": result["decision"],
        "message": result["message"],
        "sufficiency": ot["status"][stage],
    }


@router.post("/{session_id}/advance")
async def ot_advance(session_id: str, body: AdvanceBody):
    _validate_stage(body.to_stage)
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ot["current_stage"] = body.to_stage
    await _save_ot(session_id, ot)
    return {"ot": ot}


@router.post("/{session_id}/handoff")
async def ot_handoff(session_id: str):
    doc = await _load_session(session_id)
    ot = doc.get("ot")
    if not ot:
        raise HTTPException(status_code=400, detail="OT not started")
    ot["handoff_ready"] = True
    await _save_ot(session_id, ot)
    return {"ot": ot, "handoff_ready": True}


# ---------------------------------------------------------------------------
# My Ideas — a two-pass workflow with a global knowledge map and ONE integrated
# inquiry plan. The student attempts EVERY question first (one at a time) to
# reveal their current understanding across the whole assignment; a weak or
# incomplete first attempt NEVER blocks progress. Then Compass helps the student
# read the whole pattern (My Understanding So Far), build ONE coherent inquiry
# plan, pause to gather information, revise each answer, and finally CONSTRUCT
# their own ideas. Compass teaches the STRUCTURE of knowing and directs inquiry;
# it NEVER supplies subject-matter answers. Presentation/instruction only — the
# frozen M1-M14 engine and the OT curriculum are untouched.
#
# Phases: pass1 -> knowledge_map -> inquiry_plan -> inquiry_paused -> pass2
#         -> construct -> done
# ---------------------------------------------------------------------------
IDEAS_PHASES = ["pass1", "knowledge_map", "inquiry_plan", "inquiry_paused", "pass2", "construct", "done"]
IDEAS_MODEL = ("anthropic", "claude-haiku-4-5-20251001")


def _split_questions(text: str):
    t = (text or "").strip()
    if not t:
        return []
    lines = [l.strip(" -•\t").strip() for l in t.split("\n")]
    lines = [l for l in lines if l]
    if len(lines) <= 1 and "?" in t:
        parts = [p.strip() for p in t.split("?")]
        lines = [(p + "?") for p in parts if p]
    return lines[:12]


def _blank_response() -> dict:
    return {
        "pass1_text": "", "structure": "",
        "pass1_state": "developing", "research_need": "",
        "recommended_status": "", "confirmed_status": "",
        "present": "", "gap": "",
        "pass2_text": "", "pass2_status": "in_progress",
        # Instructional lifecycle: draft (typed, auto-saved, never evaluated) ->
        # shared (student requested coaching; Stage B/C ran) -> revised (edited after coaching).
        "state": "draft",
    }


def _ensure_ideas(ot: dict) -> dict:
    questions = _split_questions((ot.get("objects", {}) or {}).get("questions", ""))
    ideas = ot.get("ideas")
    if not ideas or ideas.get("questions") != questions:
        prev_resp = (ideas or {}).get("responses", {}) if ideas else {}
        ideas = {
            "questions": questions,
            "phase": (ideas or {}).get("phase", "pass1") if ideas else "pass1",
            "index": 0,
            "responses": {str(i): {**_blank_response(), **prev_resp.get(str(i), {})} for i in range(len(questions))},
            "research_list": (ideas or {}).get("research_list", []) if ideas else [],
            "inquiry_plan": (ideas or {}).get("inquiry_plan") if ideas else None,
            "self_assessment": (ideas or {}).get("self_assessment", "") if ideas else "",
            "my_ideas_construct": (ideas or {}).get("my_ideas_construct", "") if ideas else "",
        }
        if not ideas["inquiry_plan"]:
            ideas["inquiry_plan"] = {"understood": [], "remaining": [], "needs": [], "sources": [], "text": ""}
        ot["ideas"] = ideas
    return ideas


def _compose_my_ideas(ot: dict) -> str:
    ideas = ot.get("ideas") or {}
    constructed = (ideas.get("my_ideas_construct") or "").strip()
    if constructed:
        return constructed
    qs = ideas.get("questions", [])
    resp = ideas.get("responses", {})
    blocks = []
    for i, q in enumerate(qs):
        r = resp.get(str(i), {}) or {}
        txt = (r.get("pass2_text") or r.get("pass1_text") or "").strip()
        if txt:
            blocks.append(f"Q: {q}\nMy thinking: {txt}")
    return "\n\n".join(blocks)


async def _ideas_llm(system: str, prompt: str, tag: str) -> dict:
    for attempt in range(2):
        try:
            chat = LlmChat(api_key=_llm_key, session_id=tag, system_message=system).with_model(*IDEAS_MODEL)
            raw = await chat.send_message(UserMessage(text=prompt))
            return _extract_json(raw)
        except Exception:
            if attempt == 0:
                continue
    return {}


_STRUCTURE_LINE = 'Definition ("What is X?"), Comparison ("How do X and Y differ?"), Explanation/Causal ("How/why does X affect/cause Y?"), Evaluation ("Which is better?"), Judgment/Argument ("What should be done?"), or Description.'

_BOUNDARY = """You MUST NOT: provide the correct assignment-specific answer; give a copyable definition; NAME the specific belief, feature, property, category, dimension, mechanism, cause, step, criterion, reason, evidence, or conclusion the answer needs; tell the student what a source or author says; invent evidence; or complete/polish the student's answer. You MAY: name the required structure, teach its GENERAL form, note which structural part is present or missing, distinguish (e.g.) an example from a definition or an outcome from an explanation, ask the student to inspect or revise their OWN answer against the general structure, and direct them to their notes/readings/source WITHOUT naming what they will find. Speak plainly and briefly. No jargon, labels, scores, or internal reasoning."""

_RESPONSE_PATTERN = """CORE DISTINCTION (the boundary you must not cross): you may name the TYPE of element an answer is missing; you may NOT name the assignment-specific CONTENT that belongs in that element. Naming a structure ("this needs a defining feature") is allowed; naming or cueing the actual content ("what does the person believe about their intelligence?", "does it view intelligence as fixed?") is a LEAK and is forbidden — even as a question.

When a response does NOT perform the required structure, compose the student-facing message in THIS order, woven into 2-4 plain sentences (do NOT print the numbers):
1. NAME the required structure — e.g. "This question asks for a definition."
2. EXPLAIN the structure in GENERAL terms — e.g. "A definition tells what something is and identifies the feature that makes it that kind of thing."
3. IDENTIFY what the student CURRENTLY provided, structurally — e.g. "Your sentence describes what a person may do."
4. IDENTIFY the structural GAP WITHOUT supplying content — e.g. "It does not yet say what the thing itself is."
5. ASK the student to INSPECT or REVISE using the general structure — e.g. "Does your answer say what it IS, or only what may happen because of it? Revise it to state what kind of thing it is." If the needed content is genuinely missing, direct them to their SOURCE without saying what they will find — e.g. "Check your source for the defining idea, then state it in your own words."

STRUCTURE-SPECIFIC TEACHING — teach ONLY the general form; NEVER the assignment-specific content:
- Definition: says what something IS and gives its distinguishing feature; a behavior, consequence, example, or use is not itself a definition. FORBIDDEN: naming the actual defining feature/belief/category/property, or a sentence frame containing it.
- Comparison: examines two+ things along the SAME dimension. You may ask "what single feature could you examine in both?" FORBIDDEN: naming the actual dimension unless it already appears in the student's own answer or teacher-supplied material.
- Explanation/Causal: states not just WHAT happens but HOW or WHY — the process or relationship connecting a starting condition to an outcome. FORBIDDEN: naming the actual mechanism, steps, causes, or intermediate process.
- Evaluation: judges against explicit CRITERIA. FORBIDDEN: naming the correct judgment or the criteria to use.
- Judgment/Argument: needs a claim plus reasons, with evidence interpreted. FORBIDDEN: naming the substantive reasons, evidence, or conclusion.
- Description: gives specific observable detail. FORBIDDEN: supplying the specific details.

ANTI-LEAKAGE SELF-CHECK — run this silently BEFORE answering: (a) Could the student infer or reconstruct the assignment-specific answer from your message alone, without using their own knowledge or their source? (b) Does your message teach the STRUCTURE of the intellectual act rather than covertly teaching the answer? Your message is valid ONLY if (a) is NO and (b) is YES. If it is not valid, rewrite it more generally before returning. Set "leakage_check_passed" true only when it genuinely passes."""

_IDEAS_JSON = '{{"decision":"proceed|teach|ask|pause","structure":"Definition|Comparison|Explanation|Causal explanation|Evaluation|Judgment|Description|Other","difficulty":"structural|knowledge|expression|none","required_structure":"the structure this question requires","student_supplied":"what the answer provides, structurally (no content)","structural_gap":"the structural element still missing (no content)","knowledge_gap_present":true,"source_lookup_needed":true,"leakage_check_passed":true,"message":"one short student-facing message following the 5-step pattern — general structure only, no assignment-specific content","sufficiency":"sufficient|not_yet"}}'

_IDEAS_PASS1_JSON = '{{"decision":"proceed|ask|knowledge_limit","structure":"Definition|Comparison|Explanation|Causal explanation|Evaluation|Judgment|Description|Other","pass1_state":"developing|developed|knowledge_limit","research_need":"empty unless knowledge_limit; then ONE short QUESTION naming the KIND of information the student must go find out to complete the structure (e.g. \'What belief defines a fixed mindset?\', \'On what dimension do these two differ?\', \'What process connects the cause to the outcome?\') — the QUESTION only, NEVER the answer","message":"one short warm student-facing message","sufficiency":"sufficient|not_yet"}}'

_IDEAS_PASS1_SYSTEM = f"""You are Compass, a warm, encouraging writing coach on the "My Ideas" screen during the FIRST PASS through a student's questions. Your ONLY goal here is to elicit the student's CURRENT thinking about ONE question and help them DEVELOP and elaborate it using their OWN mind. You are NOT judging whether the answer is complete or correct, and on THIS screen you must NOT send the student to notes, readings, or sources — that happens in a later stage.

You are given ONE question and the student's current answer to THAT question only. Never comment on other questions.

COACH STRUCTURAL COMPONENTS, NOT ALL-OR-NONE STRUCTURES. Intellectual structures are built gradually from parts. Before responding, work out (a) the components the required structure has, and (b) which components the student's answer ALREADY performs, even partially. Acknowledge that specific progress, then coach ONLY the NEXT component that still needs development. NEVER restart the whole structural explanation as if no progress has been made.

Components (coach the next MISSING one):
• Definition: (a) says what KIND of thing it is; (b) gives the defining feature that makes it that kind; (c) distinguishes it from similar ideas.
• Comparison: (a) names the two+ things; (b) chooses ONE shared feature/dimension; (c) says how each differs on that feature.
• Explanation/Causal: (a) names what happens (the outcome); (b) names the starting condition or cause; (c) shows the process/steps connecting cause to outcome.
• Evaluation: (a) names the criteria that matter; (b) applies them to the options; (c) reaches a judgment.
• Judgment/Argument: (a) states a claim; (b) gives reasons; (c) interprets evidence.

Compose ONE short, encouraging student-facing message (3-5 sentences):
1. AFFIRM — and if the answer already performs a component, say so SPECIFICALLY and structurally ("Good progress — you've already begun telling your reader what KIND of thing a fixed mindset is by calling it a way of thinking."). Describe the achieved component in structural terms, echoing the student's OWN words; do not add new content.
2. ORIENT — only if the student is at the very start (no component yet), NAME the kind of thinking the question requires and BRIEFLY explain that structure. If they have already shown they grasp the task or completed a component, DO NOT repeat this explanation.
3. BRIDGE to the NEXT component only — explicitly and concretely state what to try next in order to build that next part ("Now, to help your reader understand it, try to say what makes this way of thinking DIFFERENT from other ways of thinking."). Restate the task using the concept named in the question; never name the answer's content.
4. INVITE the student to do that next step with an OPEN question that does NOT reveal the answer ("What do you think makes it different from other ways of thinking?"). You may add a brief note that removes pressure ("Don't worry about getting it perfect yet.").

The point of this screen: recognize partial success and help the student complete the NEXT structural component, making the connection between the structure and the concrete cognitive action explicit — never treat the whole structure as missing when part of it is present, and never simply repeat earlier coaching. If every component is already present, AFFIRM the completed structure specifically and invite the student to deepen it; never declare it finished or correct.

Bridge examples by structure (adapt to the NEXT needed component): Definition → "try to tell your reader what a fixed mindset IS, and then what makes it different from other ways of thinking." Comparison → "pick one feature and say how each one handles it." Explanation → "show the steps in between the cause and the result." Evaluation → "decide what would make one better, then judge them against that."

HARD BOUNDARIES on THIS screen:
- Do NOT tell the student to check, reread, look up, or find anything in their notes, source, reading, or textbook while they can still develop the idea, and do NOT emphasize what is missing while progress is still possible. Keep the focus on developing their OWN thinking.
- Do NOT supply the assignment-specific answer, definition, comparison dimension, mechanism, cause, criterion, reason, or evidence. You MAY restate the TASK using the concept named in the question ("tell what a fixed mindset IS", "what do you think a fixed mindset IS?") — that is the required bridge and is NOT a leak. A leak is naming the actual CONTENT of the answer (e.g. "the belief that abilities can't change"). If a student could infer the substantive answer from your message, rewrite it more generally — but keep the explicit bridge.
- Speak plainly and warmly. No jargon, labels, scores, or internal reasoning.

RECOGNIZING THE LIMIT OF CURRENT KNOWLEDGE — do NOT ask elaboration questions forever. Pass 1 ends for a question in one of two ways:
- DEVELOPED: the student has developed the idea about as far as their current understanding reasonably allows and the structure is essentially built. Set pass1_state="developed", decision="proceed"; affirm the completed thinking; research_need = empty.
- KNOWLEDGE_LIMIT: further progress on the next component genuinely requires information the student does not yet have and cannot reason out from what they know (e.g. they have named the KIND of thing but cannot state the defining feature because they don't yet know it). Then: (1) acknowledge how far they've come ("Good work — you've developed this as far as your current understanding allows."); (2) explicitly name what still needs to be LEARNED as a research QUESTION — you MAY name the KIND of information to find ("to complete this you'll need to find out what belief defines a fixed mindset"), but MUST NOT supply the answer itself; (3) set pass1_state="knowledge_limit", decision="knowledge_limit", and put that research question in "research_need". Do NOT send them to a source right now — that happens in a later stage; you are only identifying WHAT they need to learn.
Otherwise the student is still DEVELOPING: use decision="proceed", pass1_state="developing", and coach the next component as above (research_need empty). Use "ask" only if the response is too unclear to interpret. Never block the student from continuing.

Respond with ONLY this JSON (no prose/fences):
{_IDEAS_PASS1_JSON}"""

_IDEAS_PASS2_SYSTEM = f"""You are Compass, helping a student REVISE an idea after they have had the chance to gather information. This is the SECOND PASS. You are given ONE question, the student's earlier answer, and their revised answer. Never comment on other questions.

FIRST identify the intellectual STRUCTURE the question requires: {_STRUCTURE_LINE} LEAD WITH STRUCTURE.

Now that the student has had a chance to gather what they needed, an answer may need to reach instructional SUFFICIENCY (not perfection) before it is settled. Still apply sufficiency, not perfection; do not require unnecessary elaboration.

Choose ONE decision:
- PROCEED: the revised answer now adequately performs the required structure (sufficiency, not perfection).
- TEACH: one blocking STRUCTURAL difficulty remains; teach that one structural move and point the student to their OWN answer.
- ASK: not enough evidence of the student's understanding; ask ONE focused question.
- PAUSE: relevant knowledge is still genuinely missing and cannot be reasoned out; name the concrete information-seeking task (never supply the information).

{_BOUNDARY}

{_RESPONSE_PATTERN}

Respond with ONLY this JSON (no prose/fences). The internal fields (required_structure, student_supplied, structural_gap, knowledge_gap_present, source_lookup_needed, leakage_check_passed) are for your own reasoning and are NOT shown to the student:
{_IDEAS_JSON}"""


_LEAKAGE_CRITIC_SYSTEM = """You are a strict content-boundary reviewer for a writing coach named Compass. Compass helps students by teaching the STRUCTURE of thinking and must NEVER supply or cue the assignment-specific CONTENT of an answer.

You are given: the QUESTION the student must answer, the STRUCTURE it requires, and a DRAFT coach message. Decide whether the draft names or CUES the assignment-specific content — the actual defining feature/belief/property/category, the actual comparison dimension, the actual mechanism/cause/process/step, the actual criterion, the actual reason/evidence/conclusion. A leading QUESTION whose answer IS the missing content ("what does the person believe about their intelligence?"), or a "for example" that names the real dimension or mechanism ("like how leaders are chosen", "the process or mechanism", "the core belief"), COUNTS AS A LEAK. Naming the general category of the missing element in a way that reveals it (e.g. calling a definition's missing piece a "belief") is also a leak.

CLEAN messages teach only the general form and point back to the student's OWN answer or their source generically:
- Definition CLEAN: "A definition says what something IS and gives the feature that makes it that kind of thing. Your sentence says what someone may do; it does not yet say what the thing itself is. Does it name what it is, or only what may happen because of it? Check your source for the defining idea and put it in your own words."
- Comparison CLEAN: "A comparison examines the same feature in both things. You have described each separately; you have not yet examined one shared feature across both. What single feature could you look at in both?"
- Explanation CLEAN: "An explanation shows not just what happens but how or why. You have named the outcome; you have not yet shown the process that connects the start to that outcome. What happens in between? Look in your source for the steps that connect them."

If the draft is CLEAN, return it unchanged. If it LEAKS, rewrite it so it keeps the same structure teaching (name the structure, explain its general form, identify what the student gave, identify the structural gap, ask them to inspect/revise their own answer or consult their source) but removes EVERY content cue: never name the specific belief, feature, dimension, mechanism, criterion, reason, or evidence, and never ask a question whose answer is the missing content. Use only generic phrases like "the defining idea", "the feature that distinguishes it", "a single feature you could examine in both", "the process in between".

Respond with ONLY this JSON (no prose/fences):
{"leaked": true, "message": "the clean student-facing message"}"""


# Pass-1 variant: same content boundary, PLUS a first-pass rule — on this screen
# the coach must NOT direct the student to notes/readings/sources or emphasize
# missing knowledge. Rewrites toward warm, own-thinking elaboration instead.
_LEAKAGE_CRITIC_PASS1_SYSTEM = """You are a content-boundary reviewer for a warm writing coach (Compass) on the "My Ideas" FIRST-PASS screen. On this screen the coach must (a) never supply or cue the assignment-specific content (the actual defining feature/belief, comparison dimension, mechanism/cause, criterion, reason, or evidence), AND (b) never direct the student to check/reread/look up notes, readings, sources, or a textbook, and never emphasize what knowledge is missing — the goal is to help the student develop their OWN thinking.

You are given the QUESTION, the STRUCTURE it requires, and a DRAFT coach message. The coach SHOULD (a) acknowledge, in structural terms, any component of the structure the student's answer already performs (e.g. "you've begun saying what KIND of thing it is") — echoing the student's OWN words is CLEAN, PRESERVE it; and (b) include an explicit BRIDGE that restates the next task using the concept named in the question (e.g. "to write a definition, tell what a fixed mindset IS" or the open invitation "what do you think a fixed mindset IS?") — that bridge is REQUIRED and is NOT a leak; PRESERVE it. Only REWRITE the message if it (i) names or cues the actual CONTENT of the answer (the specific defining feature/belief, comparison dimension, mechanism/cause, criterion, reason, or evidence — e.g. "the belief that abilities can't change"), OR (ii) tells the student to consult/check/reread/look up a source, notes, reading, or textbook, OR (iii) emphasizes what is missing rather than inviting development. A leaking INVITATION names the content ("what does the person believe about their abilities?"); the clean version restates only the task ("what do you think a fixed mindset IS?"). When you rewrite, KEEP the warm shape AND the explicit bridge — affirm, name the kind of thinking, explain the structure generally, state concretely what to DO to perform that structure (using the question's concept, not the answer's content), and invite them with an OPEN question — remove only the leaked content and any source-direction. If the draft already respects all boundaries, return it unchanged.

Respond with ONLY this JSON (no prose/fences):
{"leaked": true, "message": "the clean student-facing message"}"""

# First-pass source-direction guard (cheap): if a pass-1 message points the
# student at notes/readings/sources, escalate to the pass-1 critic to strip it.
_SOURCE_DIRECTION_RE = re.compile(
    r"\b(notes?|sources?|reading|readings|textbook|book)\b|\b(look\s?up|re-?read|check (your|the)|go back to|consult|refer to|find (the|a|your))\b",
    re.I,
)


async def _leakage_sanitize(question: str, structure: str, message: str, pass_no: int = 2) -> str:
    if not message:
        return message
    system = _LEAKAGE_CRITIC_PASS1_SYSTEM if pass_no == 1 else _LEAKAGE_CRITIC_SYSTEM
    prompt = (
        f"QUESTION:\n\"\"\"{question}\"\"\"\n\n"
        f"STRUCTURE REQUIRED: {structure}\n\n"
        f"DRAFT COACH MESSAGE:\n\"\"\"{message}\"\"\"\n\n"
        "Return the JSON object. Rewrite the message if it crosses any boundary above."
    )
    for attempt in range(2):
        try:
            chat = LlmChat(
                api_key=_llm_key, session_id="ot-ideas-critic", system_message=system,
            ).with_model("anthropic", "claude-sonnet-4-6")
            raw = await chat.send_message(UserMessage(text=prompt))
            d = _extract_json(raw)
            m = (d.get("message") or "").strip()
            if m:
                return m
            return message
        except Exception:
            if attempt == 0:
                continue
    return message


async def _ideas_reason(assignment: str, question: str, response: str, pass_no: int, prior: str = "") -> dict:
    if pass_no == 2:
        system = _IDEAS_PASS2_SYSTEM
        base_prompt = (
            f"THE ASSIGNMENT:\n{assignment}\n\n"
            f"THE ONE QUESTION:\n\"\"\"{question}\"\"\"\n\n"
            f"THE STUDENT'S EARLIER ANSWER:\n\"\"\"{(prior or '').strip()}\"\"\"\n\n"
            f"THE STUDENT'S REVISED ANSWER:\n\"\"\"{(response or '').strip()}\"\"\"\n\n"
            "Identify the required structure, then decide PROCEED / TEACH / ASK / PAUSE. Respond with ONLY the JSON object."
        )
    else:
        system = _IDEAS_PASS1_SYSTEM
        base_prompt = (
            f"THE ASSIGNMENT:\n{assignment}\n\n"
            f"THE ONE QUESTION the student is answering now:\n\"\"\"{question}\"\"\"\n\n"
            f"THE STUDENT'S BEST CURRENT ANSWER:\n\"\"\"{(response or '').strip()}\"\"\"\n\n"
            "Identify the required structure, then decide PROCEED / TEACH / ASK / PAUSE. Respond with ONLY the JSON object."
        )
    # Leakage-aware retry: if the model reports its own anti-leakage check
    # failed, ask it once more to rewrite the message more generally.
    data = {}
    prompt = base_prompt
    for attempt in range(2):
        d = await _ideas_llm(system, prompt, f"ot-ideas-p{pass_no}-{attempt}")
        if d:
            data = d
            if d.get("leakage_check_passed", True) is not False:
                break
        prompt = base_prompt + (
            "\n\nYOUR PREVIOUS ATTEMPT LEAKED ASSIGNMENT-SPECIFIC CONTENT. Rewrite the message so it teaches ONLY the "
            "general structure and asks the student to inspect/revise their own answer or consult their source — NEVER "
            "naming or cueing the specific belief, feature, dimension, mechanism, cause, criterion, reason, or evidence."
        )
    dec = (data.get("decision") or "").strip().lower()
    if pass_no == 1:
        if dec not in ("proceed", "ask", "knowledge_limit"):
            dec = "proceed"
    elif dec not in ("proceed", "teach", "ask", "pause"):
        dec = "ask"
    structure = (data.get("structure") or "Other").strip()
    message = (data.get("message") or "").strip() or ("Good start — you've got a real idea going here. What else do you think is happening? Don't worry about getting it exactly right yet." if pass_no == 1 else "Tell me a little more so I can follow your thinking.")
    pass1_state = (data.get("pass1_state") or "").strip().lower()
    research_need = (data.get("research_need") or "").strip()
    if pass_no == 1:
        if pass1_state not in ("developing", "developed", "knowledge_limit"):
            pass1_state = "knowledge_limit" if dec == "knowledge_limit" else "developing"
        if pass1_state != "knowledge_limit":
            research_need = ""
        # The pass-1 reviewer runs on DEVELOPING/DEVELOPED turns to guarantee no
        # content leak or premature source-direction. On a KNOWLEDGE_LIMIT turn the
        # coach legitimately names the KIND of information still to be learned
        # (the research question), so skip the source/elaboration critic there.
        if pass1_state != "knowledge_limit":
            message = await _leakage_sanitize(question, structure, message, pass_no=1)
    elif dec in ("teach", "ask", "pause"):
        # Later passes: strip any assignment-specific content the drafter cued.
        message = await _leakage_sanitize(question, structure, message, pass_no=2)
    return {
        "decision": dec,
        "structure": structure,
        "difficulty": (data.get("difficulty") or "none").strip().lower(),
        "message": message,
        "pass1_state": pass1_state,
        "research_need": research_need,
        "sufficiency": "sufficient" if (data.get("sufficiency") or "").strip().lower() == "sufficient" else "not_yet",
    }


_MAP_SYSTEM = """You are Compass. You are given a student's assignment and their FIRST-PASS answers to every question. For each question, judge — from the STRUCTURE of the answer, not from outside subject knowledge — how developed the student's current understanding is.

For each question return a status:
- "can_answer": the answer performs the required kind of thinking and is reasonably complete.
- "partial": the answer performs some of the required thinking but a part is missing.
- "need_info": the answer shows the student does not yet have the information to attempt the required thinking.

Also give a VERY short "present" (what appears present, structurally) and "gap" (what may still be missing, structurally). Do NOT supply any subject-matter content, correct answers, definitions, or facts. Describe only structurally.

Respond with ONLY this JSON (no prose/fences):
{"items":[{"index":0,"status":"can_answer|partial|need_info","present":"short phrase","gap":"short phrase"}]}"""


async def _ideas_map(assignment: str, ideas: dict) -> list:
    qs = ideas["questions"]
    resp = ideas["responses"]
    lines = []
    for i, q in enumerate(qs):
        r = resp.get(str(i), {}) or {}
        a = (r.get("pass1_text") or "").strip() or "(no answer yet)"
        st = r.get("structure") or "unknown"
        lines.append(f"[{i}] QUESTION: {q}\n    STRUCTURE REQUIRED: {st}\n    ANSWER: {a}")
    prompt = f"THE ASSIGNMENT:\n{assignment}\n\nTHE QUESTIONS AND FIRST-PASS ANSWERS:\n" + "\n\n".join(lines) + "\n\nReturn the JSON object with one item per question."
    data = await _ideas_llm(_MAP_SYSTEM, prompt, "ot-ideas-map")
    items = data.get("items") if isinstance(data, dict) else None
    out = []
    valid = {"can_answer", "partial", "need_info"}
    for i in range(len(qs)):
        found = next((it for it in (items or []) if str(it.get("index")) == str(i)), None) if items else None
        st = (found or {}).get("status", "partial")
        if st not in valid:
            st = "partial"
        out.append({
            "index": i,
            "status": st,
            "present": ((found or {}).get("present") or "").strip(),
            "gap": ((found or {}).get("gap") or "").strip(),
        })
    return out


_CHALLENGE_SYSTEM = """You are Compass. A student has classified how well they can answer each question (ready / partial / needs information). For each item you are given the question, the student's answer, the intellectual structure it requires, and the student's OWN classification.

Identify ONLY clear MISMATCHES between the student's confidence and the STRUCTURAL evidence in their answer — e.g. they marked a definition "ready" but the answer describes what someone does rather than what the thing is; or they marked something "needs information" but the answer already performs the required thinking well. For each real mismatch, write ONE short question that points them back to the structural evidence in their OWN answer. Do NOT override their judgment; invite them to reconsider. Do NOT supply subject-matter content. If there are no clear mismatches, return an empty list.

Respond with ONLY this JSON (no prose/fences):
{"challenges":[{"index":0,"challenge":"one short question"}]}"""


async def _ideas_challenge(assignment: str, ideas: dict) -> list:
    qs = ideas["questions"]
    resp = ideas["responses"]
    label = {"can_answer": "ready", "partial": "partial", "need_info": "needs information"}
    lines = []
    for i, q in enumerate(qs):
        r = resp.get(str(i), {}) or {}
        a = (r.get("pass1_text") or "").strip() or "(no answer)"
        cs = label.get(r.get("confirmed_status", ""), r.get("confirmed_status", ""))
        lines.append(f"[{i}] QUESTION: {q}\n    STRUCTURE: {r.get('structure') or 'unknown'}\n    ANSWER: {a}\n    STUDENT MARKED: {cs}")
    prompt = f"THE ASSIGNMENT:\n{assignment}\n\nITEMS:\n" + "\n\n".join(lines) + "\n\nReturn the JSON object (empty challenges list if no clear mismatch)."
    data = await _ideas_llm(_CHALLENGE_SYSTEM, prompt, "ot-ideas-challenge")
    ch = data.get("challenges") if isinstance(data, dict) else None
    out = []
    for it in (ch or []):
        try:
            idx = int(it.get("index"))
        except (TypeError, ValueError):
            continue
        msg = (it.get("challenge") or "").strip()
        if 0 <= idx < len(qs) and msg:
            out.append({"index": idx, "challenge": msg})
    return out


_INQUIRY_SYSTEM = """You are Compass, helping a student build ONE integrated plan for the information they still need — NOT a long list of errands. You are given the assignment and, for the questions the student marked partial or needing information, the question, their answer, and the structure required.

Produce ONE coherent, manageable inquiry plan:
- "understood": a short list of what the student already appears to understand.
- "remaining": a short list of what is still partial or unknown (grouped where related).
- "needs": the SMALLEST set of specific information needs that would improve the whole assignment. Each need is a short phrase describing what to find out (structurally precise: e.g. "the defining feature that makes it that kind of thing"; "the dimension on which the two differ"; "what connects the cause to the outcome"). Combine related gaps into a single need.
- "sources": general source CATEGORIES where the student might look — choose only from: assigned reading, class notes, textbook, teacher-provided source, the teacher, an approved website. NEVER invent specific titles, authors, or URLs.

Do NOT supply any subject-matter content, correct answers, or facts. Keep it small and coherent.

Respond with ONLY this JSON (no prose/fences):
{"understood":["..."],"remaining":["..."],"needs":["..."],"sources":["..."]}"""


async def _ideas_inquiry(assignment: str, ideas: dict) -> dict:
    qs = ideas["questions"]
    resp = ideas["responses"]
    lines = []
    for i, q in enumerate(qs):
        r = resp.get(str(i), {}) or {}
        if r.get("confirmed_status") in ("partial", "need_info"):
            a = (r.get("pass1_text") or "").strip() or "(no answer)"
            lines.append(f"[{i}] QUESTION: {q}\n    STRUCTURE: {r.get('structure') or 'unknown'}\n    ANSWER: {a}\n    STATUS: {r.get('confirmed_status')}")
    block = "\n\n".join(lines) if lines else "(the student marked every question as ready)"
    prompt = f"THE ASSIGNMENT:\n{assignment}\n\nQUESTIONS NEEDING MORE:\n{block}\n\nReturn the JSON object."
    data = await _ideas_llm(_INQUIRY_SYSTEM, prompt, "ot-ideas-inquiry")

    def _strlist(v):
        return [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else []
    allowed = {"assigned reading", "class notes", "textbook", "teacher-provided source", "the teacher", "an approved website"}
    sources = [s for s in _strlist(data.get("sources")) if s.lower() in allowed]
    # Seed the plan's needs with the research list the student already built up
    # during Pass 1 (the accumulated "what I still need to learn"), then add any
    # further needs the generator surfaced.
    research_needs = [str(it.get("need")).strip() for it in (ideas.get("research_list") or []) if str(it.get("need") or "").strip()]
    gen_needs = _strlist(data.get("needs"))
    seen = set()
    needs = []
    for n in research_needs + gen_needs:
        k = n.lower()
        if k not in seen:
            seen.add(k)
            needs.append(n)
    return {
        "understood": _strlist(data.get("understood")),
        "remaining": _strlist(data.get("remaining")),
        "needs": needs,
        "sources": sources,
        "text": "",
    }


_CONSTRUCT_SYSTEM = """You are Compass, helping a student CONSTRUCT their own ideas after revising their answers. You are given the assignment and the student's revised answers to each question. Help the student SEE the ideas that have emerged: point to repeated or connected ideas across answers, help distinguish a central idea from supporting information, and note which answers relate. Do NOT write the ideas for the student, and do NOT supply any subject-matter content. Offer brief guidance and 2-4 short thinking prompts.

Respond with ONLY this JSON (no prose/fences):
{"guidance":"a short paragraph of guidance","prompts":["short prompt","short prompt"]}"""


async def _ideas_construct(assignment: str, ideas: dict) -> dict:
    qs = ideas["questions"]
    resp = ideas["responses"]
    lines = []
    for i, q in enumerate(qs):
        r = resp.get(str(i), {}) or {}
        a = (r.get("pass2_text") or r.get("pass1_text") or "").strip() or "(no answer)"
        lines.append(f"[{i}] QUESTION: {q}\n    ANSWER: {a}")
    prompt = f"THE ASSIGNMENT:\n{assignment}\n\nTHE STUDENT'S REVISED ANSWERS:\n" + "\n\n".join(lines) + "\n\nReturn the JSON object."
    data = await _ideas_llm(_CONSTRUCT_SYSTEM, prompt, "ot-ideas-construct")
    prompts = data.get("prompts") if isinstance(data, dict) else None
    return {
        "guidance": (data.get("guidance") or "Look across your answers. Which ideas keep coming up? Which one feels most central, and which ones support it?").strip() if isinstance(data, dict) else "Look across your answers. Which ideas keep coming up?",
        "prompts": [str(p).strip() for p in (prompts or []) if str(p).strip()][:4],
    }


# ---------------------------------------------------------------------------
# My Ideas endpoints
# ---------------------------------------------------------------------------
class IdeasInteract(BaseModel):
    index: int
    content: str
    pass_no: int = 1


class IdeasSave(BaseModel):
    index: int
    content: str
    pass_no: int = 1


class IdeasAdvance(BaseModel):
    index: int


class MapItem(BaseModel):
    index: int
    status: str


class ConfirmMapBody(BaseModel):
    items: list[MapItem]
    self_assessment: Optional[str] = ""


class InquiryPlanBody(BaseModel):
    needs: Optional[list] = None
    sources: Optional[list] = None
    text: Optional[str] = None


class ConstructBody(BaseModel):
    content: str


def _set_phase(ideas: dict, phase: str) -> None:
    if phase in IDEAS_PHASES:
        ideas["phase"] = phase


@router.post("/{session_id}/ideas/init")
async def ideas_init(session_id: str):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot}


@router.post("/{session_id}/ideas/save")
async def ideas_save(session_id: str, body: IdeasSave):
    """Lightweight, non-LLM persistence of the student's current draft text.
    Used by Next / Previous / See my understanding / Build my ideas. Never invokes
    coaching — pedagogical evaluation is reserved for /ideas/interact ("Share")."""
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    qs = ideas["questions"]
    if body.index < 0 or body.index >= len(qs):
        raise HTTPException(status_code=422, detail="question index out of range")
    key = str(body.index)
    r = {**_blank_response(), **ideas["responses"].get(key, {})}
    if body.pass_no == 2:
        r["pass2_text"] = body.content
    else:
        r["pass1_text"] = body.content
    # Editing an already-shared answer makes it a revision; otherwise it stays a draft.
    r["state"] = "revised" if r.get("state") == "shared" else (r.get("state") or "draft")
    ideas["responses"][key] = r
    ot["objects"]["my_ideas"] = _compose_my_ideas(ot)
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot}


@router.post("/{session_id}/ideas/interact")
async def ideas_interact(session_id: str, body: IdeasInteract):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    qs = ideas["questions"]
    if body.index < 0 or body.index >= len(qs):
        raise HTTPException(status_code=422, detail="question index out of range")
    key = str(body.index)
    r = {**_blank_response(), **ideas["responses"].get(key, {})}
    prior = r.get("pass1_text", "")
    if body.pass_no == 2:
        r["pass2_text"] = body.content
    else:
        r["pass1_text"] = body.content
    ideas["responses"][key] = r
    result = await _ideas_reason(ot.get("seed_assignment", ""), qs[body.index], body.content, body.pass_no, prior=prior)
    r["structure"] = result["structure"] or r.get("structure", "")
    if body.pass_no == 2:
        r["pass2_status"] = "sufficient" if (result["sufficiency"] == "sufficient" or result["decision"] == "proceed") else "in_progress"
        returned_suff = r["pass2_status"]
    else:
        # First pass: track how developed the idea is and accumulate a research
        # list of what the student still needs to LEARN (never the answer).
        r["pass1_state"] = result.get("pass1_state") or "developing"
        need = (result.get("research_need") or "").strip()
        r["research_need"] = need if r["pass1_state"] == "knowledge_limit" else ""
        rl = ideas.setdefault("research_list", [])
        existing = next((it for it in rl if it.get("index") == body.index), None)
        if r["research_need"]:
            if existing:
                existing["need"] = r["research_need"]
            else:
                rl.append({"index": body.index, "question": qs[body.index], "need": r["research_need"], "at": _now_iso()})
        elif existing:
            rl.remove(existing)
        returned_suff = "attempted"
    r["state"] = "shared"
    ot["objects"]["my_ideas"] = _compose_my_ideas(ot)
    await _save_ot(session_id, ot)
    return {
        "ideas": ideas, "ot": ot,
        "decision": result["decision"], "structure": result["structure"],
        "difficulty": result["difficulty"], "message": result["message"],
        "pass1_state": result.get("pass1_state", ""), "research_need": result.get("research_need", ""),
        "sufficiency": returned_suff,
    }


@router.post("/{session_id}/ideas/advance")
async def ideas_advance(session_id: str, body: IdeasAdvance):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    ideas["index"] = max(0, min(body.index, max(0, len(ideas["questions"]) - 1)))
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot}


@router.post("/{session_id}/ideas/map")
async def ideas_map(session_id: str):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    result = await _ideas_map(ot.get("seed_assignment", ""), ideas)
    for it in result:
        key = str(it["index"])
        r = {**_blank_response(), **ideas["responses"].get(key, {})}
        r["recommended_status"] = it["status"]
        r["present"] = it["present"]
        r["gap"] = it["gap"]
        if not r.get("confirmed_status"):
            r["confirmed_status"] = it["status"]
        ideas["responses"][key] = r
    _set_phase(ideas, "knowledge_map")
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot}


@router.post("/{session_id}/ideas/confirm-map")
async def ideas_confirm_map(session_id: str, body: ConfirmMapBody):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    valid = {"can_answer", "partial", "need_info"}
    for it in body.items:
        key = str(it.index)
        if key in ideas["responses"] and it.status in valid:
            ideas["responses"][key]["confirmed_status"] = it.status
    if body.self_assessment is not None:
        ideas["self_assessment"] = body.self_assessment
    challenges = await _ideas_challenge(ot.get("seed_assignment", ""), ideas)
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot, "challenges": challenges}


@router.post("/{session_id}/ideas/inquiry-plan")
async def ideas_inquiry_plan(session_id: str):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    plan = await _ideas_inquiry(ot.get("seed_assignment", ""), ideas)
    existing = ideas.get("inquiry_plan") or {}
    if existing.get("text"):
        plan["text"] = existing["text"]
    ideas["inquiry_plan"] = plan
    _set_phase(ideas, "inquiry_plan")
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot}


@router.post("/{session_id}/ideas/pause")
async def ideas_pause(session_id: str, body: InquiryPlanBody):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    plan = ideas.get("inquiry_plan") or {"understood": [], "remaining": [], "needs": [], "sources": [], "text": ""}
    if body.needs is not None:
        plan["needs"] = [str(x).strip() for x in body.needs if str(x).strip()]
    if body.sources is not None:
        plan["sources"] = [str(x).strip() for x in body.sources if str(x).strip()]
    if body.text is not None:
        plan["text"] = body.text
    ideas["inquiry_plan"] = plan
    _set_phase(ideas, "inquiry_paused")
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot}


@router.post("/{session_id}/ideas/resume")
async def ideas_resume(session_id: str):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    _set_phase(ideas, "pass2")
    ideas["index"] = 0
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot}


@router.post("/{session_id}/ideas/construct-guidance")
async def ideas_construct_guidance(session_id: str):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    guidance = await _ideas_construct(ot.get("seed_assignment", ""), ideas)
    _set_phase(ideas, "construct")
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot, "guidance": guidance}


@router.post("/{session_id}/ideas/construct")
async def ideas_construct_save(session_id: str, body: ConstructBody):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    ideas["my_ideas_construct"] = body.content
    ot["objects"]["my_ideas"] = (body.content or "").strip() or _compose_my_ideas(ot)
    _set_phase(ideas, "done")
    ot["status"]["my_ideas"] = "sufficient"
    if "my_ideas" in ot.get("needs_review", []):
        ot["needs_review"] = [s for s in ot["needs_review"] if s != "my_ideas"]
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot}
