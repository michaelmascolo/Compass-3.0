"""
REVISION PACKAGE 4 — Coaching controller (isolated, additive).

Makes the learner-facing coaching turn CONSUME the Sprint-3 structured decision
instead of independently inferring what to teach. It does NOT redesign Stage C, the
dialogue, the scaffolding sequences, or the CIO knowledge base. It selects one of the
mandated response PATHS from the stored decision and gates/adjusts the learner-facing
text accordingly:

  CASE 1  READY + NEEDS_INSTRUCTION              -> use the frozen engine's single-target
                                                    coaching invitation (unchanged).
  CASE 2  READY + NO_CURRENT_INSTRUCTIONAL_TARGET-> acknowledge strengths; invent no weakness.
  CASE 3  BLOCKED_*                              -> gather only the needed evidence; no teaching.
  CASE 4  TEACHER_OVERRIDE                       -> focus on the teacher-selected target
                                                    (engine recommendation preserved in audit).

The controller never re-diagnoses and never substitutes a different target; it consumes
the decision as computed for THIS turn. It never performs the learner's cognitive work.
"""
import re
from typing import Any, Dict, List, Tuple

# Cognitive-ownership guard: controller-authored text must never do the learner's work.
_DOES_WORK = re.compile(
    r"\b(here('?s| is) your (thesis|claim|paragraph|explanation|conclusion|topic sentence)|"
    r"i('?ll| will| can) (write|draft|rewrite|compose|fix) (your|the)|"
    r"try this[:] |rewritten version|corrected version|use this sentence)\b",
    re.IGNORECASE,
)


def _strengths_phrase(strengths: List[str]) -> str:
    s = [x for x in (strengths or []) if x]
    if not s:
        return "you've engaged seriously with this task"
    if len(s) == 1:
        return s[0].rstrip(".").lower() if s[0][:1].islower() else s[0].rstrip(".")
    return f"{s[0].rstrip('.')}; {s[1].rstrip('.').lower()}"


def _case2_text(decision: Dict[str, Any]) -> str:
    return (
        f"You've done real work here — {_strengths_phrase(decision.get('demonstrated_strengths'))}. "
        "Right now I don't see one clear thing that most needs teaching: your writing is meeting what "
        "this task is asking for. If you'd like to push further, you could take on a more demanding "
        "version of this prompt, start a fresh draft, or try a different kind of writing. Otherwise, "
        "this is a genuinely good place to be."
    )


def _case3_text(decision: Dict[str, Any]) -> str:
    status = decision.get("decision_status", "")
    if status == "BLOCKED_CONTRADICTORY_EVIDENCE":
        return ("I'm getting mixed signals from the draft about what you're mainly trying to say. "
                "In one sentence, in your own words, what is the main point you want a reader to take "
                "away? That will help me point you to the most useful next step.")
    if status == "BLOCKED_PREREQUISITE_UNKNOWN":
        return ("I want to make sure we work on the right thing. Could you say a little more about what "
                "you're setting up here and why? Once that's clearer on the page, I can suggest one "
                "focused next step.")
    # BLOCKED_INSUFFICIENT_EVIDENCE (default)
    return ("Before I suggest one focused next step, I need to see a bit more of your thinking on the "
            "page. Keep drafting — even a rough version is fine — and share it so I can understand what "
            "you're aiming to say.")


def _case4_text(decision: Dict[str, Any]) -> str:
    target = decision.get("selected_instructional_object") or "this focus"
    definition = decision.get("selected_object_definition") or ""
    tail = f" ({definition})" if definition else ""
    return (
        f"Let's focus on your {target}{tail}. Look back at your draft with that specifically in mind, "
        f"and revise so it does that job. Tell me what you change and why — the thinking is yours to do."
    )


def _mentions_target(text: str, target: str) -> bool:
    if not target:
        return False
    key = target.lower().split("—")[0].strip()
    head = key.split()[0] if key else ""
    return bool(head) and head in (text or "").lower()


def select_response(decision: Dict[str, Any], engine_invitation: str) -> Dict[str, Any]:
    """Return {learner_text, coaching_path, one_target, cognitive_ownership_ok,
    consistent_with_decision, instructional_target_presented}."""
    status = decision.get("decision_status", "")
    need = decision.get("instructional_need", "")
    target = decision.get("selected_instructional_object")

    if status == "TEACHER_OVERRIDE":
        text = _case4_text(decision)
        path = "CASE_4_TEACHER_OVERRIDE"
        presented = target
    elif status == "READY" and need == "NO_CURRENT_INSTRUCTIONAL_TARGET":
        text = _case2_text(decision)
        path = "CASE_2_NO_CURRENT_TARGET"
        presented = None
    elif status.startswith("BLOCKED"):
        text = _case3_text(decision)
        path = "CASE_3_BLOCKED_GATHER_EVIDENCE"
        presented = None
    else:  # READY + NEEDS_INSTRUCTION -> the frozen engine's single-target dialogue
        text = engine_invitation
        path = "CASE_1_TEACH_ONE_TARGET"
        presented = target

    # controller-authored text (CASE 2/3/4) must never do the learner's work
    author_ownership_ok = True
    if path != "CASE_1_TEACH_ONE_TARGET":
        author_ownership_ok = not bool(_DOES_WORK.search(text or ""))

    # consistency: for the teaching path, confirm the presented dialogue is about the
    # decided target (both derive from the same turn's reasoning; never substituted).
    consistent = True
    if path == "CASE_1_TEACH_ONE_TARGET" and target:
        consistent = _mentions_target(text, target)

    return {
        "learner_text": text,
        "coaching_path": path,
        "instructional_target_presented": presented,
        "one_target": True,                       # controller never presents >1 target
        "cognitive_ownership_ok": author_ownership_ok,
        "consistent_with_decision": consistent,
    }
