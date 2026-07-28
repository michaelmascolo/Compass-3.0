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
# My Ideas — one question at a time. Structure-led scaffolding; distinguishes
# structural vs knowledge vs expression difficulty; PAUSE for missing knowledge;
# NEVER supplies subject-matter answers. Ends with a student-confirmed knowledge
# review. Presentation/instruction only — frozen engine + curriculum untouched.
# ---------------------------------------------------------------------------
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


def _ensure_ideas(ot: dict) -> dict:
    questions = _split_questions((ot.get("objects", {}) or {}).get("questions", ""))
    ideas = ot.get("ideas")
    if not ideas or ideas.get("questions") != questions:
        prev = (ideas or {}).get("responses", {}) if ideas else {}
        ideas = {
            "questions": questions,
            "index": 0,
            "responses": {str(i): prev.get(str(i), {"text": "", "status": "in_progress", "structure": ""}) for i in range(len(questions))},
            "review": (ideas or {}).get("review", {}) if ideas else {},
            "review_done": False,
        }
        ot["ideas"] = ideas
    return ideas


def _compose_my_ideas(ot: dict) -> str:
    ideas = ot.get("ideas") or {}
    qs = ideas.get("questions", [])
    resp = ideas.get("responses", {})
    blocks = []
    for i, q in enumerate(qs):
        r = (resp.get(str(i), {}) or {}).get("text", "").strip()
        if r:
            blocks.append(f"Q: {q}\nMy thinking: {r}")
    return "\n\n".join(blocks)


_IDEAS_SYSTEM = """You are Compass, helping a student develop their OWN ideas by answering ONE question at a time. You are given ONE question and the student's response to THAT question only. Never comment on other questions.

FIRST identify the intellectual STRUCTURE the question requires — e.g. Definition ("What is X?"), Comparison ("How do X and Y differ?"), Explanation or Causal explanation ("How/why does X affect/cause Y?"), Evaluation ("Which is better?"), Judgment/Argument ("What should be done?"), Description. LEAD WITH STRUCTURE: scaffold whether the response performs that operation BEFORE asking for more subject-matter content. E.g. for a definition: "This question asks for a definition — what the thing is, and the feature that distinguishes it from related things," then ask the student to inspect their own answer against that.

Distinguish three difficulty types and respond in THIS ORDER (address only ONE blocking difficulty):
1. STRUCTURAL — the response does not perform the required operation (an example instead of a definition; two descriptions with no comparison dimension; a claim with no explanation; evidence with no interpretation). Address this FIRST. Name the structure; point the student to examine their OWN response. Do NOT supply the correct answer.
2. KNOWLEDGE — structure is adequate but relevant information is missing. Use PAUSE (or ASK the student to identify what information is needed and where to find it). State the information-seeking task concretely (e.g. "Return to your source and look for what the author says CAUSES this effect."). NEVER supply the missing facts, definitions, evidence, or what a named source/author says.
3. EXPRESSION — the student seems to understand but hasn't communicated it clearly; address only if it blocks interpretation.

Do NOT treat every weak response as merely needing 'more detail'. Do NOT supply subject-matter answers from your own knowledge, tell the student what a source says, invent evidence, or complete the content. You MAY: name the required structure and the KIND of knowledge needed; ask the student to examine their own response; ask them to consult their notes/text/source/class materials; ask what evidence supports the answer; help identify what is still uncertain; distinguish what they know from what they are guessing.

Decisions:
- PROCEED — the response adequately performs the required structure (sufficiency, not perfection).
- TEACH — one blocking STRUCTURAL difficulty; teach that one structural move.
- ASK — not enough evidence of the student's understanding; one focused question.
- PAUSE — relevant KNOWLEDGE is missing; state the information-seeking task.
Speak to the student plainly and briefly. No jargon, labels, scores, or internal reasoning.

Respond with ONLY this JSON (no prose/fences):
{"decision":"proceed|teach|ask|pause","structure":"Definition|Comparison|Explanation|Causal explanation|Evaluation|Judgment|Description|Other","difficulty":"structural|knowledge|expression|none","message":"one short student-facing message doing exactly the one move","sufficiency":"sufficient|not_yet"}"""


async def _ideas_reason(assignment: str, question: str, response: str) -> dict:
    prompt = (
        f"THE ASSIGNMENT:\n{assignment}\n\n"
        f"THE ONE QUESTION the student is answering now:\n\"\"\"{question}\"\"\"\n\n"
        f"THE STUDENT'S RESPONSE TO THIS QUESTION:\n\"\"\"{(response or '').strip()}\"\"\"\n\n"
        "Identify the required intellectual structure, then decide PROCEED / TEACH / ASK / PAUSE. Respond with ONLY the JSON object."
    )
    for attempt in range(2):
        try:
            chat = LlmChat(api_key=_llm_key, session_id="ot-ideas", system_message=_IDEAS_SYSTEM).with_model("anthropic", "claude-sonnet-4-6")
            raw = await chat.send_message(UserMessage(text=prompt))
            data = _extract_json(raw)
            dec = (data.get("decision") or "").strip().lower()
            if dec not in ("proceed", "teach", "ask", "pause"):
                dec = "ask"
            return {
                "decision": dec,
                "structure": (data.get("structure") or "Other").strip(),
                "difficulty": (data.get("difficulty") or "none").strip().lower(),
                "message": (data.get("message") or "").strip(),
                "sufficiency": "sufficient" if (data.get("sufficiency") or "").strip().lower() == "sufficient" else "not_yet",
            }
        except Exception:
            if attempt == 0:
                continue
    return {"decision": "ask", "structure": "Other", "difficulty": "none", "message": "Tell me a little more about how you're thinking about this question.", "sufficiency": "not_yet"}


class IdeasInteract(BaseModel):
    index: int
    content: str


class IdeasAdvance(BaseModel):
    index: int


class ReviewItem(BaseModel):
    index: int
    classification: str


class IdeasReview(BaseModel):
    items: list[ReviewItem]


@router.post("/{session_id}/ideas/init")
async def ideas_init(session_id: str):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    await _save_ot(session_id, ot)
    return {"ideas": ideas}


@router.post("/{session_id}/ideas/interact")
async def ideas_interact(session_id: str, body: IdeasInteract):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    qs = ideas["questions"]
    if body.index < 0 or body.index >= len(qs):
        raise HTTPException(status_code=422, detail="question index out of range")
    key = str(body.index)
    ideas["responses"][key] = {**ideas["responses"].get(key, {}), "text": body.content}
    result = await _ideas_reason(ot.get("seed_assignment", ""), qs[body.index], body.content)
    status = "sufficient" if (result["sufficiency"] == "sufficient" or result["decision"] == "proceed") else "in_progress"
    ideas["responses"][key]["status"] = status
    ideas["responses"][key]["structure"] = result["structure"]
    ot["objects"]["my_ideas"] = _compose_my_ideas(ot)
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "decision": result["decision"], "structure": result["structure"], "difficulty": result["difficulty"], "message": result["message"], "sufficiency": status}


@router.post("/{session_id}/ideas/advance")
async def ideas_advance(session_id: str, body: IdeasAdvance):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    ideas["index"] = max(0, min(body.index, len(ideas["questions"])))
    await _save_ot(session_id, ot)
    return {"ideas": ideas}


@router.post("/{session_id}/ideas/review")
async def ideas_review(session_id: str, body: IdeasReview):
    doc = await _load_session(session_id)
    ot = doc.get("ot") or _blank_ot(doc.get("assignment", ""))
    ideas = _ensure_ideas(ot)
    for it in body.items:
        ideas["review"][str(it.index)] = {"classification": it.classification}
    ideas["review_done"] = True
    ot["objects"]["my_ideas"] = _compose_my_ideas(ot)
    ot["status"]["my_ideas"] = "sufficient"
    if "my_ideas" in ot.get("needs_review", []):
        ot["needs_review"] = [s for s in ot["needs_review"] if s != "my_ideas"]
    await _save_ot(session_id, ot)
    return {"ideas": ideas, "ot": ot}
