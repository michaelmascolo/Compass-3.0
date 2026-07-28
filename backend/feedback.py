"""Compass Developmental Feedback System.

Collects BOTH usability and INSTRUCTIONAL feedback (whether Compass genuinely
helps students develop their own thinking), plus lightweight automatic
developmental analytics. Reuses the existing `sessions` collection (events live
on `session.feedback_events`) and stores submitted feedback in `feedback`.
Presentation/data only — the frozen engine and OT logic are untouched.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

_db = None
_now_iso = None


def init(db, now_iso):
    global _db, _now_iso
    _db = db
    _now_iso = now_iso


class FeedbackBody(BaseModel):
    kind: str = "general"  # general | end | early_exit
    responses: Optional[dict] = None
    would_use_again: Optional[str] = None
    exit_reason: Optional[str] = None
    comments: Optional[str] = None


class EventBody(BaseModel):
    event: str
    data: Optional[dict] = None


async def _load(session_id: str) -> dict:
    doc = await _db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return doc


def _analytics_snapshot(doc: dict) -> dict:
    """Automatic developmental analytics derived from session state + events."""
    events = doc.get("feedback_events", []) or []
    turns = doc.get("turns", []) or []
    ot = doc.get("ot") or {}
    revisions = sum(1 for t in turns if t.get("kind") == "revise")
    help_events = [e for e in events if e.get("event") in ("help_requested", "explain_more", "share_coach")]
    resumed = any(e.get("event") == "resume" for e in events)

    # stage reached
    phase = (doc.get("experience_control") or {}).get("phase")
    if phase == "reflection":
        stage_reached = "reflection"
    elif any(t.get("role") == "student" for t in turns):
        stage_reached = "writing"
    elif ot:
        if ot.get("handoff_ready"):
            stage_reached = "writing"
        else:
            stage_reached = f"ot:{ot.get('current_stage', 'the_assignment')}"
    else:
        stage_reached = "entry"

    # time per stage from stage_enter events (seconds between consecutive enters)
    from datetime import datetime
    enters = [e for e in events if e.get("event") == "stage_enter" and e.get("at")]
    time_per_stage = {}

    def _parse(ts):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
    for i, e in enumerate(enters):
        stage = (e.get("data") or {}).get("stage", "unknown")
        t0 = _parse(e.get("at"))
        t1 = _parse(enters[i + 1]["at"]) if i + 1 < len(enters) else _parse(doc.get("updated_at"))
        if t0 and t1 and t1 >= t0:
            time_per_stage[stage] = round(time_per_stage.get(stage, 0) + (t1 - t0).total_seconds(), 1)

    # exit after repeated difficulty: an early_exit event preceded by >=2 help/coach signals
    difficulty_signals = len(help_events)
    exited_after_difficulty = any(e.get("event") == "early_exit" for e in events) and difficulty_signals >= 2

    return {
        "stage_reached": stage_reached,
        "time_per_stage_seconds": time_per_stage,
        "revisions": revisions,
        "help_requested": len(help_events) > 0,
        "help_request_count": len(help_events),
        "exited_after_repeated_difficulty": exited_after_difficulty,
        "resumed_later": resumed,
        "event_count": len(events),
    }


@router.post("/{session_id}/event")
async def record_event(session_id: str, body: EventBody):
    ev = {"event": body.event, "data": body.data or {}, "at": _now_iso()}
    res = await _db.sessions.update_one(
        {"id": session_id}, {"$push": {"feedback_events": ev}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


@router.post("/{session_id}")
async def submit_feedback(session_id: str, body: FeedbackBody):
    doc = await _load(session_id)
    snapshot = _analytics_snapshot(doc)
    record = {
        "session_id": session_id,
        "kind": body.kind,
        "responses": body.responses or {},
        "would_use_again": body.would_use_again,
        "exit_reason": body.exit_reason,
        "comments": body.comments,
        "analytics": snapshot,
        "is_preview": doc.get("is_preview", False),
        "created_at": _now_iso(),
    }
    await _db.feedback.insert_one(dict(record))
    if body.kind == "early_exit":
        await _db.sessions.update_one(
            {"id": session_id},
            {"$push": {"feedback_events": {"event": "early_exit", "data": {"reason": body.exit_reason}, "at": _now_iso()}}},
        )
    record.pop("_id", None)
    return {"ok": True, "analytics": snapshot}


@router.get("/{session_id}/analytics")
async def get_analytics(session_id: str):
    doc = await _load(session_id)
    return {"analytics": _analytics_snapshot(doc)}
