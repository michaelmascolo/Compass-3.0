"""
SPRINT 3 — INSTRUCTIONAL DECISION ENGINE (isolated, additive).

Each live coaching turn now selects ONE instructional target through an explicit,
evidence-based decision process (A–F) rather than relying only on the generated
conversational response. This module:
  - reads the persistent instructional state (Sprints 1–2);
  - separates OBSERVED evidence from HYPOTHESIZED / UNKNOWN;
  - identifies candidate targets, checks structural + conceptual prerequisites;
  - selects exactly ONE primary target (or an explicit blocked/no-target status);
  - records why, with confidence + uncertainty + requirement IDs;
  - writes the decision into persistent state BEFORE the learner-facing response.

It adds NO scaffolding sequences, does NOT redesign the dialogue, and does NOT
rewrite the Canonical Instructional Object knowledge base. It only selects a target.
Interfaces cleanly with compass_foundation (state, evidence, audit, guards).

Epistemic rule: structural PRESENCE/ABSENCE in the text is OBSERVED (directly
verifiable in the artifact); inferences about the learner's mind are HYPOTHESIZED.
DE-03 forbids treating a HYPOTHESIZED/UNKNOWN item as an observed fact.
"""
from typing import Any, Dict, List, Optional, Tuple

import compass_foundation as F
from compass_foundation import (AuditEvent, EvidenceRecord, InstructionalState,
                                 PROHIBITED_ATTRIBUTION, now_iso)

# ---- controlled vocabularies -------------------------------------------------
# Canonical priority order (index 0 = highest priority). Encodes priority rules
# D1–D7: structural integrity / higher-order structures / prerequisites before
# dependent skills / reader comprehension before stylistic refinement.
CANONICAL_ORDER = [
    "Reader Orientation",
    "Thesis",
    "Paragraph Main Point",
    "Definition",
    "Evidence",
    "Explanation",
    "Elaboration",
    "Transition",
    "Paragraph Closure",
    "Conclusion",
    "Sentence Construction",
]
ORDER_INDEX = {o: i for i, o in enumerate(CANONICAL_ORDER)}

# Brief references to existing object names (NOT the CIO knowledge base — one-line
# references only, per "reference existing object names").
OBJECT_DEFINITIONS = {
    "Reader Orientation": "Establishes for the reader what the piece is about and why it matters.",
    "Thesis": "A single contestable central claim that answers the task and organizes the writing.",
    "Paragraph Main Point": "The one idea a paragraph exists to make.",
    "Definition": "Clarifies the working meaning of a key term the writing depends on.",
    "Evidence": "Specific, relevant material that supports a claim.",
    "Explanation": "Makes explicit how the evidence supports the claim (the reasoning connecting them).",
    "Elaboration": "Develops an idea so a reader can fully understand it.",
    "Transition": "Signals the relationship between two ideas so the reader can follow the move.",
    "Paragraph Closure": "Completes a paragraph's work before moving on.",
    "Conclusion": "Consolidates the argument's meaning for the reader.",
    "Sentence Construction": "Sentence-level clarity and correctness (refinement).",
}

DECISION_STATUSES = (
    "READY",
    "BLOCKED_INSUFFICIENT_EVIDENCE",
    "BLOCKED_CONTRADICTORY_EVIDENCE",
    "BLOCKED_PREREQUISITE_UNKNOWN",
    "TEACHER_OVERRIDE",
)
# v2.1 orthogonality: decision VALIDITY (above) is separate from instructional NECESSITY (below).
INSTRUCTIONAL_NEEDS = ("NEEDS_INSTRUCTION", "NO_CURRENT_INSTRUCTIONAL_TARGET")
DE_REQS = ["DE-01", "DE-02", "DE-03", "DE-04", "DE-05"]

# structural / conceptual prerequisites. "A|B" = satisfied if A OR B present.
# special tokens: "two_ideas" (>=2 content objects present), "body" (any body element present).
PREREQUISITES: Dict[str, Dict[str, List[str]]] = {
    "Reader Orientation": {"structural": [], "conceptual": []},
    "Thesis": {"structural": [], "conceptual": []},
    "Paragraph Main Point": {"structural": [], "conceptual": []},
    "Definition": {"structural": [], "conceptual": []},
    "Evidence": {"structural": ["Thesis|Paragraph Main Point"], "conceptual": []},
    "Explanation": {"structural": ["Thesis|Paragraph Main Point", "Evidence"],
                    "conceptual": ["relationship_claim_evidence"]},
    "Elaboration": {"structural": ["Paragraph Main Point|Thesis"], "conceptual": []},
    "Transition": {"structural": ["two_ideas"], "conceptual": ["relationship_between_ideas"]},
    "Paragraph Closure": {"structural": ["Paragraph Main Point"], "conceptual": []},
    "Conclusion": {"structural": ["Thesis", "body"], "conceptual": []},
    "Sentence Construction": {"structural": [], "conceptual": []},
}
BODY_OBJECTS = {"Evidence", "Explanation", "Paragraph Main Point", "Elaboration"}
CONTENT_OBJECTS = {"Thesis", "Paragraph Main Point", "Evidence", "Explanation", "Elaboration", "Definition"}


def normalize_object(name: str) -> Optional[str]:
    """Map a free-text engine element label to a canonical instructional object."""
    if not name:
        return None
    n = name.lower()
    table = [
        ("thesis", "Thesis"),
        ("central claim", "Thesis"),
        ("governing claim", "Thesis"),
        ("main point", "Paragraph Main Point"),
        ("topic sentence", "Paragraph Main Point"),
        ("paragraph focus", "Paragraph Main Point"),
        ("reader orientation", "Reader Orientation"),
        ("orientation", "Reader Orientation"),
        ("introduction", "Reader Orientation"),
        ("definition", "Definition"),
        ("evidence", "Evidence"),
        ("explanation", "Explanation"),
        ("reasoning", "Explanation"),
        ("warrant", "Explanation"),
        ("relationship", "Explanation"),
        ("elaboration", "Elaboration"),
        ("develop", "Elaboration"),
        ("transition", "Transition"),
        ("coherence", "Transition"),
        ("closure", "Paragraph Closure"),
        ("conclusion", "Conclusion"),
        ("sentence", "Sentence Construction"),
        ("grammar", "Sentence Construction"),
        ("syntax", "Sentence Construction"),
        ("mechanic", "Sentence Construction"),
        ("style", "Sentence Construction"),
        ("organization", "Paragraph Main Point"),
    ]
    for key, obj in table:
        if key in n:
            return obj
    return None


# ---- structured input --------------------------------------------------------
class EvidenceView:
    """A normalized, decision-scoped evidence item."""
    __slots__ = ("category", "object", "polarity", "description")

    def __init__(self, category: str, object: Optional[str], polarity: str, description: str):
        self.category = category           # OBSERVED | HYPOTHESIZED | UNKNOWN
        self.object = object               # canonical object or None
        self.polarity = polarity           # present | absent | weak | contradictory | na
        self.description = description


class Decision:
    def __init__(self):
        self.demonstrated_strengths: List[str] = []
        self.strength_status: str = "UNKNOWN"
        self.candidate_instructional_objects: List[str] = []
        self.selected_instructional_object: Optional[str] = None
        self.selected_object_definition: str = ""
        self.structural_prerequisite_status: str = "NOT_APPLICABLE"
        self.conceptual_prerequisite_status: str = "NOT_APPLICABLE"
        self.observed_selection_evidence: List[str] = []
        self.priority_rationale: str = ""
        self.deferred_targets: List[str] = []
        self.decision_status: str = "BLOCKED_INSUFFICIENT_EVIDENCE"
        self.instructional_need: str = "NEEDS_INSTRUCTION"
        self.decision_confidence: str = "low"
        self.decision_uncertainty: List[str] = []
        self.engine_recommendation: Optional[str] = None   # preserved when a teacher overrides
        self.decision_requirement_ids: List[str] = list(DE_REQS)

    def as_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "demonstrated_strengths", "strength_status", "candidate_instructional_objects",
            "selected_instructional_object", "selected_object_definition",
            "structural_prerequisite_status", "conceptual_prerequisite_status",
            "observed_selection_evidence", "priority_rationale", "deferred_targets",
            "decision_status", "instructional_need", "decision_confidence", "decision_uncertainty",
            "engine_recommendation", "decision_requirement_ids")}


# ---- the explicit A–F decision process --------------------------------------
def _prereq_status_for(obj: str, present: set, absent: set,
                       concept_not_met: set, concept_unknown_default: str = "UNKNOWN"
                       ) -> Tuple[str, str, Optional[str]]:
    """Return (structural_status, conceptual_status, missing_structural_object)."""
    spec = PREREQUISITES.get(obj, {"structural": [], "conceptual": []})
    # structural
    s_status, missing = "NOT_APPLICABLE", None
    if spec["structural"]:
        statuses = []
        for req in spec["structural"]:
            if req == "two_ideas":
                present_content = present & CONTENT_OBJECTS
                ok = len(present_content) >= 2
                statuses.append("MET" if ok else ("NOT_MET" if absent else "UNKNOWN"))
            elif req == "body":
                ok = bool(present & BODY_OBJECTS)
                statuses.append("MET" if ok else ("NOT_MET" if (BODY_OBJECTS & absent) else "UNKNOWN"))
            else:
                alts = req.split("|")
                if any(a in present for a in alts):
                    statuses.append("MET")
                elif any(a in absent for a in alts):
                    statuses.append("NOT_MET")
                    missing = missing or next((a for a in alts if a in absent), alts[0])
                else:
                    statuses.append("UNKNOWN")
        s_status = "NOT_MET" if "NOT_MET" in statuses else ("UNKNOWN" if "UNKNOWN" in statuses else "MET")
    # conceptual
    c_status = "NOT_APPLICABLE"
    if spec["conceptual"]:
        if any(c in concept_not_met for c in spec["conceptual"]):
            c_status = "NOT_MET"
        else:
            c_status = concept_unknown_default
    return s_status, c_status, missing


def decide(evidence: List[EvidenceView], teacher_override: Optional[Dict[str, Any]] = None) -> Decision:
    """Pure A–F decision over normalized evidence. Deterministic and testable."""
    d = Decision()

    # DE-05: prohibited personal attributions never influence selection — drop them.
    def _prohibited(e: EvidenceView) -> bool:
        return bool(PROHIBITED_ATTRIBUTION.search(e.description or ""))
    clean = [e for e in evidence if not _prohibited(e)]
    d.decision_uncertainty += [f"suppressed personal attribution: {e.description[:60]}"
                               for e in evidence if _prohibited(e)]

    observed = [e for e in clean if e.category == "OBSERVED"]
    hypothesized = [e for e in clean if e.category == "HYPOTHESIZED"]
    unknown = [e for e in clean if e.category == "UNKNOWN"]

    # A. RECOGNIZE STRENGTH — only from OBSERVED present evidence
    present = {e.object for e in observed if e.polarity == "present" and e.object}
    absent = {e.object for e in observed if e.polarity in ("absent", "weak") and e.object}
    d.demonstrated_strengths = [e.description for e in observed if e.polarity == "present"]
    d.strength_status = "PRESENT" if d.demonstrated_strengths else "UNKNOWN"

    # F(early). Insufficient evidence → block, do not invent.
    if not observed:
        d.decision_status = "BLOCKED_INSUFFICIENT_EVIDENCE"
        d.decision_uncertainty.append("no OBSERVED evidence available for a decision")
        return _finalize(d, observed, teacher_override)

    # Contradiction: same object OBSERVED both present and absent.
    contradictions = present & absent
    explicit_contra = {e.object for e in observed if e.polarity == "contradictory" and e.object}
    contradictions |= explicit_contra
    if contradictions:
        d.decision_status = "BLOCKED_CONTRADICTORY_EVIDENCE"
        d.decision_uncertainty.append(f"contradictory OBSERVED evidence for: {sorted(contradictions)}")
        return _finalize(d, observed, teacher_override)

    # B. CANDIDATE TARGETS — OBSERVED structural gaps (absent/weak) are the plausible targets.
    concept_not_met = {c for e in observed if e.polarity in ("absent", "weak")
                       for c in _concepts_for(e)}
    candidates = sorted([o for o in absent if o in ORDER_INDEX], key=lambda o: ORDER_INDEX[o])
    d.candidate_instructional_objects = list(candidates)

    # Test-6 branch: no OBSERVED gap. Prefer a justified advanced target from an OBSERVED
    # 'emerging/weak' higher structure; else an honest no-current-target state (never invent).
    if not candidates:
        d.decision_status = "READY"
        d.instructional_need = "NO_CURRENT_INSTRUCTIONAL_TARGET"
        d.priority_rationale = ("No OBSERVED structural gap; writing meets current objectives. "
                                "No weakness invented.")
        d.decision_confidence = "high" if d.demonstrated_strengths else "medium"
        return _finalize(d, observed, teacher_override)

    # C+D. Walk candidates by priority; resolve prerequisites (prerequisites before dependent skills).
    selected, why, chain = _resolve_priority(candidates, present, absent, concept_not_met)

    d.selected_instructional_object = selected
    d.deferred_targets = [c for c in candidates if c != selected]
    s_status, c_status, missing = _prereq_status_for(selected, present, absent, concept_not_met)
    d.structural_prerequisite_status = s_status
    d.conceptual_prerequisite_status = c_status

    # F. Decision status
    if s_status == "UNKNOWN":
        d.decision_status = "BLOCKED_PREREQUISITE_UNKNOWN"
        d.decision_uncertainty.append(
            f"structural prerequisite for {selected} cannot be confirmed from OBSERVED evidence")
        d.decision_confidence = "low"
    else:
        d.decision_status = "READY"
        d.decision_confidence = ("high" if (d.demonstrated_strengths and s_status == "MET")
                                 else "medium")

    d.priority_rationale = why
    d.selected_object_definition = OBJECT_DEFINITIONS.get(selected, "")
    d.decision_uncertainty += [e.description for e in hypothesized][:4]
    d.decision_uncertainty += [e.description for e in unknown][:3]
    if c_status == "UNKNOWN":
        d.decision_uncertainty.append(f"conceptual understanding for {selected} not directly observable")
    return _finalize(d, observed, teacher_override)


def _concepts_for(e: EvidenceView) -> List[str]:
    """Map an observed weakness to the conceptual prerequisite it implicates."""
    text = (e.description or "").lower()
    out = []
    if e.object == "Transition" or "relationship between" in text or "unclear relationship" in text:
        out.append("relationship_between_ideas")
    if e.object == "Explanation" or ("relationship" in text and "evidence" in text):
        out.append("relationship_claim_evidence")
    return out


def _resolve_priority(candidates, present, absent, concept_not_met) -> Tuple[str, str, List[str]]:
    """Select the single highest-priority target, re-targeting to a prerequisite when the
    top candidate's structural or conceptual prerequisite is NOT_MET."""
    chain: List[str] = []
    top = candidates[0]
    guard = 0
    while guard < 8:
        guard += 1
        chain.append(top)
        s_status, c_status, missing = _prereq_status_for(top, present, absent, concept_not_met)
        # structural prerequisite missing → the missing structure is the higher-priority target
        if s_status == "NOT_MET" and missing and missing in ORDER_INDEX and missing not in chain:
            top = missing
            continue
        # conceptual prerequisite not met (e.g. mechanical transition, unclear relationship)
        # → target the underlying relationship (Explanation), not the surface object.
        if c_status == "NOT_MET" and top in ("Transition",):
            reason = (f"'{top}' is used but the underlying relationship between the ideas is not yet "
                      f"clear; the reader cannot follow the move. Teach the underlying relationship "
                      f"(a {top} prerequisite) before transitional wording.")
            return "Explanation", reason, chain + ["Explanation"]
        break
    reason = (f"Selected '{top}' as the highest-leverage OBSERVED structural gap "
              f"(structural integrity / higher-order structure / prerequisites before dependent skills; "
              f"error frequency did not drive this). Deferred lower-order refinements.")
    return top, reason, chain


def _finalize(d: Decision, observed: List[EvidenceView],
              teacher_override: Optional[Dict[str, Any]]) -> Decision:
    # observed evidence that supports the selection (DE-02)
    if d.selected_instructional_object:
        d.observed_selection_evidence = [
            e.description for e in observed
            if e.object == d.selected_instructional_object or e.polarity == "present"][:6]
    # TC-02: teacher override — preserve the engine recommendation separately.
    if teacher_override and teacher_override.get("to_value"):
        d.engine_recommendation = d.selected_instructional_object
        d.selected_instructional_object = teacher_override["to_value"]
        d.selected_object_definition = OBJECT_DEFINITIONS.get(teacher_override["to_value"], "")
        d.decision_status = "TEACHER_OVERRIDE"
        d.priority_rationale = (f"Teacher override → {teacher_override['to_value']}. "
                                f"Engine recommendation preserved: {d.engine_recommendation}.")
    return d


# ---- machine-checkable guards -----------------------------------------------
def run_guards(d: Decision, observed: List[EvidenceView]) -> List[Dict[str, Any]]:
    results = []
    blocked = d.decision_status.startswith("BLOCKED")
    no_target = (d.decision_status == "READY"
                 and d.instructional_need == "NO_CURRENT_INSTRUCTIONAL_TARGET")
    active_targets = 1 if d.selected_instructional_object else 0

    # DE-01: exactly one active target, OR an explicit blocked status, OR an explicit
    # READY + NO_CURRENT_INSTRUCTIONAL_TARGET (no invented weakness).
    if d.decision_status == "TEACHER_OVERRIDE":
        de01 = active_targets == 1
    elif blocked or no_target:
        de01 = active_targets == 0
    else:
        de01 = active_targets == 1
    results.append({"requirement_id": "DE-01", "passed": de01,
                    "detail": f"status={d.decision_status} need={d.instructional_need} active_targets={active_targets}"})

    # DE-02: selection supported by >=1 OBSERVED evidence record.
    de02 = (not d.selected_instructional_object) or len(d.observed_selection_evidence) >= 1
    results.append({"requirement_id": "DE-02", "passed": de02,
                    "detail": f"observed_support={len(d.observed_selection_evidence)}"})

    # DE-03: no HYPOTHESIZED/UNKNOWN treated as observed — selection uses only OBSERVED.
    de03 = all(any(e.description == s and e.category == "OBSERVED" for e in observed)
               for s in d.observed_selection_evidence)
    results.append({"requirement_id": "DE-03", "passed": de03,
                    "detail": "selection evidence is exclusively OBSERVED"})

    # DE-04: missing/contradictory evidence → blocked, not invented.
    de04 = True
    if d.decision_status in ("BLOCKED_INSUFFICIENT_EVIDENCE", "BLOCKED_CONTRADICTORY_EVIDENCE",
                             "BLOCKED_PREREQUISITE_UNKNOWN"):
        de04 = d.selected_instructional_object is None or d.decision_status == "BLOCKED_PREREQUISITE_UNKNOWN"
    results.append({"requirement_id": "DE-04", "passed": de04,
                    "detail": "blocked states do not invent a target"})

    # DE-05: no prohibited attribution in selection evidence.
    de05 = not any(PROHIBITED_ATTRIBUTION.search(s or "") for s in d.observed_selection_evidence)
    results.append({"requirement_id": "DE-05", "passed": de05,
                    "detail": "no prohibited attribution influenced selection"})
    return results


# ---- live integration: build evidence from the frozen engine's theory --------
def build_evidence_from_theory(theory: Dict[str, Any]) -> List[EvidenceView]:
    sr = theory.get("structural_reasoning") or {}
    ir = theory.get("instructional_reasoning") or {}
    ev: List[EvidenceView] = []
    for el in (sr.get("elements_present") or []):
        obj = normalize_object(el)
        if obj:
            ev.append(EvidenceView("OBSERVED", obj, "present", f"Element present: {el}"))
    for el in (sr.get("elements_emerging") or []):
        obj = normalize_object(el)
        if obj:
            ev.append(EvidenceView("OBSERVED", obj, "weak", f"Element emerging: {el}"))
    for el in (sr.get("elements_absent") or []):
        obj = normalize_object(el)
        if obj:
            ev.append(EvidenceView("OBSERVED", obj, "absent", f"Element not yet present in the text: {el}"))
    # HYPOTHESIZED (about the learner's understanding) — informs uncertainty only.
    for k in ("primary_developmental_tension", "required_dependency"):
        if ir.get(k):
            ev.append(EvidenceView("HYPOTHESIZED", None, "na", ir[k]))
    for t in (theory.get("unresolved_tensions") or []):
        ev.append(EvidenceView("UNKNOWN", None, "na", t))
    return ev


async def decide_for_session(session_id: str, theory: Dict[str, Any],
                             invitation: str) -> Optional[Dict[str, Any]]:
    """Read state, run the explicit decision over the frozen engine's structural
    reasoning, persist the decision + supporting OBSERVED evidence + audit BEFORE
    the learner-facing response is presented. Returns the decision dict."""
    doc = await F.STATES.find_one({"session_id": session_id}, {"_id": 0})
    if not doc:
        return None
    state = InstructionalState(**doc)

    # honor an existing, unconsumed teacher override targeting the selected object
    t_override = None
    for ov in reversed(state.teacher_overrides):
        if ov.field in ("selected_instructional_object", "selected_object"):
            t_override = ov.model_dump()
            break

    evidence = build_evidence_from_theory(theory)
    observed = [e for e in evidence if e.category == "OBSERVED"
                and not PROHIBITED_ATTRIBUTION.search(e.description or "")]
    d = decide(evidence, t_override)
    guards = run_guards(d, observed)

    # persist supporting OBSERVED evidence records (DE-02 auditable grounds)
    ev_ids = []
    if d.selected_instructional_object:
        for e in observed:
            if e.object == d.selected_instructional_object or e.polarity == "present":
                rec = EvidenceRecord(state_id=state.id, assignment_id=state.assignment_id,
                                     category="OBSERVED", description=e.description,
                                     candidate_instructional_object=e.object,
                                     source="decision_engine", confidence="observed", text_span=None)
                await F.EVIDENCE.insert_one(rec.model_dump())
                ev_ids.append(rec.id)

    _write_decision_onto_state(state, d)
    state.decision_requirement_ids = list(DE_REQS)
    state.decision_timestamp = now_iso()
    state.version += 1
    await F._save_state(state)

    await F._write_audit(AuditEvent(
        state_id=state.id, event_type="instructional_decision", requirement_ids=list(DE_REQS) + ["VA-06"],
        evidence_reviewed=ev_ids, decision=f"{d.decision_status}: {d.selected_instructional_object}",
        rationale=d.priority_rationale, generated_response=(invitation or "")[:1000],
        teacher_override=t_override,
        output_state=d.as_dict(), validation_results=guards,
    ))
    result = d.as_dict()
    result["guards"] = guards
    return result


def _write_decision_onto_state(state: InstructionalState, d: Decision) -> None:
    state.demonstrated_strengths = d.demonstrated_strengths
    state.strength_status = d.strength_status
    state.candidate_instructional_objects = d.candidate_instructional_objects
    state.selected_instructional_object = d.selected_instructional_object
    state.selected_object_definition = d.selected_object_definition
    state.structural_prerequisite_status = d.structural_prerequisite_status
    state.conceptual_prerequisite_status = d.conceptual_prerequisite_status
    state.observed_selection_evidence = d.observed_selection_evidence
    state.priority_rationale = d.priority_rationale
    state.deferred_targets = d.deferred_targets
    state.decision_status = d.decision_status
    state.instructional_need = d.instructional_need
    state.decision_confidence = d.decision_confidence
    state.decision_uncertainty = d.decision_uncertainty
    state.engine_recommendation = d.engine_recommendation


async def apply_teacher_target_override(state_id: str, teacher_id: str, to_object: str,
                                        reason: str = "") -> Dict[str, Any]:
    """TC-02 — record an explicit teacher target override that is stored separately,
    preserves the original engine recommendation, is visible in the trace, and is
    logged append-only. Never treated as evidence about the learner."""
    from compass_foundation import TeacherOverride
    doc = await F.STATES.find_one({"id": state_id}, {"_id": 0})
    if not doc:
        raise ValueError("state not found")
    state = InstructionalState(**doc)
    original = state.selected_instructional_object
    ov = TeacherOverride(teacher_id=teacher_id, field="selected_instructional_object",
                         from_value=original, to_value=to_object, reason=reason)
    state.teacher_overrides.append(ov)
    state.engine_recommendation = original           # preserve original recommendation
    state.selected_instructional_object = to_object  # honor teacher selection
    state.selected_object_definition = OBJECT_DEFINITIONS.get(to_object, "")
    state.decision_status = "TEACHER_OVERRIDE"
    state.instructional_need = "NEEDS_INSTRUCTION"
    state.decision_requirement_ids = list(DE_REQS) + ["TC-02"]
    state.decision_timestamp = now_iso()
    state.version += 1
    await F._save_state(state)
    await F._write_audit(AuditEvent(
        state_id=state.id, event_type="teacher_target_override", requirement_ids=["TC-02"],
        teacher_override=ov.model_dump(), decision=f"override -> {to_object}",
        rationale=reason or "teacher override",
        output_state={"engine_recommendation": original, "selected_instructional_object": to_object},
        validation_results=[{"requirement_id": "TC-02", "passed": True,
                             "detail": "override honored; engine recommendation preserved separately"}],
    ))
    return {"engine_recommendation": original, "selected_instructional_object": to_object,
            "decision_status": "TEACHER_OVERRIDE"}
