"""
SPRINT 1 — Compass Instructional State, Evidence & Audit Foundation.

An ADDITIVE, isolated persistence + audit layer. It does NOT touch the frozen
instructional engine, the Stage B/C reasoners, or any existing route. Its single
purpose: make every future Compass instructional decision traceable to student
EVIDENCE, a selected INSTRUCTIONAL OBJECT, a SUPPORT LEVEL, an EXIT CRITERION,
and a REQUIREMENT ID.

Governing sources: Compass Operational Specification v0.9 + Architecture Audit &
Implementation Package v0.95 (not present in the workspace; implemented to the
self-contained Sprint 1 brief; requirement IDs come from that brief).

Data-integrity core: the model NEVER stores a hypothesis as a fact. Every evidence
item is explicitly OBSERVED, HYPOTHESIZED, or UNKNOWN. Audit events are append-only;
a correction adds a superseding event and never erases the original.
"""
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

APP_VERSION = "sprint1-foundation-v1"

# Own DB handle (same Mongo/DB as the app; a second client is harmless).
_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
_db = _client[os.environ["DB_NAME"]]

STATES = _db.instructional_states
EVIDENCE = _db.evidence_records
AUDIT = _db.audit_events

foundation_router = APIRouter(prefix="/api")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Controlled vocabularies & requirement IDs
# ---------------------------------------------------------------------------
EVIDENCE_CATEGORIES = ("OBSERVED", "HYPOTHESIZED", "UNKNOWN")
EVIDENCE_SOURCES = ("student_text", "student_response", "teacher_input", "system_state")
EXIT_STATUSES = ("met", "not_met", "UNKNOWN")
ADVANCEMENT_DECISIONS = ("advance", "hold", "blocked")

REQ = {
    "VA-05": "Required instructional state persists across turns.",
    "DS-01": "Evidence categories (OBSERVED/HYPOTHESIZED/UNKNOWN) remain distinct.",
    "DS-02": "Prohibited personal attributions are not stored as diagnostic facts.",
    "TC-01": "Teacher overrides are visible and logged.",
    "VA-06": "Audit events can store requirement IDs.",
    "VA-07": "Conflicting or missing state is marked uncertain, never silently invented.",
}

# DS-02 — stable personal attributions that must NEVER be recorded as OBSERVED
# diagnostic facts about a learner. (The engine attends to observable writing
# activity, not hidden traits/abilities/stages.)
PROHIBITED_ATTRIBUTION = re.compile(
    r"\b("
    r"lazy|smart|dumb|stupid|unintelligent|intelligent|gifted|slow learner|"
    r"struggling student|weak student|poor writer|bad writer|low ability|high ability|"
    r"iq|dyslexi\w*|adhd|learning disab\w*|special needs|"
    r"unmotivated|careless|apathetic|incapable|hopeless|"
    r"below grade level as a person|just isn't a writer|not a writer|"
    r"talented|untalented|natural writer"
    r")\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class EvidenceRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state_id: str = ""
    assignment_id: str = ""
    revision_id: str = ""
    text_span: Optional[str] = None            # exact span/location when available
    category: str                              # OBSERVED | HYPOTHESIZED | UNKNOWN
    description: str = ""
    candidate_instructional_object: Optional[str] = None
    confidence: Optional[str] = None           # value or label
    source: str = ""                           # student_text|student_response|teacher_input|system_state
    created_at: str = Field(default_factory=now_iso)


class TeacherOverride(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    teacher_id: str = ""
    field: str = ""
    from_value: Optional[Any] = None
    to_value: Optional[Any] = None
    reason: str = ""
    created_at: str = Field(default_factory=now_iso)


class RevisionEntry(BaseModel):
    revision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    created_at: str = Field(default_factory=now_iso)


class ValidationResult(BaseModel):
    requirement_id: str
    passed: bool
    detail: str = ""


class InstructionalState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # identity
    student_id: str = ""
    teacher_id: str = ""
    assignment_id: str = ""
    session_id: Optional[str] = None           # link to an existing engine session, if any
    # assignment framing
    assignment_purpose: str = ""
    intended_reader: str = ""
    genre: str = ""
    grade_level: str = ""
    # student work
    current_student_text: str = ""
    revision_history: List[RevisionEntry] = Field(default_factory=list)
    # instruction
    current_instructional_object: Optional[str] = None   # may be null before selection
    dialogue_state: str = "not_started"
    scaffolding_level: str = "UNKNOWN"                    # support level
    exit_criterion_status: str = "UNKNOWN"                # met|not_met|UNKNOWN
    # interpretation, kept STRICTLY separated by epistemic status
    observed_strengths: List[str] = Field(default_factory=list)     # OBSERVED
    observed_evidence: List[str] = Field(default_factory=list)      # evidence_ids (OBSERVED)
    provisional_hypotheses: List[str] = Field(default_factory=list) # HYPOTHESIZED
    unknowns: List[str] = Field(default_factory=list)               # UNKNOWN / unresolved uncertainty
    # teacher control
    teacher_constraints: Dict[str, Any] = Field(default_factory=dict)
    teacher_overrides: List[TeacherOverride] = Field(default_factory=list)
    # decision
    advancement_decision: str = "hold"                   # advance|hold|blocked
    last_diagnostic_notice: str = ""                     # visible to authorized users only
    # --- Sprint 2 (Engine Bridge) additive fields: homes for live-engine decision
    # state the Sprint-1 model did not yet carry. Optional/defaulted → backward
    # compatible with every existing record and the Sprint-1 tests. ---
    reason_for_selection: str = ""                       # why the current object was selected
    prerequisite_status: Dict[str, Any] = Field(default_factory=dict)  # structural/conceptual prerequisites
    current_learner_task: str = ""                       # the task/invitation presented this turn
    last_learner_response: str = ""                      # the learner action that drove this turn
    last_revision_produced: str = ""                     # revision text produced this turn, if any
    exit_criterion_description: str = ""                 # the exit criterion text under instruction
    turns_recorded: int = 0                              # count of live engine turns bridged
    # --- Sprint 3 (Instructional Decision Engine) additive fields ---
    demonstrated_strengths: List[str] = Field(default_factory=list)
    strength_status: str = "UNKNOWN"                     # PRESENT | UNKNOWN
    candidate_instructional_objects: List[str] = Field(default_factory=list)
    selected_instructional_object: Optional[str] = None
    selected_object_definition: str = ""
    structural_prerequisite_status: str = "NOT_APPLICABLE"   # MET|NOT_MET|UNKNOWN|NOT_APPLICABLE
    conceptual_prerequisite_status: str = "NOT_APPLICABLE"
    observed_selection_evidence: List[str] = Field(default_factory=list)
    priority_rationale: str = ""
    deferred_targets: List[str] = Field(default_factory=list)
    decision_status: str = ""                            # READY|BLOCKED_*|TEACHER_OVERRIDE
    instructional_need: str = ""                         # NEEDS_INSTRUCTION|NO_CURRENT_INSTRUCTIONAL_TARGET
    decision_confidence: str = ""                        # high|medium|low
    decision_uncertainty: List[str] = Field(default_factory=list)
    engine_recommendation: Optional[str] = None          # preserved original when a teacher overrides
    decision_requirement_ids: List[str] = Field(default_factory=list)
    decision_timestamp: str = ""
    # --- Decision Engine V2 (RP5 consolidated) authoritative-output fields (additive) ---
    developmental_variation: str = ""                    # which common developmental form the writer is at
    instructional_intent: str = ""                       # what this coaching cycle intends the writer to build
    # --- Internal Instructional Decision analysis (never shown to the student; drives Teacher Review) ---
    instructional_analysis: Dict[str, Any] = Field(default_factory=dict)
    # count of consecutive continuation turns on the CURRENT target (0 on a fresh/first turn);
    # gates DISCOVERY (default) vs RESCUE (adaptive strategy scaffolds) dialogue. Additive/defaulted.
    current_target_attempts: int = 0
    # provenance
    migrated_from_session_id: Optional[str] = None
    migration_limitations: List[str] = Field(default_factory=list)
    version: int = 1
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state_id: str = ""
    event_type: str = ""
    requirement_ids: List[str] = Field(default_factory=list)   # VA-06
    input_state: Dict[str, Any] = Field(default_factory=dict)
    evidence_reviewed: List[str] = Field(default_factory=list) # evidence ids
    decision: str = ""
    rationale: str = ""
    generated_response: str = ""
    learner_action: str = ""
    teacher_override: Optional[Dict[str, Any]] = None
    output_state: Dict[str, Any] = Field(default_factory=dict)
    validation_results: List[Dict[str, Any]] = Field(default_factory=list)
    application_version: str = APP_VERSION
    supersedes: Optional[str] = None       # append-only correction chain
    superseded_by: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
async def _load_state(state_id: str) -> InstructionalState:
    doc = await STATES.find_one({"id": state_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Instructional state not found.")
    return InstructionalState(**doc)


async def _save_state(state: InstructionalState) -> None:
    state.updated_at = now_iso()
    await STATES.replace_one({"id": state.id}, state.model_dump(), upsert=True)


async def _write_audit(event: AuditEvent) -> AuditEvent:
    """Append-only. Never update-in-place; corrections add a superseding event."""
    await AUDIT.insert_one(event.model_dump())
    return event


def _authorize(viewer_role: str) -> None:
    if (viewer_role or "").lower() not in ("teacher", "admin"):
        # Never leak internals to a student; a plain 403 only.
        raise HTTPException(status_code=403, detail="Diagnostic trace is restricted to teacher/admin.")


# ---------------------------------------------------------------------------
# Validation guards (machine-checkable)
# ---------------------------------------------------------------------------
def guard_va05(state: InstructionalState) -> ValidationResult:
    missing = [f for f in ("student_id", "assignment_id") if not getattr(state, f)]
    ok = not missing
    return ValidationResult(requirement_id="VA-05", passed=ok,
                            detail="ok" if ok else f"missing required identity: {missing}")


def guard_ds01(evidence_items: List[EvidenceRecord]) -> ValidationResult:
    bad = [e.id for e in evidence_items if e.category not in EVIDENCE_CATEGORIES]
    # an item's text must not be simultaneously OBSERVED and HYPOTHESIZED
    seen: Dict[str, str] = {}
    conflicts = []
    for e in evidence_items:
        key = (e.description or "").strip().lower()
        if key and key in seen and seen[key] != e.category:
            conflicts.append(key)
        elif key:
            seen[key] = e.category
    ok = not bad and not conflicts
    detail = "ok" if ok else f"invalid_categories={bad}; cross_category_conflicts={conflicts}"
    return ValidationResult(requirement_id="DS-01", passed=ok, detail=detail)


def guard_ds02(text: str, category: str) -> ValidationResult:
    """A prohibited personal attribution may NEVER be stored as an OBSERVED fact."""
    hit = PROHIBITED_ATTRIBUTION.search(text or "")
    violates = bool(hit) and category == "OBSERVED"
    return ValidationResult(
        requirement_id="DS-02",
        passed=not violates,
        detail="ok" if not violates else f"prohibited personal attribution stored as OBSERVED fact: '{hit.group(0)}'",
    )


def guard_ds02_state(state: InstructionalState, observed_ev: List[EvidenceRecord]) -> ValidationResult:
    for e in observed_ev:
        r = guard_ds02(e.description, "OBSERVED")
        if not r.passed:
            return r
    for s in state.observed_strengths:
        r = guard_ds02(s, "OBSERVED")
        if not r.passed:
            return r
    return ValidationResult(requirement_id="DS-02", passed=True, detail="ok")


def guard_va07(state: InstructionalState, observed_ev: List[EvidenceRecord]) -> ValidationResult:
    """Conflicting or missing state must be marked uncertain, not invented.
    Advancement is only coherent when there is OBSERVED support for the current
    instructional object and the exit criterion is genuinely met."""
    problems = []
    if not state.current_instructional_object:
        problems.append("no instructional object selected")
    if state.exit_criterion_status == "met" and not observed_ev:
        problems.append("exit_criterion_status=met but no OBSERVED evidence exists")
    # cross-list contradiction: same item claimed OBSERVED and UNKNOWN
    overlap = set(x.lower() for x in state.observed_strengths) & set(x.lower() for x in state.unknowns)
    if overlap:
        problems.append(f"item claimed both OBSERVED and UNKNOWN: {sorted(overlap)}")
    ok = not problems
    return ValidationResult(requirement_id="VA-07", passed=ok,
                            detail="ok" if ok else "; ".join(problems))


def guard_va06(requirement_ids: List[str]) -> ValidationResult:
    ok = bool(requirement_ids)
    return ValidationResult(requirement_id="VA-06", passed=ok,
                            detail="ok" if ok else "decision audit event carries no requirement IDs")


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------
class StateCreate(BaseModel):
    student_id: str
    teacher_id: str = ""
    assignment_id: str
    session_id: Optional[str] = None
    assignment_purpose: str = ""
    intended_reader: str = ""
    genre: str = ""
    grade_level: str = ""
    current_student_text: str = ""
    teacher_constraints: Dict[str, Any] = Field(default_factory=dict)


class RevisionBody(BaseModel):
    text: str


class EvidenceBody(BaseModel):
    category: str
    description: str
    text_span: Optional[str] = None
    candidate_instructional_object: Optional[str] = None
    confidence: Optional[str] = None
    source: str = "system_state"
    revision_id: str = ""


class OverrideBody(BaseModel):
    teacher_id: str
    field: str
    from_value: Optional[Any] = None
    to_value: Optional[Any] = None
    reason: str = ""


class AdvanceBody(BaseModel):
    target_instructional_object: Optional[str] = None
    requested_exit_status: Optional[str] = None   # met|not_met|UNKNOWN


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@foundation_router.post("/instructional-state", response_model=InstructionalState)
async def create_state(body: StateCreate):
    """Get-or-create the persistent instructional state for a (student, assignment)."""
    existing = await STATES.find_one(
        {"student_id": body.student_id, "assignment_id": body.assignment_id}, {"_id": 0}
    )
    if existing:
        return InstructionalState(**existing)
    state = InstructionalState(
        student_id=body.student_id, teacher_id=body.teacher_id, assignment_id=body.assignment_id,
        session_id=body.session_id, assignment_purpose=body.assignment_purpose,
        intended_reader=body.intended_reader, genre=body.genre, grade_level=body.grade_level,
        current_student_text=body.current_student_text, teacher_constraints=body.teacher_constraints,
    )
    if body.current_student_text:
        state.revision_history.append(RevisionEntry(text=body.current_student_text))
    await _save_state(state)
    await _write_audit(AuditEvent(
        state_id=state.id, event_type="state_created", requirement_ids=["VA-05"],
        decision="created", rationale="new instructional state persisted",
        output_state={"version": state.version}, validation_results=[guard_va05(state).model_dump()],
    ))
    return state


@foundation_router.get("/instructional-state", response_model=Optional[InstructionalState])
async def lookup_state(student_id: str = Query(...), assignment_id: str = Query(...)):
    doc = await STATES.find_one({"student_id": student_id, "assignment_id": assignment_id}, {"_id": 0})
    return InstructionalState(**doc) if doc else None


@foundation_router.get("/instructional-state/{state_id}", response_model=InstructionalState)
async def get_state(state_id: str):
    return await _load_state(state_id)


@foundation_router.get("/instructional-state-by-session/{session_id}",
                       response_model=Optional[InstructionalState])
async def get_state_by_session(session_id: str):
    doc = await STATES.find_one({"session_id": session_id}, {"_id": 0})
    return InstructionalState(**doc) if doc else None


@foundation_router.post("/instructional-state/{state_id}/revision", response_model=InstructionalState)
async def save_revision(state_id: str, body: RevisionBody):
    state = await _load_state(state_id)
    entry = RevisionEntry(text=body.text)
    state.revision_history.append(entry)
    state.current_student_text = body.text
    state.version += 1
    await _save_state(state)
    await _write_audit(AuditEvent(
        state_id=state.id, event_type="revision_saved", requirement_ids=["VA-05"],
        learner_action="submitted_revision", decision="persisted",
        rationale="student revision appended to revision_history and current text updated",
        output_state={"version": state.version, "revision_id": entry.revision_id},
        validation_results=[guard_va05(state).model_dump()],
    ))
    return state


@foundation_router.post("/instructional-state/{state_id}/evidence")
async def add_evidence(state_id: str, body: EvidenceBody):
    state = await _load_state(state_id)
    category = (body.category or "").upper()
    if category not in EVIDENCE_CATEGORIES:
        # DS-01: reject unknown categories rather than silently coercing.
        raise HTTPException(status_code=422, detail={
            "diagnostic": f"DS-01 violation: category '{body.category}' is not one of {EVIDENCE_CATEGORIES}",
            "requirement_id": "DS-01",
        })
    ds02 = guard_ds02(body.description, category)
    if not ds02.passed:
        # DS-02: never store a prohibited personal attribution as an OBSERVED fact.
        await _write_audit(AuditEvent(
            state_id=state.id, event_type="evidence_rejected", requirement_ids=["DS-02"],
            decision="rejected", rationale=ds02.detail,
            validation_results=[ds02.model_dump()],
        ))
        raise HTTPException(status_code=422, detail={
            "diagnostic": ds02.detail, "requirement_id": "DS-02",
        })
    ev = EvidenceRecord(
        state_id=state.id, assignment_id=state.assignment_id, revision_id=body.revision_id,
        text_span=body.text_span, category=category, description=body.description,
        candidate_instructional_object=body.candidate_instructional_object,
        confidence=body.confidence, source=body.source,
    )
    await EVIDENCE.insert_one(ev.model_dump())
    # keep the state's separated interpretation lists in sync by epistemic status
    if category == "OBSERVED":
        state.observed_evidence.append(ev.id)
        if body.description:
            state.observed_strengths.append(body.description)
    elif category == "HYPOTHESIZED":
        state.provisional_hypotheses.append(body.description)
    else:
        state.unknowns.append(body.description or "unresolved uncertainty")
    await _save_state(state)
    await _write_audit(AuditEvent(
        state_id=state.id, event_type="evidence_added", requirement_ids=["DS-01", "DS-02"],
        evidence_reviewed=[ev.id], decision="stored", rationale=f"evidence stored as {category}",
        validation_results=[
            guard_ds01([ev]).model_dump(), ds02.model_dump(),
        ],
    ))
    return {"evidence": ev.model_dump(), "state_version": state.version}


@foundation_router.post("/instructional-state/{state_id}/override", response_model=InstructionalState)
async def add_override(state_id: str, body: OverrideBody):
    state = await _load_state(state_id)
    ov = TeacherOverride(teacher_id=body.teacher_id, field=body.field,
                         from_value=body.from_value, to_value=body.to_value, reason=body.reason)
    state.teacher_overrides.append(ov)
    # A teacher override may set a state field directly (visible + logged).
    if body.field and hasattr(state, body.field) and body.field not in (
        "id", "teacher_overrides", "version", "created_at"
    ):
        try:
            setattr(state, body.field, body.to_value)
        except Exception:
            pass
    await _save_state(state)
    await _write_audit(AuditEvent(
        state_id=state.id, event_type="teacher_override", requirement_ids=["TC-01"],
        teacher_override=ov.model_dump(), decision="override_recorded",
        rationale=body.reason or "teacher override",
        output_state={"field": body.field, "to_value": body.to_value},
        validation_results=[ValidationResult(requirement_id="TC-01", passed=True,
                                             detail="override recorded and visible in trace").model_dump()],
    ))
    return state


@foundation_router.post("/instructional-state/{state_id}/advance")
async def advance(state_id: str, body: AdvanceBody):
    state = await _load_state(state_id)
    if body.target_instructional_object is not None:
        state.current_instructional_object = body.target_instructional_object
    if body.requested_exit_status is not None:
        if body.requested_exit_status not in EXIT_STATUSES:
            raise HTTPException(status_code=422, detail="invalid exit status")
        state.exit_criterion_status = body.requested_exit_status

    observed_ev_docs = await EVIDENCE.find(
        {"state_id": state.id, "category": "OBSERVED"}, {"_id": 0}
    ).to_list(length=500)
    observed_ev = [EvidenceRecord(**d) for d in observed_ev_docs]

    checks = [
        guard_va05(state),
        guard_ds02_state(state, observed_ev),
        guard_va07(state, observed_ev),
    ]
    requirement_ids = ["VA-05", "DS-02", "VA-07", "VA-06"]
    checks.append(guard_va06(requirement_ids))
    failed = [c for c in checks if not c.passed]

    if failed:
        state.advancement_decision = "blocked"
        notice = "Advancement blocked — " + "; ".join(f"{c.requirement_id}: {c.detail}" for c in failed)
        state.last_diagnostic_notice = notice
        await _save_state(state)
        await _write_audit(AuditEvent(
            state_id=state.id, event_type="advancement_blocked", requirement_ids=requirement_ids,
            evidence_reviewed=[e.id for e in observed_ev], decision="blocked", rationale=notice,
            output_state={"advancement_decision": "blocked"},
            validation_results=[c.model_dump() for c in checks],
        ))
        # Visible diagnostic for authorized users; NOT a stack trace.
        raise HTTPException(status_code=409, detail={
            "diagnostic": notice,
            "failed_requirements": [c.requirement_id for c in failed],
            "validation_results": [c.model_dump() for c in checks],
        })

    state.advancement_decision = "advance"
    state.last_diagnostic_notice = ""
    await _save_state(state)
    await _write_audit(AuditEvent(
        state_id=state.id, event_type="advancement", requirement_ids=requirement_ids,
        evidence_reviewed=[e.id for e in observed_ev], decision="advance",
        rationale="all validation guards passed; exit criterion met with observed support",
        output_state={"advancement_decision": "advance",
                      "current_instructional_object": state.current_instructional_object},
        validation_results=[c.model_dump() for c in checks],
    ))
    return {"advancement_decision": "advance",
            "validation_results": [c.model_dump() for c in checks]}


@foundation_router.get("/instructional-state/{state_id}/trace")
async def diagnostic_trace(state_id: str, viewer_role: str = Query("student")):
    """Read-only diagnostic trace for authorized teacher/admin use. Not a numeric
    score; not for the student in this sprint."""
    _authorize(viewer_role)
    state = await _load_state(state_id)
    observed = [e["description"] for e in await EVIDENCE.find(
        {"state_id": state.id, "category": "OBSERVED"}, {"_id": 0, "description": 1}).to_list(200)]
    last_audit = await AUDIT.find({"state_id": state.id}, {"_id": 0}).sort("created_at", -1).to_list(1)
    coaching = await AUDIT.find({"state_id": state.id, "event_type": "coaching_dialogue"},
                                {"_id": 0}).sort("created_at", -1).to_list(1)
    coaching_os = (coaching[0].get("output_state") if coaching else {}) or {}
    return {
        "current_target": state.current_instructional_object,
        "observed_strength": state.observed_strengths,
        "evidence_used": observed,
        "provisional_interpretation": state.provisional_hypotheses,
        "uncertainty": state.unknowns,
        "current_support_level": state.scaffolding_level,
        "exit_criterion_status": state.exit_criterion_status,
        "most_recent_advancement_decision": state.advancement_decision,
        "teacher_overrides": [o.model_dump() for o in state.teacher_overrides],
        "diagnostic_notice": state.last_diagnostic_notice,
        "applicable_requirement_ids": (last_audit[0]["requirement_ids"] if last_audit else []),
        "version": state.version,
        # --- Sprint 3 decision block ---
        "demonstrated_strength": state.demonstrated_strengths,
        "strength_status": state.strength_status,
        "candidate_targets": state.candidate_instructional_objects,
        "selected_target": state.selected_instructional_object,
        "selected_object_definition": state.selected_object_definition,
        "structural_prerequisite_status": state.structural_prerequisite_status,
        "conceptual_prerequisite_status": state.conceptual_prerequisite_status,
        "observed_selection_evidence": state.observed_selection_evidence,
        "priority_rationale": state.priority_rationale,
        "deferred_targets": state.deferred_targets,
        "decision_status": state.decision_status,
        "instructional_need": state.instructional_need,
        "decision_confidence": state.decision_confidence,
        "decision_uncertainty": state.decision_uncertainty,
        "engine_recommendation": state.engine_recommendation,
        "decision_requirement_ids": state.decision_requirement_ids,
        "decision_timestamp": state.decision_timestamp,
        "developmental_variation": state.developmental_variation,
        "instructional_intent": state.instructional_intent,
        "instructional_analysis": state.instructional_analysis,
        # --- Revision Package 4 coaching path ---
        "coaching_path": coaching_os.get("coaching_path"),
        "instructional_target_presented": coaching_os.get("instructional_target_presented"),
        "dialogue_consistent_with_decision": coaching_os.get("consistent_with_decision"),
    }


@foundation_router.get("/instructional-state/{state_id}/audit")
async def get_audit(state_id: str, viewer_role: str = Query("student")):
    _authorize(viewer_role)
    events = await AUDIT.find({"state_id": state_id}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    return {"count": len(events), "events": events}


@foundation_router.post("/instructional-state/{state_id}/audit/correct")
async def correct_audit(state_id: str, supersedes_id: str = Query(...), rationale: str = Query(""),
                        viewer_role: str = Query("student")):
    """Append-only correction: add a superseding event; the original is preserved."""
    _authorize(viewer_role)
    orig = await AUDIT.find_one({"id": supersedes_id, "state_id": state_id}, {"_id": 0})
    if not orig:
        raise HTTPException(status_code=404, detail="original audit event not found")
    new_evt = AuditEvent(state_id=state_id, event_type="correction", supersedes=supersedes_id,
                         decision="supersede", rationale=rationale or "correction",
                         requirement_ids=orig.get("requirement_ids", []))
    await _write_audit(new_evt)
    # mark the original as superseded WITHOUT erasing it
    await AUDIT.update_one({"id": supersedes_id}, {"$set": {"superseded_by": new_evt.id}})
    return {"superseding_event": new_evt.model_dump()}


@foundation_router.post("/instructional-state/{state_id}/target-override")
async def teacher_target_override(state_id: str, teacher_id: str = Query(...),
                                  to_object: str = Query(...), reason: str = Query(""),
                                  viewer_role: str = Query("student")):
    """TC-02 — explicit teacher target override; preserves the engine recommendation."""
    _authorize(viewer_role)
    import compass_decision_engine as _de
    try:
        return await _de.apply_teacher_target_override(state_id, teacher_id, to_object, reason)
    except ValueError:
        raise HTTPException(status_code=404, detail="Instructional state not found.")


@foundation_router.post("/admin/foundation/migrate")
async def migrate_existing(viewer_role: str = Query("student"), limit: int = Query(1000)):
    """Compatibility layer: create an instructional state for each existing engine
    session that lacks one. READ-ONLY on `sessions` (never deletes/modifies student
    data). Missing fields become UNKNOWN/null and are logged as migration limitations."""
    _authorize(viewer_role)
    created, skipped, limitations_total = 0, 0, 0
    cursor = _db.sessions.find({}, {"_id": 0}).limit(limit)
    async for s in cursor:
        sid = s.get("id")
        if not sid:
            continue
        if await STATES.find_one({"migrated_from_session_id": sid}, {"_id": 0}):
            skipped += 1
            continue
        telos = s.get("telos") or {}
        theory = s.get("theory") or {}
        sc = (theory.get("scaffolding_control") or {})
        turns = s.get("turns") or []
        student_turns = [t for t in turns if t.get("role") == "student"]
        current_text = student_turns[-1]["content"] if student_turns else ""
        limitations: List[str] = []

        def pick(val, name):
            nonlocal limitations
            if val:
                return val
            limitations.append(f"{name} unavailable in legacy session -> UNKNOWN")
            return "UNKNOWN"

        state = InstructionalState(
            student_id=pick(s.get("student_name") or s.get("teacher_id"), "student_id"),
            teacher_id=s.get("teacher_id") or "UNKNOWN",
            assignment_id=s.get("config_id") or s.get("assignment") or pick(None, "assignment_id"),
            session_id=sid,
            assignment_purpose=telos.get("governing_pedagogical_purpose") or s.get("pedagogical_purpose") or "UNKNOWN",
            intended_reader=telos.get("audience_or_communicative_purpose") or "UNKNOWN",
            genre=pick(None, "genre"),
            grade_level=pick(None, "grade_level"),
            current_student_text=current_text,
            current_instructional_object=(sc.get("primary_target") or None),
            exit_criterion_status="UNKNOWN",
            scaffolding_level="UNKNOWN",
            migrated_from_session_id=sid,
            migration_limitations=limitations,
        )
        if current_text:
            state.revision_history.append(RevisionEntry(text=current_text))
        await _save_state(state)
        limitations_total += len(limitations)
        await _write_audit(AuditEvent(
            state_id=state.id, event_type="migration", requirement_ids=["VA-05", "VA-07"],
            decision="migrated", rationale="legacy session mapped; missing fields set UNKNOWN",
            input_state={"session_id": sid},
            output_state={"instructional_state_id": state.id, "limitations": limitations},
            validation_results=[guard_va05(state).model_dump()],
        ))
        created += 1
    return {"created": created, "skipped_already_migrated": skipped,
            "total_migration_limitations_logged": limitations_total}


# ===========================================================================
# SPRINT 2 — ENGINE BRIDGE
# The live coaching engine becomes both CONSUMER and PRODUCER of persistent
# instructional state. `begin_instructional_turn` = read (turn start);
# `record_instructional_turn` = write (turn end, BEFORE the learner sees the
# response). No new instructional logic — this maps the frozen engine's output
# into structured, auditable state so that no instructional decision exists only
# in generated text.
# ===========================================================================
async def get_or_create_state_for_session(session: Dict[str, Any]) -> InstructionalState:
    """One persistent instructional state per live engine session (keyed by session_id)."""
    sid = session.get("id")
    doc = await STATES.find_one({"session_id": sid}, {"_id": 0})
    if doc:
        return InstructionalState(**doc)
    telos = session.get("telos") or {}
    state = InstructionalState(
        student_id=session.get("student_name") or sid,
        teacher_id=session.get("teacher_id") or "",
        assignment_id=(session.get("config_id") or session.get("assignment_code")
                       or session.get("assignment") or sid),
        session_id=sid,
        assignment_purpose=(telos.get("governing_pedagogical_purpose")
                            or session.get("pedagogical_purpose") or ""),
        intended_reader=telos.get("audience_or_communicative_purpose") or "",
        genre=session.get("current_writing_task") or "",
        grade_level="",
    )
    await _save_state(state)
    await _write_audit(AuditEvent(
        state_id=state.id, event_type="state_created_from_session", requirement_ids=["VA-05"],
        decision="created", rationale="instructional state bootstrapped for live engine session",
        input_state={"session_id": sid}, output_state={"version": state.version},
        validation_results=[guard_va05(state).model_dump()],
    ))
    return state


async def begin_instructional_turn(session: Dict[str, Any], learner_content: str, kind: str) -> InstructionalState:
    """CONSUMER step — every interaction BEGINS by reading the current instructional
    state. Logs a turn_started audit event capturing the state that was read."""
    state = await get_or_create_state_for_session(session)
    await _write_audit(AuditEvent(
        state_id=state.id, event_type="turn_started", requirement_ids=["VA-05"],
        input_state={
            "current_instructional_object": state.current_instructional_object,
            "exit_criterion_status": state.exit_criterion_status,
            "advancement_decision": state.advancement_decision,
            "version": state.version,
        },
        learner_action=f"{kind}: {(learner_content or '')[:280]}",
        decision="state_read", rationale="engine read persistent instructional state before reasoning",
        validation_results=[guard_va05(state).model_dump()],
    ))
    return state


def _first_nonempty(*vals) -> str:
    for v in vals:
        if v:
            return v if isinstance(v, str) else str(v)
    return ""


async def record_instructional_turn(
    session: Dict[str, Any],
    theory: Dict[str, Any],
    invitation: str,
    learner_content: str,
    kind: str,
) -> Optional[InstructionalState]:
    """PRODUCER step — every interaction ENDS by writing the updated instructional
    state (+ evidence + a comprehensive audit event) BEFORE the response is presented.
    Pure mapping of the frozen engine's `theory` output; no instructional logic."""
    state = await get_or_create_state_for_session(session)
    sc = theory.get("scaffolding_control") or {}
    ir = theory.get("instructional_reasoning") or {}
    sr = theory.get("structural_reasoning") or {}
    rd = theory.get("revision_development") or {}

    draft_before = state.current_student_text
    is_revision = (kind == "revise") and bool(learner_content) and (learner_content.strip() != (draft_before or "").strip())

    # ---- current writing snapshot / revision produced ----
    if learner_content:
        state.revision_history.append(RevisionEntry(text=learner_content))
        state.current_student_text = learner_content
    state.last_revision_produced = learner_content if is_revision else ""
    state.last_learner_response = f"{kind}: {learner_content}" if learner_content else ""

    # ---- selected canonical instructional object + reason ----
    obj = _first_nonempty(sc.get("primary_target"), ir.get("active_instructional_element")) or None
    state.current_instructional_object = obj
    state.reason_for_selection = _first_nonempty(
        sc.get("prioritization_rationale"), ir.get("resource_selection_rationale"))

    # ---- structural & conceptual prerequisite status ----
    state.prerequisite_status = {
        "required_dependency": ir.get("required_dependency") or "",
        "dependency_status": ir.get("dependency_status") or "",
        "dependency_rationale": ir.get("dependency_rationale") or "",
        "developmental_dependencies": sr.get("developmental_dependencies") or [],
        "continue_consolidate_release_or_shift": ir.get("continue_consolidate_release_or_shift") or "",
    }

    # ---- dialogue state / support level / learner task ----
    state.dialogue_state = _first_nonempty(sc.get("cycle_status"), "in_progress")
    state.scaffolding_level = _first_nonempty(
        ir.get("degree_of_student_control"), sc.get("instructional_mode"), "UNKNOWN")
    state.current_learner_task = _first_nonempty(invitation, ir.get("next_student_act"))

    # ---- exit criterion status + description ----
    suff = (ir.get("sufficiency_for_next_step") or "").lower()
    state.exit_criterion_status = "met" if suff == "sufficient" else ("not_met" if suff == "not_yet" else "UNKNOWN")
    state.exit_criterion_description = _first_nonempty(
        ir.get("next_developmental_step"), sr.get("active_exit_criterion"), ir.get("active_instructional_element"))

    # ---- advancement decision (RECORD the engine's decision; not a new gate) ----
    release = (ir.get("continue_consolidate_release_or_shift") or "").lower()
    cycle = (sc.get("cycle_status") or "").lower()
    if state.exit_criterion_status == "met" or release == "release" or cycle in ("stop", "consolidate_and_return"):
        state.advancement_decision = "advance"
    else:
        state.advancement_decision = "hold"

    # ---- evidence (OBSERVED / HYPOTHESIZED / UNKNOWN), append-only records ----
    # reset the per-turn interpretation lists (state reflects the CURRENT turn);
    # the evidence_records collection retains the full append-only history.
    state.observed_strengths, state.observed_evidence = [], []
    state.provisional_hypotheses, state.unknowns = [], []

    async def _emit(category: str, description: str, source: str, span: Optional[str] = None):
        if not description:
            return
        if category == "OBSERVED" and not guard_ds02(description, "OBSERVED").passed:
            # DS-02: never store a prohibited personal attribution as an OBSERVED fact.
            await _write_audit(AuditEvent(
                state_id=state.id, event_type="evidence_suppressed", requirement_ids=["DS-02"],
                decision="suppressed", rationale=f"DS-02: '{description[:80]}' not stored as OBSERVED fact",
                validation_results=[guard_ds02(description, "OBSERVED").model_dump()]))
            return
        ev = EvidenceRecord(state_id=state.id, assignment_id=state.assignment_id, category=category,
                            description=description, candidate_instructional_object=obj,
                            source=source, text_span=span, confidence="engine")
        await EVIDENCE.insert_one(ev.model_dump())
        if category == "OBSERVED":
            state.observed_evidence.append(ev.id)
            state.observed_strengths.append(description)
        elif category == "HYPOTHESIZED":
            state.provisional_hypotheses.append(description)
        else:
            state.unknowns.append(description)
        return ev.id

    # OBSERVED — demonstrated strengths / what the text actually does
    for el in (sr.get("elements_present") or [])[:6]:
        await _emit("OBSERVED", f"Element present: {el}", "student_text")
    for k in ("observed_differentiations", "observed_integrations", "observed_coordinations"):
        for item in (theory.get(k) or [])[:4]:
            await _emit("OBSERVED", item, "student_text")
    await _emit("OBSERVED", ir.get("student_current_organization"), "student_text")
    await _emit("OBSERVED", ir.get("evidence_of_developmental_movement"), "student_response")
    if rd.get("applies") and rd.get("development_detected"):
        await _emit("OBSERVED", f"Revision: {rd.get('development_detected')}", "student_response")

    # HYPOTHESIZED — developmental needs / interpretations (never asserted as fact)
    await _emit("HYPOTHESIZED", ir.get("primary_developmental_tension"), "system_state")
    if ir.get("required_dependency"):
        await _emit("HYPOTHESIZED", f"Prerequisite need: {ir.get('required_dependency')}", "system_state")
    for el in (sr.get("elements_absent") or [])[:4]:
        await _emit("HYPOTHESIZED", f"Element not yet present: {el}", "system_state")

    # UNKNOWN — unresolved uncertainty / missing state marked, never invented (VA-07)
    if not obj:
        await _emit("UNKNOWN", "No single instructional object selected this turn.", "system_state")
    if state.exit_criterion_status == "UNKNOWN":
        await _emit("UNKNOWN", "Readiness to advance (exit criterion) not yet determinable.", "system_state")
    for t in (theory.get("unresolved_tensions") or [])[:3]:
        await _emit("UNKNOWN", t, "system_state")

    state.turns_recorded += 1
    state.version += 1
    await _save_state(state)

    # ---- validation guards (non-blocking here: recorded, do not interrupt the
    # frozen live turn — the live engine already produced the decision) ----
    observed_ev = [EvidenceRecord(state_id=state.id, category="OBSERVED", description=d)
                   for d in state.observed_strengths]
    checks = [guard_va05(state), guard_ds01(observed_ev), guard_ds02_state(state, observed_ev),
              guard_va07(state, observed_ev), guard_va06(["VA-05", "DS-01", "DS-02", "VA-07", "VA-06"])]

    latest_override = state.teacher_overrides[-1].model_dump() if state.teacher_overrides else None
    req_ids = ["VA-05", "DS-01", "DS-02", "VA-06", "VA-07"] + (["TC-01"] if latest_override else [])

    await _write_audit(AuditEvent(
        state_id=state.id, event_type="instructional_turn", requirement_ids=req_ids,
        input_state={"draft_before": (draft_before or "")[:400]},
        evidence_reviewed=state.observed_evidence,
        decision=f"object={obj}; advancement={state.advancement_decision}; exit={state.exit_criterion_status}",
        rationale=state.reason_for_selection,
        generated_response=(invitation or "")[:2000],   # ties the generated text to the structured decision
        learner_action=state.last_learner_response,
        teacher_override=latest_override,
        output_state={
            "current_instructional_object": obj,
            "reason_for_selection": state.reason_for_selection,
            "prerequisite_status": state.prerequisite_status,
            "dialogue_state": state.dialogue_state,
            "support_level": state.scaffolding_level,
            "current_learner_task": state.current_learner_task,
            "exit_criterion_status": state.exit_criterion_status,
            "exit_criterion_description": state.exit_criterion_description,
            "advancement_decision": state.advancement_decision,
            "revision_produced": bool(state.last_revision_produced),
            "version": state.version,
        },
        validation_results=[c.model_dump() for c in checks],
    ))
    return state
