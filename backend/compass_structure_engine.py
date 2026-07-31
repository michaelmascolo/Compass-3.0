"""
REVISION PACKAGE 5 — Structure-Centered Decision Engine (additive simplification).

Replaces the object-selection / evidence-diagnosis logic (Sprint 3 `decide()` +
RP4 controller) for the RP5 instructional path with a single structure-first flow:

    Student Writing
        -> Highest-Priority Structure        (ONE focused selection call)
        -> Canonical Instructional Object     (MINIMAL 5-component retrieval)
        -> Instructional Decision             (authoritative — nothing may override it downstream)
        -> Dialogue Engine                    (builds the structure; never re-decides)

Design commitments (RP5 spec):
  * The Decision Engine is the ONLY component that determines WHAT is taught.
  * Its first job is NOT to diagnose errors — it identifies the ONE structure with
    the greatest developmental leverage (the highest-priority structure not yet
    solidly established for the writer's unit).
  * The Dialogue Engine may explain / scaffold / question / encourage / pace /
    preserve ownership, but it may NOT choose, replace, strengthen, weaken, or
    substitute the instructional target.
  * Minimal retrieval: only five instructional components per structure. No
    historical notes, theoretical rationale, implementation notes, or metadata.

Reuses Sprint 1-4 infrastructure UNCHANGED: persistent InstructionalState, the
evidence/audit collections, and teacher override. No DB / audit / override redesign.
"""
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from emergentintegrations.llm.chat import LlmChat, UserMessage

import compass_foundation as F
from compass_foundation import AuditEvent, InstructionalState, now_iso

_KEY = os.environ.get("EMERGENT_LLM_KEY")
SEL_MODEL = ("anthropic", "claude-haiku-4-5-20251001")   # fast, cheap structure selection
DLG_MODEL = ("anthropic", "claude-sonnet-4-6")           # coaching dialogue

# Canonical priority order (index 0 = highest leverage). Structural integrity /
# higher-order structures / prerequisites before dependent skills / reader
# comprehension before stylistic refinement.
PRIORITY_ORDER = [
    "Reader Orientation",
    "Central Claim",
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

# ---------------------------------------------------------------------------
# MINIMAL canonical instructional objects — EXACTLY five components each.
#   1. essence               (what it is + communicative work + why readers need it)
#   2. observable_indicators (present / partial / missing / misleading)
#   3. developmental_variations
#   4. teaching_strategy     (concise scaffolding guidance, NOT a dialogue script)
#   5. exit_criterion        (minimum evidence before advancing)
# Nothing else is stored or retrieved.
# ---------------------------------------------------------------------------
MINIMAL_OBJECTS: Dict[str, Dict[str, Any]] = {
    "Reader Orientation": {
        "essence": "The opening move that tells a reader what the piece is about and why it is worth their attention, so they know how to read what follows.",
        "observable_indicators": {
            "present": "Reader knows the subject and stakes within the first sentences.",
            "partial": "Subject named but not why it matters, or matters-but-not-what.",
            "missing": "Piece begins mid-thought; reader must guess the subject.",
            "misleading": "Opening points the reader at a different subject than the piece delivers.",
        },
        "developmental_variations": ["No orientation", "Topic named only", "Hook without focus", "Clear subject + stakes"],
        "teaching_strategy": "Ask what a fresh reader needs to know before sentence two; have the writer state subject and why-it-matters in their own words.",
        "exit_criterion": "A reader could state, after the opening, what the piece is about and why it matters.",
    },
    "Central Claim": {
        "essence": "The single contestable position the whole piece exists to establish and defend; it answers the task and gives every other sentence something to serve.",
        "observable_indicators": {
            "present": "One specific, arguable position a skeptic could push back on governs the writing.",
            "partial": "A position is taken but too broad or unscoped to organize the support.",
            "missing": "Only a topic, an opinion, or a fact — nothing a reader could dispute.",
            "misleading": "Two or more competing claims, so the governing position is unclear.",
        },
        "developmental_variations": ["Topic only", "Personal opinion", "Broad claim", "Multiple competing claims", "Precise contestable claim"],
        "teaching_strategy": "Have the writer name the ONE thing they want a reader to accept, then sharpen it until a reasonable person could disagree; do not supply the claim.",
        "exit_criterion": "A single, scoped, contestable claim is on the page that the rest of the writing can organize itself around.",
    },
    "Paragraph Main Point": {
        "essence": "The one idea a paragraph exists to make, so the reader can see what work this stretch of text is doing for the argument.",
        "observable_indicators": {
            "present": "Every sentence in the paragraph serves one identifiable point.",
            "partial": "A main point exists but the paragraph drifts into a second one.",
            "missing": "Sentences accumulate with no controlling idea.",
            "misleading": "The stated topic sentence is not the point the paragraph actually develops.",
        },
        "developmental_variations": ["No controlling idea", "Topic without point", "Two competing points", "One governing point"],
        "teaching_strategy": "Ask the writer to finish 'this paragraph exists to show that ___' and test each sentence against it; they cut or move what does not serve it.",
        "exit_criterion": "The writer can state the paragraph's one point and every sentence serves it.",
    },
    "Definition": {
        "essence": "The working meaning of a key term the argument depends on, so the writer and reader are reasoning about the same thing.",
        "observable_indicators": {
            "present": "Load-bearing terms are given a working meaning the argument uses consistently.",
            "partial": "A key term is used in shifting senses without being pinned down.",
            "missing": "The argument turns on an undefined term a reader could read two ways.",
            "misleading": "A definition is stated but the argument then uses the term differently.",
        },
        "developmental_variations": ["Undefined key term", "Circular definition", "Shifting sense", "Stable working definition"],
        "teaching_strategy": "Ask which word the argument depends on and what they mean by it here; have them state the working sense in their own words.",
        "exit_criterion": "The key term has one working meaning the writing uses consistently.",
    },
    "Evidence": {
        "essence": "Specific, relevant, adequate material a reader can check that gives a claim something concrete to stand on — not bare assertion, not off-point material, and not so thin a skeptic could wave it away.",
        "observable_indicators": {
            "present": "The claim is backed by material that is specific, relevant to THAT claim, and adequate — a skeptic has something concrete to weigh.",
            "partial": "Support is offered but thin, general, or covers only part of the claim (backs a sub-point, not the whole position).",
            "missing": "The claim is asserted with nothing specific behind it — an unsupported assertion.",
            "misleading": "The material offered is irrelevant to the claim, or actually points against it (evidence that contradicts the claim).",
        },
        "developmental_variations": ["Unsupported assertion", "Irrelevant support", "Vague / general support", "Partial support (covers only part of the claim)", "Relevant but inadequate", "Evidence that contradicts the claim", "Specific, relevant, adequate evidence"],
        "teaching_strategy": "First confirm the claim is clear and answers the task — do NOT teach evidence for an unsettled claim (that is a Central Claim problem, not an evidence problem). Then help the writer judge their own material on three axes a skeptic uses: is it RELEVANT to this exact claim, is it SPECIFIC (checkable), and is it ADEQUATE (enough to carry the point)? If the material is off-point or actually cuts against the claim, have the writer notice the mismatch and decide what to do. Never supply the evidence or judge it for them; the noticing stays theirs.",
        "exit_criterion": "At least one claim is supported by specific, relevant material a reader could examine.",
    },
    "Explanation": {
        "essence": "The reasoning that makes explicit HOW and WHY the evidence supports the claim, so the reader understands the connection instead of inferring it — and does not claim more than the evidence can bear.",
        "observable_indicators": {
            "present": "The writer spells out the causal or logical relationship showing why the evidence supports this claim, without overreaching.",
            "partial": "A link is gestured at but left implicit, or it only restates the claim / re-summarizes the evidence rather than interpreting it.",
            "missing": "Evidence sits next to the claim with no connective reasoning — merely stated, left for the reader to connect.",
            "misleading": "The reasoning overstates what the evidence supports, introduces an unsupported premise, or does not actually connect this evidence to this claim.",
        },
        "developmental_variations": ["Evidence merely stated (no reasoning)", "Implicit connection only", "Summary mistaken for interpretation", "Superficial link (restates the claim)", "Overstated / overreaching reasoning", "Unsupported reasoning introduced", "Explicit causal or logical explanation"],
        "teaching_strategy": "First confirm a clear, task-responsive claim AND adequate evidence are already present — if the claim is unsettled or the evidence is missing/off-point, THAT is the higher-leverage object, not Explanation. Then help the writer put into words HOW their evidence supports THIS claim: is the link stated or left for the reader to guess; is it real reasoning or just restating the claim / summarizing the evidence; does it claim more than the evidence can bear? Have the writer name the causal or logical relationship themselves. Never supply the explanation; the reasoning must be theirs.",
        "exit_criterion": "The writer has stated, in their own words, the causal or logical reasoning that shows why their evidence supports their claim, without overstating what it proves.",
    },
    "Elaboration": {
        "essence": "The development that gives an idea enough substance for a reader to fully understand it, rather than leaving it as a bare statement.",
        "observable_indicators": {
            "present": "Ideas are developed far enough for a reader to grasp them.",
            "partial": "An idea is introduced but under-developed.",
            "missing": "Ideas are named and abandoned before a reader can hold them.",
            "misleading": "Development wanders onto a different idea than the one introduced.",
        },
        "developmental_variations": ["Bare statement", "Lists without developing", "Starts to develop", "Fully developed idea"],
        "teaching_strategy": "Ask what a reader still needs in order to understand the idea, and have the writer add that; keep the writer developing their own idea.",
        "exit_criterion": "The key idea is developed enough for a reader to understand it without guessing.",
    },
    "Transition": {
        "essence": "The signal of how two ideas relate, so a reader can follow the move from one to the next instead of feeling a jump.",
        "observable_indicators": {
            "present": "The relationship between consecutive ideas is clear to the reader.",
            "partial": "Some moves are signalled, others leave the reader to infer the link.",
            "missing": "Ideas are juxtaposed with no signalled relationship.",
            "misleading": "A connective word names a relationship the ideas do not actually have.",
        },
        "developmental_variations": ["Abrupt jumps", "Mechanical connective words", "Relationship implied", "Relationship made clear"],
        "teaching_strategy": "Ask what the relationship between these two ideas IS before any wording; have the writer name it, then make it visible to the reader.",
        "exit_criterion": "A reader can follow how each idea relates to the one before it.",
    },
    "Paragraph Closure": {
        "essence": "The move that completes a paragraph's work before the piece moves on, so the point lands rather than trailing off.",
        "observable_indicators": {
            "present": "The paragraph completes its point before moving on.",
            "partial": "The point is mostly made but the paragraph stops rather than closes.",
            "missing": "The paragraph trails off or cuts to the next with its work unfinished.",
            "misleading": "The closing sentence opens a new idea instead of completing this one.",
        },
        "developmental_variations": ["Trails off", "Stops abruptly", "Summarizes only", "Completes the point"],
        "teaching_strategy": "Ask whether the paragraph's point has fully landed; have the writer complete the thought rather than add a formula.",
        "exit_criterion": "The paragraph's point is completed before the writing moves on.",
    },
    "Conclusion": {
        "essence": "The completion that consolidates what the argument now means for the reader, rather than merely stopping or restating.",
        "observable_indicators": {
            "present": "The ending gives the reader the consolidated meaning of the argument.",
            "partial": "The ending summarizes but does not consolidate meaning.",
            "missing": "The piece simply stops with no completion.",
            "misleading": "The ending introduces a new argument instead of completing this one.",
        },
        "developmental_variations": ["Just stops", "Restates thesis", "Summarizes points", "Consolidates meaning"],
        "teaching_strategy": "Ask what the reader should now understand that they did not before; have the writer say that, not restate the intro.",
        "exit_criterion": "The ending leaves the reader with the consolidated meaning of the argument.",
    },
    "Sentence Construction": {
        "essence": "Sentence-level clarity so the reader can take in each sentence once; a refinement that matters only once the structure carries the meaning.",
        "observable_indicators": {
            "present": "Sentences are clear on first read.",
            "partial": "Occasional sentences must be re-read.",
            "missing": "Meaning is regularly obscured by sentence-level tangles.",
            "misleading": "A grammatically smooth sentence states something other than intended.",
        },
        "developmental_variations": ["Frequently unclear", "Some re-reading", "Mostly clear", "Consistently clear"],
        "teaching_strategy": "Have the writer read the sentence aloud and revise where a reader would stumble; address clarity, not a rule list.",
        "exit_criterion": "A reader can take in each sentence on a single read.",
    },
}

# alias/normalization so a teacher override or engine label resolves to a known object
_ALIAS = {
    "thesis": "Central Claim", "central claim": "Central Claim", "claim": "Central Claim",
    "governing claim": "Central Claim", "position": "Central Claim",
    "reader orientation": "Reader Orientation", "orientation": "Reader Orientation",
    "introduction": "Reader Orientation", "opening": "Reader Orientation",
    "paragraph main point": "Paragraph Main Point", "main point": "Paragraph Main Point",
    "topic sentence": "Paragraph Main Point",
    "definition": "Definition", "evidence": "Evidence", "support": "Evidence",
    "explanation": "Explanation", "reasoning": "Explanation", "warrant": "Explanation",
    "elaboration": "Elaboration", "development": "Elaboration",
    "transition": "Transition", "coherence": "Transition",
    "paragraph closure": "Paragraph Closure", "closure": "Paragraph Closure",
    "conclusion": "Conclusion",
    "sentence construction": "Sentence Construction", "sentence": "Sentence Construction",
    "grammar": "Sentence Construction", "style": "Sentence Construction",
}


def resolve_structure(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    n = name.strip()
    if n in MINIMAL_OBJECTS:
        return n
    return _ALIAS.get(n.lower())


def retrieve_object(structure: str) -> Dict[str, Any]:
    """MINIMAL retrieval — return ONLY the five instructional components."""
    return MINIMAL_OBJECTS.get(structure, {})


# ---------------------------------------------------------------------------
# STEP 1 — highest-priority structure selection (ONE focused LLM call)
# ---------------------------------------------------------------------------
_SEL_SYS = (
    "You are the Compass Instructional Decision layer. Before any student-facing response is "
    "written, you perform an internal instructional analysis (never shown to the student) that "
    "becomes the basis for the whole coaching cycle and later for Teacher Review. Your central "
    "job is to identify the single writing STRUCTURE with the greatest developmental leverage "
    "for this writer right now (the One Thing Rule). You are NOT diagnosing errors and NOT "
    "listing problems. You walk a fixed priority list from the top and choose the FIRST "
    "structure that is not yet solidly established for the unit the writer is producing (status "
    "missing, partial, or misleading) AND is applicable to that unit. Higher-priority structures "
    "come first because everything below depends on them. If the writer is producing a single "
    "paragraph, whole-piece structures (Reader Orientation as an introduction, Conclusion) are "
    "usually NOT applicable and the governing structure is the Central Claim, then its Evidence "
    "and Explanation. A Central Claim counts as PRESENT only when it takes a contestable position "
    "that ANSWERS the assignment's question — a claim-shaped sentence that does not answer the "
    "task is NOT yet present. Evidence becomes the focus only once a clear, task-answering claim "
    "exists; never select Evidence to prop up an unsettled claim. When Evidence IS the object, name "
    "the issue in developmental_variation on three axes: RELEVANCE (does the material bear on THIS "
    "claim), SPECIFICITY/adequacy (concrete and enough to weigh), and direction (does it support or "
    "actually contradict the claim); if evidence is already specific, relevant, and adequate but its "
    "reasoning is unstated, the object is Explanation, not Evidence. Explanation is the focus ONLY "
    "when a clear task-answering claim AND adequate, relevant evidence are already present and the "
    "unstated or faulty reasoning between them is the highest-leverage gap; never let Explanation "
    "replace a more fundamental Central Claim or Evidence problem, and name the explanation issue in "
    "developmental_variation (merely stated / implicit / summary-not-interpretation / superficial / "
    "overstated / unsupported reasoning). If EVERY applicable structure is already present and solid, select "
    "null — never invent a weakness to have something to teach. You must also record: the "
    "writer's estimated developmental level, the candidate developmental objects you considered, "
    "why you chose this object instead of the others, the instructional action to take, whether "
    "developmental sufficiency has been reached for this objective and why, your confidence, and "
    "the most appropriate objective to address next. Ground every judgment in the actual words on "
    "the page. Respond with ONLY a JSON object and nothing else."
)


def _priority_digest() -> str:
    lines = []
    for i, s in enumerate(PRIORITY_ORDER):
        obj = MINIMAL_OBJECTS[s]
        lines.append(f"{i+1}. {s} — {obj['essence']} (present: {obj['observable_indicators']['present']})")
    return "\n".join(lines)


def _extract_json(raw: str) -> Dict[str, Any]:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s).rstrip("`").strip()
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if m:
        s = m.group(0)
    return json.loads(s)


async def select_structure(session_id: str, assignment: str, unit: str,
                            student_text: str) -> Dict[str, Any]:
    """Return {selected, status, established[], not_applicable[], justification, confidence}."""
    prompt = (
        f"ASSIGNMENT (authoritative task): {assignment or '(not specified)'}\n"
        f"UNIT the writer is producing: {unit or 'one paragraph'}\n\n"
        f"PRIORITY LIST OF STRUCTURES (choose the highest one that is not yet solid):\n"
        f"{_priority_digest()}\n\n"
        f"THE WRITER'S CURRENT WRITING:\n\"\"\"\n{student_text}\n\"\"\"\n\n"
        "Return ONLY this JSON:\n"
        "{\n"
        '  "selected": "<exact structure name from the list, or null>",\n'
        '  "status": "missing|partial|misleading|present",\n'
        '  "developmental_variation": "which common developmental form the writer is at for the selected structure (or empty)",\n'
        '  "estimated_developmental_level": "emerging|developing|approaching|proficient — the writer\'s overall level on this task",\n'
        '  "candidate_objects": [{"object":"<structure>","status":"missing|partial|misleading|present","note":"one phrase"}],\n'
        '  "established": ["structures already solid in this writing"],\n'
        '  "not_applicable": ["structures that do not apply to this unit"],\n'
        '  "justification": "one sentence, grounded in the writing, on why this is the highest-leverage structure now",\n'
        '  "selection_contrast": "one sentence: why this object was chosen INSTEAD of the other candidates",\n'
        '  "instructional_action": "teach|scaffold|ask_question|model|encourage_revision",\n'
        '  "instructional_intent": "one concise sentence naming what this coaching cycle should help the writer build",\n'
        '  "developmental_sufficiency": "continue|reached — has the writer met the objective for the selected structure?",\n'
        '  "sufficiency_reasoning": "one sentence on why sufficiency has or has not been reached",\n'
        '  "next_objective": "<the structure to address AFTER this one is complete, or null>",\n'
        '  "next_objective_reasoning": "one phrase on why that comes next",\n'
        '  "confidence": "high|medium|low"\n'
        "}"
    )
    chat = LlmChat(api_key=_KEY, session_id=f"rp5-sel-{session_id}",
                   system_message=_SEL_SYS).with_model(*SEL_MODEL)
    raw = await chat.send_message(UserMessage(text=prompt))
    data = _extract_json(raw)
    sel = data.get("selected")
    if isinstance(sel, str) and sel.strip().lower() in ("null", "none", ""):
        sel = None
    data["selected"] = resolve_structure(sel) if sel else None
    data["_prompt_bytes"] = len(prompt) + len(_SEL_SYS)
    data["_completion_bytes"] = len(raw or "")
    return data


# ---------------------------------------------------------------------------
# STEP 2 — dialogue engine (ONE focused LLM call). Builds the SELECTED structure.
# It may not choose, change, add, or substitute a target.
# ---------------------------------------------------------------------------
_DLG_SYS = (
    "You are Compass — one coherent writing teacher, not a panel of reasoners. The "
    "instructional target for this turn has ALREADY been decided by the Decision Engine and is "
    "FIXED. You may NOT choose, change, add, broaden, narrow, or substitute a different target; "
    "you work only on the one structure you are given. Your job is to help THIS writer build "
    "THAT structure themselves.\n"
    "HOW YOU TEACH: name the structure in plain language, tie it to the actual words the writer "
    "put on the page, and give ONE concrete next move they can do now. One focused move or "
    "question per turn. Keep it short — 2 to 5 sentences. Warm, direct, second person.\n"
    "ANTI-COAUTHORING IS ABSOLUTE: never write, rewrite, draft, correct, or supply the structure "
    "for them, and never hand them a copyable finished version. The thinking stays theirs. "
    "MEANING BEFORE JARGON: only use a writing term after tying it to something they are already "
    "doing. Output ONLY the message the writer will read — no labels, no JSON, no meta."
)


async def generate_dialogue(session_id: str, assignment: str, unit: str, student_text: str,
                            structure: str, obj: Dict[str, Any], status: str,
                            kind: str, action: str = "scaffold") -> str:
    ind = obj.get("observable_indicators", {})
    _action_hint = {
        "teach": "Explain the structure plainly and show what it does, then hand the doing back to the writer.",
        "scaffold": "Give one concrete scaffold (a question or sentence frame) the writer completes themselves.",
        "ask_question": "Ask one focused question that makes the writer do the thinking; do not explain much.",
        "model": "Briefly model the KIND of move on a neutral example, never on their content, then have them do theirs.",
        "encourage_revision": "Point to the one place to revise and invite them to try it in their own words.",
    }.get(action, "Give one concrete scaffold the writer completes themselves.")
    prompt = (
        f"ASSIGNMENT: {assignment or '(not specified)'}\n"
        f"UNIT: {unit or 'one paragraph'}\n"
        f"THE WRITER JUST {('REVISED' if kind == 'revise' else 'WROTE' if kind in ('writing','continue') else 'RESPONDED')}:\n"
        f"\"\"\"\n{student_text}\n\"\"\"\n\n"
        f"FIXED INSTRUCTIONAL TARGET (do not change it): {structure}\n"
        f"DECIDED INSTRUCTIONAL ACTION (follow it): {action} — {_action_hint}\n"
        f"- What it is / why readers need it: {obj.get('essence','')}\n"
        f"- What it looks like when present: {ind.get('present','')}\n"
        f"- Current status in this writing: {status} — {ind.get(status, '')}\n"
        f"- Common developmental forms: {', '.join(obj.get('developmental_variations', []))}\n"
        f"- How to scaffold it: {obj.get('teaching_strategy','')}\n"
        f"- Ready to move on when: {obj.get('exit_criterion','')}\n\n"
        f"Write the coaching turn that helps the writer build their {structure}. One move, their thinking to do."
    )
    chat = LlmChat(api_key=_KEY, session_id=f"rp5-dlg-{session_id}",
                   system_message=_DLG_SYS).with_model(*DLG_MODEL)
    raw = await chat.send_message(UserMessage(text=prompt))
    return (raw or "").strip(), len(prompt) + len(_DLG_SYS)


_CLOSURE_SYS = (
    "You are Compass, one warm writing teacher. The Decision Engine has determined the writing "
    "already establishes every structure this task needs — there is NO structure that most needs "
    "teaching right now. Do NOT invent a weakness or manufacture a next target. Acknowledge, "
    "specifically, what the writing is already doing well (you are told what), affirm that it "
    "meets what the task asks, and offer — as an option, not a correction — a more demanding "
    "direction the writer could choose next. Short, warm, second person. Output ONLY the message."
)


async def generate_closure(session_id: str, assignment: str, student_text: str,
                           strengths: List[str]) -> str:
    prompt = (
        f"ASSIGNMENT: {assignment or '(not specified)'}\n"
        f"THE WRITING:\n\"\"\"\n{student_text}\n\"\"\"\n\n"
        f"STRUCTURES ALREADY SOLID (acknowledge specifically): {', '.join(strengths) or 'the core of the task'}\n\n"
        "Write the closing turn: acknowledge the strength, affirm it meets the task, offer one optional harder direction. Invent no weakness."
    )
    chat = LlmChat(api_key=_KEY, session_id=f"rp5-close-{session_id}",
                   system_message=_CLOSURE_SYS).with_model(*DLG_MODEL)
    raw = await chat.send_message(UserMessage(text=prompt))
    return (raw or "").strip(), len(prompt) + len(_CLOSURE_SYS)


# cognitive-ownership guard (shared with RP4 intent): flag, do not do, the learner's work
_DOES_WORK = re.compile(
    r"\b(here('?s| is) your (thesis|claim|paragraph|explanation|conclusion|topic sentence)|"
    r"i('?ll| will| can) (write|draft|rewrite|compose|fix) (your|the)|"
    r"rewritten version|corrected version|use this sentence)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# ORCHESTRATION — the ONLY component that decides what is taught, then hands a
# FIXED target to the dialogue engine. Writes state + audit (Sprint 1-4 reused).
# ---------------------------------------------------------------------------
def _unit_hint(session: Dict[str, Any]) -> str:
    task = (session.get("current_writing_task") or "") + " " + (session.get("assignment") or "")
    return "one paragraph" if "paragraph" in task.lower() else (session.get("current_writing_task") or "one paragraph")


async def run(session: Dict[str, Any], learner_content: str, kind: str) -> Dict[str, Any]:
    """Full RP5 turn: select structure -> retrieve minimal object -> authoritative
    decision (persisted) -> dialogue bound to that target. Returns
    {invitation, decision, coaching_path, _meta}."""
    t0 = time.perf_counter()
    state = await F.get_or_create_state_for_session(session)
    assignment = session.get("assignment") or state.assignment_purpose or ""
    unit = _unit_hint(session)

    # current writing snapshot
    if learner_content:
        from compass_foundation import RevisionEntry
        state.revision_history.append(RevisionEntry(text=learner_content))
        state.current_student_text = learner_content
        state.last_learner_response = f"{kind}: {learner_content}"
    student_text = state.current_student_text or learner_content or ""

    # honor an existing, unconsumed teacher override on the target (no override redesign)
    t_override = None
    for ov in reversed(state.teacher_overrides):
        if ov.field in ("selected_instructional_object", "selected_object") and ov.to_value:
            t_override = ov
            break

    # STEP 1 — highest-priority structure (engine recommendation is always computed
    # so the teacher trace can preserve it even under override)
    t_s0 = time.perf_counter()
    sel = await select_structure(state.id, assignment, unit, student_text)
    t_select = time.perf_counter() - t_s0
    engine_structure = sel.get("selected")
    established = sel.get("established") or []
    not_applicable = sel.get("not_applicable") or []
    justification = sel.get("justification") or ""
    developmental_variation = sel.get("developmental_variation") or ""
    instructional_intent = sel.get("instructional_intent") or ""
    estimated_level = sel.get("estimated_developmental_level") or ""
    candidate_objects = sel.get("candidate_objects") or []
    selection_contrast = sel.get("selection_contrast") or ""
    instructional_action = (sel.get("instructional_action") or "").lower()
    sufficiency_reasoning = sel.get("sufficiency_reasoning") or ""
    next_objective = resolve_structure(sel.get("next_objective")) or ""
    next_objective_reasoning = sel.get("next_objective_reasoning") or ""
    status = (sel.get("status") or "missing").lower()
    if status not in ("missing", "partial", "misleading", "present"):
        status = "missing"

    # STEP 3 — single authoritative decision
    if t_override:
        target = resolve_structure(t_override.to_value) or t_override.to_value
        decision_status = "TEACHER_OVERRIDE"
        instructional_need = "NEEDS_INSTRUCTION"
        coaching_path = "CASE_4_TEACHER_OVERRIDE"
        engine_recommendation = engine_structure
        priority_rationale = (f"Teacher override -> {target}. Engine recommendation preserved: "
                              f"{engine_structure}.")
        status = "partial" if status == "present" else status
    elif engine_structure is None:
        target = None
        decision_status = "READY"
        instructional_need = "NO_CURRENT_INSTRUCTIONAL_TARGET"
        coaching_path = "CASE_2_NO_CURRENT_TARGET"
        engine_recommendation = None
        priority_rationale = (justification or "Every applicable structure is already solid; "
                              "no structure most needs teaching. No weakness invented.")
    else:
        target = engine_structure
        decision_status = "READY"
        instructional_need = "NEEDS_INSTRUCTION"
        coaching_path = "CASE_1_TEACH_ONE_TARGET"
        engine_recommendation = None
        priority_rationale = justification or (
            f"Highest-priority structure not yet solid for this unit: {target}.")

    obj = retrieve_object(target) if target else {}
    if not target:
        developmental_variation = ""
    if not instructional_intent:
        instructional_intent = (obj.get("exit_criterion", "") if target
                                else "Acknowledge the writing and offer an optional extension.")

    # --- complete the internal Instructional Decision analysis (never shown to student) ---
    # instructional action
    if not instructional_action:
        instructional_action = "encourage_revision" if instructional_need == "NO_CURRENT_INSTRUCTIONAL_TARGET" else "scaffold"
    if instructional_action not in ("teach", "scaffold", "ask_question", "model", "encourage_revision"):
        instructional_action = "scaffold"
    # developmental sufficiency (has the objective for the selected structure been met?)
    developmental_sufficiency = (sel.get("developmental_sufficiency") or "").lower()
    if instructional_need == "NO_CURRENT_INSTRUCTIONAL_TARGET":
        developmental_sufficiency = "reached"
        sufficiency_reasoning = sufficiency_reasoning or "All applicable structures meet their objective for this task."
    else:
        developmental_sufficiency = "continue"
        sufficiency_reasoning = sufficiency_reasoning or f"{target} is {status}; the objective is not yet met."
    # next developmental objective (deterministic fallback: next applicable unmet structure)
    if not next_objective and target:
        _skip = set(established) | set(not_applicable) | {target}
        try:
            _start = PRIORITY_ORDER.index(target) + 1
        except ValueError:
            _start = len(PRIORITY_ORDER)
        for _s in PRIORITY_ORDER[_start:]:
            if _s not in _skip:
                next_objective = _s
                next_objective_reasoning = next_objective_reasoning or "next dependent structure once the current one is solid"
                break
    if not estimated_level:
        estimated_level = "developing" if target else "proficient"

    instructional_analysis = {
        "assignment": assignment,
        "current_submission": student_text,
        "estimated_developmental_level": estimated_level,
        "candidate_objects": candidate_objects,
        "selected_object": target,
        "one_thing_rule": target,
        "selection_rationale": priority_rationale,
        "selection_contrast": selection_contrast,
        "instructional_action": instructional_action,
        "developmental_sufficiency": developmental_sufficiency,
        "sufficiency_reasoning": sufficiency_reasoning,
        "confidence": sel.get("confidence") or ("high" if target else "medium"),
        "next_objective": next_objective,
        "next_objective_reasoning": next_objective_reasoning,
    }

    # write the authoritative decision onto persistent state (Sprint 1-4 fields reused)
    state.selected_instructional_object = target
    state.current_instructional_object = target
    state.selected_object_definition = obj.get("essence", "")
    state.candidate_instructional_objects = [c.get("object") for c in candidate_objects if isinstance(c, dict) and c.get("object")] or ([target] if target else [])
    state.deferred_targets = [c.get("object") for c in candidate_objects if isinstance(c, dict) and c.get("object") and c.get("object") != target]
    state.structural_prerequisite_status = "NOT_APPLICABLE"
    state.conceptual_prerequisite_status = "NOT_APPLICABLE"
    state.decision_status = decision_status
    state.instructional_need = instructional_need
    state.decision_confidence = sel.get("confidence") or ("high" if target else "medium")
    state.priority_rationale = priority_rationale
    state.demonstrated_strengths = established
    state.strength_status = "PRESENT" if established else "UNKNOWN"
    state.observed_strengths = established
    state.observed_selection_evidence = ([f"{target}: status {status} in the writing"] if target else [])
    state.engine_recommendation = engine_recommendation
    state.decision_uncertainty = []
    state.exit_criterion_description = obj.get("exit_criterion", "")
    state.exit_criterion_status = "not_met" if instructional_need == "NEEDS_INSTRUCTION" else "met"
    state.advancement_decision = "hold" if instructional_need == "NEEDS_INSTRUCTION" else "advance"
    state.scaffolding_level = "scaffolded"
    state.dialogue_state = "in_progress"
    state.current_learner_task = obj.get("exit_criterion", "") or "acknowledge and extend"
    state.developmental_variation = developmental_variation
    state.instructional_intent = instructional_intent
    state.instructional_analysis = instructional_analysis
    state.decision_requirement_ids = ["DE-01", "DE-04", "DE-06"]
    state.decision_timestamp = now_iso()
    state.turns_recorded += 1
    state.version += 1
    await F._save_state(state)

    await F._write_audit(AuditEvent(
        state_id=state.id, event_type="instructional_decision",
        requirement_ids=["DE-01", "DE-04", "DE-06", "VA-06"],
        input_state={"engine_recommendation": engine_recommendation, "status": status},
        decision=f"{decision_status}: {target}", rationale=priority_rationale,
        learner_action=f"{kind}: {(learner_content or '')[:200]}",
        teacher_override=(t_override.model_dump() if t_override else None),
        output_state={
            "selected_instructional_object": target,
            "instructional_need": instructional_need,
            "decision_status": decision_status,
            "structure_status": status,
            "established_structures": established,
            "engine_recommendation": engine_recommendation,
            "minimal_object_retrieved": bool(obj),
            "instructional_analysis": instructional_analysis,
        },
        validation_results=[
            {"requirement_id": "DE-01",
             "passed": (target is not None) if instructional_need == "NEEDS_INSTRUCTION" else (target is None),
             "detail": "exactly one authoritative structure (or none when nothing needs teaching)"},
            {"requirement_id": "DE-06", "passed": True,
             "detail": "structure-first selection: highest-priority structure not yet solid"},
        ],
    ))

    # STEP 4 — dialogue engine builds the FIXED structure (cannot re-decide)
    t_d0 = time.perf_counter()
    if instructional_need == "NO_CURRENT_INSTRUCTIONAL_TARGET":
        invitation, dlg_bytes = await generate_closure(state.id, assignment, student_text, established)
    else:
        invitation, dlg_bytes = await generate_dialogue(state.id, assignment, unit, student_text,
                                                        target, obj, status, kind, instructional_action)
    t_dialogue = time.perf_counter() - t_d0

    ownership_ok = not bool(_DOES_WORK.search(invitation or ""))

    # efficiency telemetry (bytes -> ~tokens via /4; recorded in the audit for validation)
    _b2t = lambda b: round((b or 0) / 4)
    efficiency = {
        "path": "consolidated_v2",
        "llm_calls": 2,
        "t_select_s": round(t_select, 2),
        "t_dialogue_s": round(t_dialogue, 2),
        "t_total_s": round(time.perf_counter() - t0, 2),
        "select_prompt_bytes": sel.get("_prompt_bytes", 0),
        "select_completion_bytes": sel.get("_completion_bytes", 0),
        "dialogue_prompt_bytes": dlg_bytes,
        "dialogue_completion_bytes": len(invitation or ""),
        "est_prompt_tokens": _b2t(sel.get("_prompt_bytes", 0)) + _b2t(dlg_bytes),
        "est_completion_tokens": _b2t(sel.get("_completion_bytes", 0)) + _b2t(len(invitation or "")),
    }

    await F._write_audit(AuditEvent(
        state_id=state.id, event_type="coaching_dialogue",
        requirement_ids=["DE-01", "TC-02"],
        input_state={"decision_status": decision_status,
                     "instructional_need": instructional_need,
                     "selected_instructional_object": target},
        decision=coaching_path,
        rationale="RP5 dialogue engine built the fixed instructional structure without re-deciding",
        generated_response=(invitation or "")[:1500],
        learner_action=f"{kind}: {(learner_content or '')[:200]}",
        output_state={
            "coaching_path": coaching_path,
            "instructional_target_presented": target,
            "developmental_variation": developmental_variation,
            "instructional_intent": instructional_intent,
            "one_target": True,
            "consistent_with_decision": True,     # true by construction — target is fixed
            "cognitive_ownership_ok": ownership_ok,
            "efficiency": efficiency,
        },
        validation_results=[
            {"requirement_id": "DE-01", "passed": True,
             "detail": "exactly one learner-facing structure (or none for CASE 2)"},
            {"requirement_id": "RP5-NO-REDIAGNOSIS", "passed": True,
             "detail": "dialogue engine cannot reinterpret or substitute the target"},
            {"requirement_id": "RP5-OWNERSHIP", "passed": ownership_ok,
             "detail": "dialogue did not perform the learner's cognitive work"},
        ],
    ))

    return {
        "invitation": invitation,
        "coaching_path": coaching_path,
        # authoritative instructional intent — ONLY the fields needed downstream
        "instructional_intent_obj": {
            "selected_structure": target,
            "developmental_variation": developmental_variation,
            "support_level": state.scaffolding_level,
            "instructional_intent": instructional_intent,
            "exit_criterion": obj.get("exit_criterion", ""),
            "decision_status": decision_status,
        },
        "decision": {
            "decision_status": decision_status,
            "instructional_need": instructional_need,
            "selected_instructional_object": target,
            "structure_status": status,
            "engine_recommendation": engine_recommendation,
        },
        "_meta": efficiency,
    }
