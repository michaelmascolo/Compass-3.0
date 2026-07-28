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
