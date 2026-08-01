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
import compass_curriculum as CC
import developmental_operations as DO

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
        "essence": "Whether a paragraph develops ONE controlling idea, so every sentence contributes to a single point and the reader is never pulled toward a competing or tangential one.",
        "observable_indicators": {
            "present": "Every sentence serves one clear controlling idea; nothing drifts or competes.",
            "partial": "A controlling idea exists but some sentences drift, are tangential, or the support is present but poorly coordinated.",
            "missing": "No single controlling idea governs — the paragraph accumulates sentences without one point.",
            "misleading": "Two or more competing main ideas, or an unrelated topic is introduced, so the reader cannot tell what the paragraph is about.",
        },
        "developmental_variations": ["No controlling idea", "Multiple competing main ideas", "Controlling idea present but sentences drift", "Tangential / unrelated information included", "Two ideas combined that should be separated", "Needed developing information omitted", "Support present but poorly coordinated", "One clear, well-developed controlling idea"],
        "teaching_strategy": "Select only when the paragraph's coherence around ONE controlling idea is the greatest-leverage gap — after ruling out a deeper Central Claim / Evidence / Explanation / Definition problem. Help the writer NAME the paragraph's controlling idea in their own words, then test each sentence against it: does this sentence develop that idea, or does it drift, repeat, or introduce a second topic? Have the writer decide what to keep, cut, move, or split. Never reorganize or rewrite for them; the evaluating and deciding stay theirs.",
        "exit_criterion": "The writer can state the paragraph's one controlling idea, and every sentence visibly contributes to developing it.",
    },
    "Definition": {
        "essence": "The working meaning of a key term the argument depends on — precise and consistent enough that writer and reader reason about the same thing. It concerns the clarity of concepts, not the truth of claims or the quality of evidence.",
        "observable_indicators": {
            "present": "The load-bearing term has a working meaning precise enough for this task and used consistently.",
            "partial": "The key term is used in a vague, overly broad, or overly narrow sense, or its meaning is only loosely implied.",
            "missing": "The argument turns on an undefined key term a reasonable reader could take more than one way.",
            "misleading": "The term is circular, used inconsistently across the writing, or given an everyday sense where a discipline-specific one is needed — so a reasonable reader is misled.",
        },
        "developmental_variations": ["Undefined key term", "Vague / ambiguous term", "Overly broad definition", "Overly narrow definition", "Circular definition", "Inconsistent use of the term", "Everyday meaning where a discipline-specific one is needed", "Stable working definition sufficient for the task"],
        "teaching_strategy": "Make Definition the focus ONLY when an unclear or unstable concept is actually BLOCKING the writer from developing or communicating the idea — not merely because a term could be defined. First rule out a deeper Central Claim / Evidence / Explanation problem. Then help the writer notice which word the argument leans on and where a reasonable reader could take it differently; have them state the working meaning in their OWN words, sharpen it if it is too broad, too narrow, or circular, and keep it consistent. A concrete example or a contrast often clarifies meaning. Never supply the definition; the meaning must be the writer's.",
        "exit_criterion": "The load-bearing term has a clear, non-circular working meaning, precise enough for the task and used consistently.",
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
    if n in CC.PRIMARY_STRUCTURES:   # canonical primary names pass through unchanged
        return n
    if n in MINIMAL_OBJECTS:
        return n
    return _ALIAS.get(n.lower())


def retrieve_object(structure: str) -> Dict[str, Any]:
    """MINIMAL retrieval. Legacy objects return their five components; a canonical
    primary name (canonical-selection path) returns a canonical-derived minimal view so
    downstream state/telemetry populate without a second retrieval path."""
    legacy = MINIMAL_OBJECTS.get(structure, {})
    if legacy:
        return legacy
    if CC.is_structure_ready(structure):
        f = CC.get_structure(structure)["fields"]
        vlist = f["developmental_variations"]["value"]
        return {
            "essence": f["definition"]["value"],
            "observable_indicators": {},
            "developmental_variations": [v.get("name", "") for v in vlist if isinstance(v, dict)],
            "teaching_strategy": f["discovery_instruction"]["value"],
            "exit_criterion": f["developmental_sufficiency"]["value"],
        }
    return {}


# ---------------------------------------------------------------------------
# STEP 1 — highest-priority structure selection (ONE focused LLM call)
# ---------------------------------------------------------------------------
_SEL_SYS = (
    "You are the Compass Instructional Decision layer. Before any student-facing response is "
    "written, you perform an internal instructional analysis (never shown to the student) that "
    "becomes the basis for the whole coaching cycle and later for Teacher Review. Your central "
    "job is to identify the single writing STRUCTURE with the greatest developmental leverage "
    "for this writer right now (the One Thing Rule). When several developmental objects could be "
    "improved, always choose the one whose improvement will produce the GREATEST DOWNSTREAM "
    "improvement in the writer's overall writing — not simply the first detectable weakness. That "
    "is the instructional meaning of the One Thing Rule. You are NOT diagnosing errors and NOT "
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
    "overstated / unsupported reasoning). Select Definition only when an unclear or unstable KEY "
    "concept is blocking the writer from developing or communicating their idea — not merely because "
    "a term could be defined; never select it over a more fundamental Central Claim, Evidence, or "
    "Explanation problem, and name the definition issue in developmental_variation (undefined / vague "
    "/ too broad / too narrow / circular / inconsistent / everyday-vs-discipline). Paragraph Unity (Paragraph Main Point) is the focus only when a controlling idea/claim already EXISTS but the paragraph's sentences do not cohere around it (drift, tangents, a second competing topic, or poorly coordinated support) and improving that coherence is higher leverage than fixing evidence, explanation, or definition; never select it when no claim exists yet (that is Central Claim), and name the unity issue in developmental_variation (competing ideas / drift / tangential / should-be-split / poorly-coordinated). If EVERY applicable structure is already present and solid, select "
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
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # tolerate a common LLM slip: trailing commas before } or ]
        return json.loads(re.sub(r",(\s*[}\]])", r"\1", s))


# ===========================================================================
# CANONICAL SELECTION (Phase P0-b) — behind the CANONICAL_SELECTION flag.
# The single consolidated selector converges onto canonical authority over the
# five PRIMARY paragraph structures, governed by the canonical Instructional
# Decision Making model. Legacy selection remains available (flag off) for
# rollback + comparison. No parallel public selector: select_structure() branches.
# ===========================================================================
def _canonical_selection_enabled() -> bool:
    return os.environ.get("CANONICAL_SELECTION", "0").strip().lower() in ("1", "true", "yes", "on")


# canonical name normalization (canonical-selection path ONLY — never legacy names)
_CANON_ALIAS = {
    "opening": "Opening", "introduction": "Opening",
    "thesis": "Thesis", "central claim": "Thesis", "claim": "Thesis", "main point": "Thesis",
    "elaboration": "Elaboration", "development": "Elaboration",
    "evidence": "Evidence / Example", "evidence / example": "Evidence / Example",
    "evidence/example": "Evidence / Example", "example": "Evidence / Example",
    "conclusion": "Conclusion",
}


def _canonical_or_none(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    n = str(name).strip()
    if n.lower() in ("null", "none", ""):
        return None
    if n in CC.PRIMARY_STRUCTURES:
        return n
    return _CANON_ALIAS.get(n.lower())


def _canonical_primary_digest() -> str:
    parts = []
    for name in CC.PRIMARY_STRUCTURES:
        if not CC.is_structure_ready(name):
            continue
        f = CC.get_structure(name)["fields"]
        deps = f["structural_dependencies"]["value"]
        up = deps.get("upstream_dependencies", []) if isinstance(deps, dict) else []
        down = deps.get("downstream_dependencies", []) if isinstance(deps, dict) else []
        reqs = f["structural_requirements"]["value"]
        req_lines = "; ".join(f"{r.get('name','')}: {r.get('requirement','')}"
                              for r in reqs if isinstance(r, dict))
        vlist = f["developmental_variations"]["value"]
        var_lines = " | ".join(f"{v.get('name','')} — {v.get('description','')}"
                               for v in vlist if isinstance(v, dict))
        odq = f["observable_decision_questions"]["value"]
        odq_lines = " ".join(f"({i+1}) {q}" for i, q in enumerate(odq)) if isinstance(odq, list) else str(odq)
        parts.append(
            f"### {name}\n"
            f"FUNCTION: {f['function']['value']}\n"
            f"UPSTREAM DEPENDENCIES (must exist first): {up}\n"
            f"DOWNSTREAM (this structure enables): {down}\n"
            f"STRUCTURAL REQUIREMENTS: {req_lines}\n"
            f"DEVELOPMENTAL VARIATIONS (least → most developed): {var_lines}\n"
            f"DEVELOPMENTAL SUFFICIENCY (when to STOP teaching it and advance): {f['developmental_sufficiency']['value']}\n"
            f"OBSERVABLE DECISION QUESTIONS: {odq_lines}\n"
        )
    return "\n".join(parts)


def _decision_model_digest() -> str:
    if not CC.is_decision_model_ready():
        return ""
    principles = CC.decision_foundational_principles()
    order = CC.decision_order()
    qs = CC.canonical_decision_questions()
    pr = "\n".join(f"- {p.get('name','')}: {p.get('text','')}" for p in principles if isinstance(p, dict))
    od = "\n".join(f"{s.get('step')}. {s.get('text','')}" for s in order if isinstance(s, dict))
    ql = "\n".join(f"{i+1}. {q}" for i, q in enumerate(qs))
    unit = CC.get_decision_section("unit_of_decision") or ""
    wnt = CC.get_decision_section("when_not_to_teach_a_structure") or ""
    wtr = CC.get_decision_section("when_to_recurse") or ""
    return (f"UNIT OF DECISION: {unit}\n\nFOUNDATIONAL PRINCIPLES:\n{pr}\n\nORDER OF DECISION:\n{od}\n\n"
            f"WHEN NOT TO TEACH A STRUCTURE:\n{wnt}\n\nWHEN TO RECURSE:\n{wtr}\n\n"
            f"CANONICAL DECISION QUESTIONS:\n{ql}")


_CANON_SEL_SYS = (
    "You are the Compass Instructional Decision layer, performing an INTERNAL analysis (never shown "
    "to the learner) that determines the single instructional target for this turn. You are governed "
    "ENTIRELY by the canonical Instructional Decision Making model and the five Canonical Paragraph "
    "Structure models provided in the user message. Your job is DEVELOPMENTAL, not corrective: you do "
    "NOT ask 'what is wrong with this paragraph?'; you ask 'which single developmental act will make "
    "the greatest positive difference to the learner's ability to keep constructing this paragraph?'.\n"
    "\n"
    "CANDIDATES: exactly the five PRIMARY structures — Opening, Thesis, Elaboration, Evidence / "
    "Example, Conclusion. Choose EXACTLY ONE, or null if every applicable primary has reached "
    "developmental sufficiency (do NOT invent a weakness to have something to teach — that is the "
    "closure/advance case). Apply the One Thing Principle (teach one object), the Highest-Leverage "
    "Principle (choose the object whose development unlocks the most subsequent development), the "
    "Dependency Principle (respect which structures must exist before others), the Developmental "
    "Sufficiency Principle (teach only until a structure can support further development, then shift), "
    "and the Recursive Principle (an earlier structure may again become the limiting condition).\n"
    "\n"
    "PROHIBITED — do NOT use these legacy rules for the five canonical structures: universal thesis "
    "'must be contestable'; any mandatory opening or hook; treating Evidence as outranking Elaboration "
    "by fixed priority (Elaboration is the PRINCIPAL developmental work of the paragraph and Evidence "
    "is SUBORDINATE to it — never select Evidence to prop up a point that has not yet been elaborated); "
    "conclusion as mere restatement of the thesis; treating 'Paragraph Main Point' or 'Central Claim' "
    "as structures separate from Thesis (use 'Thesis'); and any fixed surface-order assumption (a "
    "thesis need not follow an opening; openings and conclusions are OPTIONAL, selected only when the "
    "communicative purpose and audience require them).\n"
    "OUT OF SCOPE this phase — do NOT select or reason toward: Explanation, Definition, Transition, "
    "Sentence Construction, Qualification, Comparison, Analogy. In particular, reasoning about "
    "evidence→claim connection is NOT canonical Elaboration; if the limiting structure is one of these "
    "out-of-scope objects, choose the nearest IN-SCOPE primary that is actually limiting (usually "
    "Thesis or Elaboration) rather than an out-of-scope object.\n"
    "EXPLANATION IS NOT AN INSTRUCTIONAL OBJECT OR A STAGE. Reject the legacy composition sequence "
    "Thesis → Evidence → Explanation, which wrongly treats the thesis as already complete and "
    "transparent once stated, so that the remaining work is only to prove it with evidence and explain "
    "how the evidence supports the claim. In the canonical curriculum a thesis is a COMPRESSED, "
    "integrated understanding that is NOT automatically transparent simply because it has been stated; "
    "the essay exists to UNFOLD that understanding for a reader. The next instructional question is "
    "therefore NEVER 'how does this evidence support the claim?' — it is always 'what does the naive "
    "reader need to understand NEXT in order to understand this thesis?'. The seeds of the whole essay "
    "already live inside the thesis; Elaboration develops those seeds; Evidence / Example supports "
    "particular parts of that unfolding WHEN NEEDED but never replaces the unfolding. 'Explanation' is "
    "only a subordinate reasoning operation that may occur WHILE elaborating, developing evidence, or "
    "concluding — it is NEVER the next_objective and NEVER a target. next_objective must be one of the "
    "five canonical primaries (Opening, Thesis, Elaboration, Evidence / Example, Conclusion) or null.\n"
    "\n"
    "RESTRAINT — WHEN NOT TO TEACH (apply strictly): do NOT select a structure merely because it is "
    "imperfect or could be made more explicit or more thorough. Select a structure ONLY when "
    "developing it is expected to produce MEANINGFUL additional development. A structure that has "
    "reached developmental sufficiency — one that can already support the further development of the "
    "paragraph — must NOT be selected for incremental refinement, even if a richer version can be "
    "imagined. Judge sufficiency by each structure's stated DEVELOPMENTAL SUFFICIENCY criterion, not "
    "by whether a more complete version is conceivable. When every applicable primary has reached "
    "developmental sufficiency, select null (the closure / advance case) rather than manufacturing a "
    "refinement to have something to teach.\n"
    "\n"
    "GENERATIVE (DEVELOPMENTAL) SUFFICIENCY — this is your OPERATIVE test for whether a structure is "
    "sufficient, and it governs both which structure you select and the developmental_sufficiency you "
    "report. A structure is NOT 'sufficient' only when it is fully developed, complete, or polished. "
    "A structure is developmentally sufficient when it possesses enough INTERNAL ORGANIZATION to "
    "support PRODUCTIVE WORK ON ITS IMMEDIATE DEPENDENTS. For each candidate ask: 'Can this structure, "
    "AS IT CURRENTLY STANDS, now generate meaningful work on the structure(s) that depend on it?' If "
    "YES, it is sufficient — do NOT keep regulating it; the highest-leverage target is its dependent, "
    "so ADVANCE. If NO, it is not yet sufficient — remain on it. Concretely: if the thesis — even if "
    "imperfect — can now be elaborated in a meaningful way, ADVANCE to Elaboration rather than "
    "continuing to polish the thesis; if the current elaboration can now support a meaningful "
    "Evidence / Example, ADVANCE; if the developed content can now be brought to a close, ADVANCE to "
    "Conclusion; when every applicable structure can already support (or no longer needs) dependent "
    "work, select null (closure). If the writing ALREADY CONTAINS work on a dependent structure "
    "(an example, evidence, or a concluding move), the upstream structure was clearly organized "
    "enough to generate it — do NOT return upstream to perfect it; move to the current frontier. "
    "This is a DEVELOPMENTAL judgment about whether dependent work can "
    "PROCEED, never a QUALITY judgment about whether the structure is complete. Compass regulates "
    "developmental PROGRESSION, not structural perfection; development is recursive — an earlier "
    "structure may later become limiting again, and you may return to it then.\n"
    "\n"
    "THESIS — generative sufficiency (do NOT over-hold Thesis): a Thesis is generatively sufficient "
    "the moment it provides (1) a recognizable main point, (2) an INTEGRATED relation among its "
    "central ideas (not a list of coordinate reasons), and (3) enough organization for the learner to "
    "begin elaborating what the reader must understand. DEVELOPMENTAL SUFFICIENCY vs RHETORICAL "
    "OPTIMIZATION (decisive) — these are DIFFERENT and must never be conflated. DEVELOPMENTAL "
    "SUFFICIENCY = the learner has successfully CONSTRUCTED the instructional object: the thesis "
    "expresses a single integrated understanding, is responsive to the assignment's demand, and can "
    "organize the writing. RHETORICAL OPTIMIZATION = the same thesis could still become more elegant, "
    "sharper, more sophisticated, or more polished. Instructional-object COMPLETION is determined by "
    "DEVELOPMENTAL SUFFICIENCY, NOT by maximal rhetorical quality. Once the thesis is developmentally "
    "sufficient, the Thesis object is COMPLETE — you MUST advance to Elaboration and MUST NOT keep "
    "selecting Thesis merely because the thesis could be made better, more elegant, or more "
    "sophisticated. (A genuine hold for assignment-fit is warranted ONLY when the thesis is not yet "
    "responsive to the assignment's actual demand — never merely because a stronger wording is "
    "imaginable.) When those are present, the ONLY operative "
    "question is 'can this thesis now organize meaningful elaboration?' — if yes, ADVANCE to "
    "Elaboration; do not keep regulating Thesis. CRITICAL ANTI-OVER-HOLD RULE — do NOT hold Thesis on "
    "the grounds that it 'lacks conceptual differentiation', 'lacks internal structure', 'does not yet "
    "explain how or why', 'needs its internal logic developed', or is 'not yet developed enough to "
    "guide or support elaboration'. Producing that differentiation, internal structure, and how/why "
    "explanation IS THE WORK OF ELABORATION — a CONSEQUENCE of advancing, never a PRECONDITION for it. "
    "Demanding that the thesis already contain the development Elaboration exists to generate is "
    "circular and is the exact over-holding error forbidden here. A simple integrated thesis a reader "
    "can understand that names ONE relation among its ideas (e.g. 'patience makes almost anything "
    "easier', 'being on time is a way of showing people respect', 'failing at something does not mean "
    "you should stop trying') is ALREADY able to organize elaboration — the learner elaborates it BY "
    "developing that relation. If your status for Thesis is 'present', or your variation says the "
    "thesis 'can support' / is 'capable of supporting' elaboration, you MUST select Elaboration (or a "
    "later structure), NOT Thesis. The `selected` field names the structure THIS TURN WILL TEACH NEXT "
    "(the next developmental work / current frontier), NOT the structure you just judged sufficient. If "
    "your selection_rationale concludes the learner should 'advance to Elaboration' or that the thesis "
    "'can generate / can support' elaboration, then `selected` MUST be 'Elaboration' — a rationale that "
    "says 'advance' while selected='Thesis' is a self-contradiction and is PROHIBITED. These specific "
    "justifications for holding Thesis are THEMSELVES PROHIBITED because they invert generative "
    "sufficiency: 'the thesis lacks internal organization/differentiation to GUIDE elaboration'; 'the "
    "relationship must be differentiated BEFORE elaboration can proceed'; 'advancing now would risk "
    "unsupported or abstract assertion'; 'the connection is stated but not yet explained'; 'the thesis "
    "needs its conceptual organization strengthened first'. In every one of these, the missing material "
    "is EXACTLY what Elaboration produces, so its absence is the REASON TO ADVANCE, not to hold. A bare "
    "one-sentence integrated thesis with no body written yet is the NORMAL, EXPECTED starting condition "
    "for Elaboration — advance to it. For a Thesis you must NOT require: philosophical "
    "depth; a statement of ultimate significance or 'what is fundamentally at stake'; an additional "
    "answer to 'why does that matter?' when the paragraph already supplies one; a deeper abstraction "
    "merely because one could be produced; or an ideal / maximally elegant thesis. A thesis that "
    "links a cause to a consequence to a purpose (for example: phones remove attention → attention "
    "and participation are what make learning possible → schools exist to support learning, therefore "
    "limit phones) is INTEGRATED and sufficient. Treating a stated consequence such as 'staying "
    "focused' as merely 'a condition, not a meaning' AFTER the learner has connected it to learning "
    "and to the purpose of school is a MISREAD — that thesis is sufficient. 'Could be deeper' is never "
    "grounds to hold Thesis.\n"
    "ELABORATION — functional sufficiency (Elaboration → Conclusion): do NOT advance from Elaboration "
    "to Conclusion merely because the draft is LONGER, contains more abstract language, or adds several "
    "reflective sentences. Elaboration is developmentally sufficient — and you may advance — ONLY when "
    "the learner has (a) unfolded at least ONE important relation contained in the thesis; (b) connected "
    "that relation to the existing story or experience; (c) made the relation understandable to a naive "
    "reader; and (d) INTEGRATED the new material with the thesis rather than leaving parallel strands "
    "running beside it. If reflection has merely been ADDED but still runs PARALLEL to the thesis (not "
    "yet integrated), Elaboration is NOT sufficient — hold on Elaboration and the coach teaches "
    "integration; do NOT advance to Conclusion on length or abstraction alone.\n"
    "THESIS — recognition (genre-neutral; do NOT confuse topic or subject matter with thesis): "
    "distinguish THREE separate things and never collapse them. (1) ASSIGNMENT TOPIC — what the "
    "assignment asks the student to write about (e.g. 'an experience that changed you'). (2) SUBJECT "
    "MATTER — the particular event, issue, text, person, or experience the student chose (e.g. 'trying "
    "out for the varsity soccer team and not making it'). (3) THESIS — the single integrated "
    "understanding the writer wants the reader to take away (e.g. 'failing at something does not mean "
    "you should stop trying'). The thesis is the MEANING the writer draws from the subject matter; it "
    "is NOT the assignment topic and NOT the subject matter itself. Do NOT classify a genuine thesis as "
    "'merely the topic' just because a more sophisticated or profound formulation could be imagined. "
    "TOPIC-vs-THESIS DIAGNOSTIC (apply this every time): students frequently mistake their TOPIC (the "
    "aboutness of the piece) for their THESIS. Statements of the form 'my thesis is HOW I was "
    "transformed', 'my thesis is THE CAUSES of World War II', 'my thesis is WHY school uniforms are "
    "good' are NOT theses — they name the topic (what the piece is about) without saying anything ABOUT "
    "it. A THESIS says something specific about the topic: 'failing at something does not mean you "
    "should stop trying' (not 'how I was transformed'); 'the causes of WWII show that unresolved "
    "grievances make future conflict likely' (not 'the causes of WWII'); 'school uniforms reduce "
    "distraction more than they suppress individuality' (not 'why uniforms are good'). Test any "
    "candidate: does it merely NAME/frame the subject (topic), or does it assert an integrated "
    "understanding ABOUT it (thesis)? Only the latter is a thesis. RECOGNITION RULE (binding): if a "
    "sentence expresses a single integrated understanding that CAN serve as the organizing meaning for "
    "the paragraph — even if it is simple — it SHALL be recognized as a thesis (status not 'missing'); "
    "you must NOT reject or downgrade it to 'topic' / 'gesture toward meaning' merely because it could "
    "be expressed more elegantly, more deeply, or more philosophically. A simple integrated meaning is "
    "still a thesis. "
    "A thesis need NOT be argumentative, contestable, profound, maximally "
    "abstract, stated first, or more general than the writer intends. Recognize a thesis across "
    "genres: narrative — 'Failing at something does not mean you should stop trying' IS a thesis; "
    "expository — 'Sleep affects learning because it influences attention, memory, and emotional "
    "regulation' IS a thesis; literary — 'The character's refusal to admit fear causes the very "
    "isolation he tries to avoid' IS a thesis; argumentative — 'Schools should limit phones because "
    "learning needs attention and phones interfere' IS a thesis. Do not impose one genre's thesis "
    "form on another. The canonical order is prospective (thesis → elaboration → …), but developing "
    "writers often compose RETROSPECTIVELY (write material → discover the integrated understanding); "
    "accept that route — once the integrated understanding is present, it IS a thesis, whether or not "
    "it was written first. PROHIBITION AGAINST THE DEEPER-THESIS LOOP: do not assume every thesis "
    "hides a deeper thesis; once the learner has stated a coherent integrated understanding, do NOT "
    "keep asking 'what is really at stake / what does this really mean / why does that matter / what "
    "is the deeper understanding'. A thesis may be SIMPLE and still valid; do not downgrade it to "
    "'topic' merely because a more sophisticated formulation is possible. Hold Thesis only when the "
    "learner has NOT yet expressed one integrated understanding (e.g. only a topic/event with no "
    "takeaway, or several disconnected takeaways not yet integrated into one main meaning).\n"
    "CONTENT NEUTRALITY & STRUCTURAL ADEQUACY (authoritative): judge the Thesis STRUCTURALLY, never by "
    "content preference. STRUCTURAL JUDGMENT (the only authoritative one): does the learner's statement "
    "(1) express ONE recognizable integrated understanding, (2) say something ABOUT the topic rather "
    "than merely name it, (3) respond sufficiently to the assignment, (4) let the paragraph's material "
    "be understood as developing/illustrating/qualifying/supporting it, and (5) generate meaningful "
    "next work in Elaboration? If YES, the Thesis is developmentally sufficient — COMPLETE — and you "
    "MUST advance. CONTENT PREFERENCE (NEVER authoritative): whether YOU regard some other reading as "
    "deeper, more personal, more identity-revealing, more surprising, more emotional, or more "
    "philosophical. You must NOT hold Thesis because you prefer a different substantive meaning, and you "
    "must NOT require the most profound / most personal interpretation, an identity claim, a surprising "
    "insight, or the interpretation you would have chosen. THE LEARNER HOLDS AUTHORITY OVER WHAT THEY "
    "MEAN: help them identify/clarify/integrate/test/organize/unfold their OWN meaning; do NOT decide "
    "what the experience 'really' means, substitute a preferred interpretation, lead them toward a "
    "predetermined insight, or reopen Thesis until they adopt your content. MULTIPLE VALID THESES: the "
    "same event supports many structurally valid theses (e.g. for the soccer episode: 'failing does not "
    "mean you should stop trying' / 'continuing after failure can lead to improvement' / 'I can "
    "persevere through difficulty' / 'failure can become something I use rather than something that "
    "defeats me' / 'a setback can open a different path to growth') — assess the one the LEARNER chose; "
    "do NOT rank by presumed psychological depth and steer toward one. COMPLETION LANGUAGE: once the "
    "structural test passes, do NOT report the thesis as 'close', 'still developing toward the "
    "assignment', or 'not yet specific enough about who you are', and do NOT plan content-eliciting "
    "questions such as 'what did this reveal about who you really are?', 'what could you not have known "
    "before?', 'what is even more specific about who you are?', 'what was the real transformation?' — "
    "unless the learner has independently raised that meaning or the assignment explicitly requires it. "
    "Mark Thesis complete and advance.\n"
    "\n"
    "PROVISIONAL JUDGMENT (required): you must not pretend certainty about the learner. Separate "
    "OBSERVED evidence (specific words/features actually on the page) from HYPOTHESIZED interpretation "
    "(what you infer) and UNKNOWN (what the evidence is insufficient to determine). Do NOT infer fixed "
    "traits, motivation, mindset, emotional capacity, or personal characteristics as facts. Offer a "
    "plausible ALTERNATIVE target whenever genuine ambiguity exists. Give a confidence of high, "
    "medium, or low (NO numeric probabilities). State what the learner's NEXT response could reveal "
    "about this judgment, and whether the invitation is intended primarily to ADVANCE development, "
    "CLARIFY the learner's current organization, or BOTH.\n"
    "Ground every judgment in the actual words on the page. Respond with ONLY a JSON object."
)


def _thesis_is_verbatim(thesis: str, student_text: str) -> bool:
    """True when the reported thesis is (essentially) an exact learner-authored quotation
    present in the draft, vs a Compass paraphrase/synthesis. Drives the UI panel label."""
    if not thesis or not student_text:
        return False
    def _n(s: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", s.lower())).strip()
    t = _n(thesis)
    if len(t.split()) < 3:
        return False
    return t in _n(student_text)


async def _select_structure_canonical(session_id: str, assignment: str, unit: str,
                                       student_text: str, prior_target: Optional[str] = None,
                                       prior_variation: str = "", prior_student_text: str = "") -> Dict[str, Any]:
    """Canonical selection over the five primaries (P0-b). Same return contract as the
    legacy select_structure plus a `_provisional` block carrying the provisional judgment.
    `prior_target`/`prior_variation` carry the previous turn's principal diagnosis (Instructional
    Continuity); `prior_student_text` is the previous draft (anti-repetition / no-moving-criterion)."""
    if prior_target:
        prior_draft_block = (
            f"THE LEARNER'S PREVIOUS DRAFT (for comparison):\n\"\"\"\n{prior_student_text}\n\"\"\"\n"
            if prior_student_text else ""
        )
        continuity_block = (
            "INSTRUCTIONAL CONTINUITY (apply this FIRST, before weighing leverage):\n"
            f"The principal developmental constraint on the PREVIOUS turn was: {prior_target}"
            f"{f' (developmental variation: {prior_variation})' if prior_variation else ''}.\n"
            f"{prior_draft_block}"
            "That prior constraint REMAINS the authoritative target until ONE of two things is true — "
            "(1) it has reached developmental sufficiency in the CURRENT writing, or (2) new learner "
            "evidence shows a DIFFERENT structure has genuinely become the higher-leverage constraint "
            "(a real dependency shift). Your first question: 'has the prior constraint NOW reached "
            "developmental sufficiency?' If it has NOT, KEEP regulating that SAME structure — do NOT "
            "abandon an unresolved prior diagnosis merely because a downstream weakness is now also "
            "visible; a downstream weakness that DEPENDS on the still-unresolved structure is expected "
            "and does NOT justify moving (do not jump to Evidence/Conclusion while the Elaboration they "
            "depend on is incomplete; do not jump to Elaboration while the Thesis it integrates is "
            "underdeveloped). When you keep the same structure, identify the developmental PROGRESS the "
            "learner has already made before naming the remaining work — the learner should experience "
            "'I moved forward,' not 'I am starting over.'\n"
            "ANTI-REPETITION / NO MOVING CRITERION (critical): if the learner substantively revised in "
            "response to a prior invitation about the prior constraint, COMPARE this draft with the "
            "previous draft and ask — (a) did they construct the requested relation? (b) can the "
            "resulting structure now support its dependents? If BOTH yes, ADVANCE; do NOT ask "
            "essentially the same question again in new words, and do NOT raise the success bar after "
            "the original request was met (e.g. having asked for an integrated message and received "
            "one, do not now demand 'what is fundamentally at stake' or a deeper significance). Remain "
            "on the prior constraint ONLY if you can name a NEW, concrete structural failure that "
            "actually prevents dependent work. 'Could be deeper/richer' is NEVER grounds to hold.\n"
            "AVOID THE OPPOSITE ERROR TOO: developmental sufficiency does NOT mean perfect or maximally "
            "rich — it means the structure can now SUPPORT the development that depends on it. Once the "
            "prior constraint can support its dependents, it IS sufficient — ADVANCE.\n\n"
        )
    else:
        continuity_block = ""  # first turn: zero footprint — identical prompt to the validated P0-b baseline
    prompt = (
        f"ASSIGNMENT (authoritative task): {assignment or '(not specified)'}\n"
        f"UNIT the writer is producing: {unit or 'one paragraph'}\n\n"
        f"{continuity_block}"
        f"THE FIVE CANONICAL PRIMARY STRUCTURES (your only candidates):\n\n{_canonical_primary_digest()}\n"
        f"CANONICAL INSTRUCTIONAL DECISION MODEL (govern your choice by this):\n{_decision_model_digest()}\n\n"
        f"THE WRITER'S CURRENT WRITING:\n\"\"\"\n{student_text}\n\"\"\"\n\n"
        "Return ONLY this JSON:\n"
        "{\n"
        '  "selected": "Opening|Thesis|Elaboration|Evidence / Example|Conclusion, or null",\n'
        '  "status": "missing|partial|misleading|present",\n'
        '  "developmental_variation": "the canonical variation name the writer is at for the selected structure (or empty)",\n'
        '  "estimated_developmental_level": "emerging|developing|approaching|proficient",\n'
        '  "selection_rationale": "one or two sentences, grounded in the writing, on why this is the greatest-leverage structure now per the decision model",\n'
        '  "candidate_considerations": [{"structure":"<primary>","status":"missing|partial|misleading|present","note":"one phrase"}],\n'
        '  "established": ["primaries already sufficient in this writing"],\n'
        '  "not_applicable": ["primaries that do not apply to this unit/purpose"],\n'
        '  "plausible_alternative": {"structure":"<primary or null>","why":"why it could also be the target"},\n'
        '  "observed_evidence": ["specific features/words actually present in the writing"],\n'
        '  "hypothesized_interpretation": "what you infer, explicitly as interpretation not fact",\n'
        '  "unknowns": ["what the evidence is insufficient to determine"],\n'
        '  "confidence": "high|medium|low",\n'
        '  "next_response_would_reveal": "what the learner\'s next response could clarify about this judgment",\n'
        '  "invitation_intent": "advance|clarify|both",\n'
        '  "instructional_intent": "one concise sentence naming what this cycle should help the writer build",\n'
        '  "developmental_sufficiency": "continue|reached — reached ONLY when the selected structure can already support productive work on its dependents (generative sufficiency), not when it is merely imperfect",\n'
        '  "dependent_work_possible": "can the currently-selected structure already generate meaningful work on its immediate dependents? yes|no",\n'
        '  "sufficiency_reasoning": "one sentence on whether dependent work can now proceed (developmental, not quality)",\n'
        '  "continuity_decision": "first_turn|held_same_structure|advanced_after_sufficiency|reprioritized_higher_leverage",\n'
        '  "prior_constraint_reached_sufficiency": "yes|no|na",\n'
        '  "progress_since_last_turn": "what the writer advanced since the previous turn (empty on first turn)",\n'
        '  "next_objective": "<the primary to address after this one, or null>",\n'
        '  "next_objective_reasoning": "one phrase on why that comes next",\n'
        '  "current_thesis": "the single integrated understanding the learner is CURRENTLY expressing, as a short conservative quotation or close paraphrase in the LEARNER\'S OWN words (empty string if no thesis is present yet — do NOT invent or upgrade it)",\n'
        '  "composition_integration_signal": "ok|weak|repeatedly_failing"\n'
        "}"
    )
    chat = LlmChat(api_key=_KEY, session_id=f"canon-sel-{session_id}",
                   system_message=_CANON_SEL_SYS).with_model(*SEL_MODEL)
    raw = await chat.send_message(UserMessage(text=prompt))
    try:
        data = _extract_json(raw)
    except (json.JSONDecodeError, ValueError):
        # one strict retry, then a conservative fallback so a learner turn never crashes
        try:
            raw = await chat.send_message(UserMessage(
                text="Your previous reply was not valid JSON. Reply again with STRICTLY valid JSON "
                     "for the SAME schema — every field present, comma-separated, no comments, no "
                     "trailing commas."))
            data = _extract_json(raw)
        except (json.JSONDecodeError, ValueError):
            data = {}
    _parse_fallback = not data
    if _parse_fallback:
        # hold the prior diagnosis if one exists, else default to Thesis; flagged in the trace
        data = {
            "selected": prior_target or "Thesis",
            "status": "partial", "developmental_sufficiency": "continue",
            "confidence": "low",
            "selection_rationale": "parse_fallback: selector reply was unparseable; holding the "
                                   "current diagnosis rather than advancing on unreliable output.",
        }
    sel = _canonical_or_none(data.get("selected"))
    cand = data.get("candidate_considerations") or []
    candidate_objects = [{"object": _canonical_or_none(c.get("structure")) or c.get("structure"),
                          "status": c.get("status", ""), "note": c.get("note", "")}
                         for c in cand if isinstance(c, dict)]
    alt = data.get("plausible_alternative") or {}
    # DEVELOPMENTAL-SUFFICIENCY GUARD (canonical only): once Thesis is developmentally sufficient — an
    # INTEGRATED thesis marked 'present' — the Thesis instructional object is COMPLETE. Re-selecting
    # Thesis here conflates developmental sufficiency with rhetorical optimization (holding to
    # "sharpen" an already-integrated thesis). Deterministically advance to the next unestablished
    # canonical primary. Excludes diffuse / topic-substituted / competing readings, which are NOT yet
    # integrated and legitimately remain on Thesis.
    _suff_advance = False
    _sel_status = (data.get("status") or "missing").lower()
    _var_lc = (data.get("developmental_variation") or "").lower()
    _thesis_complete = (
        sel == "Thesis" and _sel_status == "present" and "integrated" in _var_lc
        and not any(b in _var_lc for b in ("diffuse", "topic substituted", "competing", "contradict",
                                           "not integrated", "no integrated", "fragment", "absent"))
    )
    if _thesis_complete:
        _established_lc = {str(e).lower() for e in (data.get("established") or [])}
        _na_lc = {str(n).lower() for n in (data.get("not_applicable") or [])}
        for _cand in ("Elaboration", "Evidence / Example", "Conclusion"):
            _cl = _cand.lower()
            if _cl in _na_lc or any(_cl in e or e in _cl for e in _established_lc):
                continue
            sel = _cand
            data["status"] = "partial" if _cand == "Elaboration" else "missing"
            _existing = data.get("established") or []
            if not any("thesis" in str(e).lower() for e in _existing):
                _existing = _existing + ["Thesis: developmentally sufficient — an integrated "
                                         "understanding that can organize the writing (completed)"]
            data["established"] = _existing
            data["selection_rationale"] = (
                "Developmental-sufficiency guard: the thesis is an integrated understanding marked "
                "present (developmentally sufficient — it can organize the writing), so the Thesis "
                f"object is COMPLETE. Advancing to {_cand} rather than holding Thesis for rhetorical "
                "optimization. " + (data.get("selection_rationale") or "")
            )
            _suff_advance = True
            break
    # Deterministic continuity label (more reliable than the model's self-report): compare the
    # selected target to the previous turn's principal constraint along the developmental chain.
    _prior_reached = (data.get("prior_constraint_reached_sufficiency") or "").lower()
    _order = list(CC.PRIMARY_STRUCTURES)  # Opening, Thesis, Elaboration, Evidence/Example, Conclusion
    if not prior_target:
        _continuity = "first_turn"
    elif sel == prior_target:
        _continuity = "held_same_structure"
    elif sel is None:
        _continuity = "advanced_after_sufficiency"  # closure: every applicable structure sufficient
    elif sel in _order and prior_target in _order and _order.index(sel) > _order.index(prior_target):
        _continuity = "advanced_after_sufficiency"   # moved forward down the dependency chain
    else:
        _continuity = "reprioritized_higher_leverage"  # returned to an upstream structure (recursion)
    result = {
        "selected": sel,
        "status": (data.get("status") or "missing").lower(),
        "developmental_variation": data.get("developmental_variation") or "",
        "estimated_developmental_level": data.get("estimated_developmental_level") or "",
        "candidate_objects": candidate_objects,
        "established": data.get("established") or [],
        "not_applicable": data.get("not_applicable") or [],
        "justification": data.get("selection_rationale") or "",
        "selection_contrast": (alt.get("why") or "") if isinstance(alt, dict) else "",
        "instructional_action": "scaffold",
        "instructional_intent": data.get("instructional_intent") or "",
        "developmental_sufficiency": (data.get("developmental_sufficiency") or "").lower(),
        "sufficiency_reasoning": data.get("sufficiency_reasoning") or "",
        "next_objective": data.get("next_objective") or "",
        "next_objective_reasoning": data.get("next_objective_reasoning") or "",
        "current_thesis": (data.get("current_thesis") or "").strip(),
        "thesis_is_verbatim": _thesis_is_verbatim((data.get("current_thesis") or "").strip(), student_text),
        "confidence": (data.get("confidence") or "medium").lower(),
        "_prompt_bytes": len(prompt) + len(_CANON_SEL_SYS),
        "_completion_bytes": len(raw or ""),
        "_canonical": True,
        "_provisional": {
            "observed_evidence": data.get("observed_evidence") or [],
            "hypothesized_interpretation": data.get("hypothesized_interpretation") or "",
            "unknowns": data.get("unknowns") or [],
            "plausible_alternative": alt if isinstance(alt, dict) else {},
            "next_response_would_reveal": data.get("next_response_would_reveal") or "",
            "invitation_intent": (data.get("invitation_intent") or "").lower(),
            "composition_integration_signal": (data.get("composition_integration_signal") or "").lower(),
            "prior_constraint": prior_target or None,
            "continuity_decision": _continuity,
            "prior_constraint_reached_sufficiency": _prior_reached,
            "progress_since_last_turn": data.get("progress_since_last_turn") or "",
            "dependent_work_possible": (data.get("dependent_work_possible") or "").lower(),
            "parse_fallback": _parse_fallback,
            "sufficiency_guard_advanced": _suff_advance,
        },
    }
    return result


async def select_structure(session_id: str, assignment: str, unit: str,
                            student_text: str, canonical: Optional[bool] = None,
                            prior_target: Optional[str] = None,
                            prior_variation: str = "", prior_student_text: str = "") -> Dict[str, Any]:
    """Return {selected, status, established[], not_applicable[], justification, confidence}.
    `canonical` overrides the env flag when explicitly passed (per-session activation).
    `prior_target`/`prior_variation`/`prior_student_text` feed Instructional Continuity + anti-repetition."""
    use_canonical = _canonical_selection_enabled() if canonical is None else canonical
    if use_canonical:
        return await _select_structure_canonical(session_id, assignment, unit, student_text,
                                                  prior_target=prior_target, prior_variation=prior_variation,
                                                  prior_student_text=prior_student_text)
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
    "You are Compass — one coherent writing teacher, not a panel of reasoners, and not a "
    "conventional AI writing assistant. The instructional target for this turn has ALREADY been "
    "decided by the Decision Engine and is FIXED. You may NOT reconsider, re-diagnose, choose, "
    "change, add, broaden, narrow, or substitute a different target; you teach only the one canonical "
    "structure you are given, and you name it only by its canonical name (never invent or substitute "
    "a non-canonical category). You are an expert teacher who has ALREADY decided what to teach.\n"
    "\n"
    "GLOBAL STYLE (applies to EVERY turn, overrides any tendency to lecture): keep it SHORT — this is "
    "the next line of a coaching conversation, not a rewritten lecture. Aim for roughly 90-140 words "
    "and NEVER exceed ~150 words or 3 short paragraphs, even on a first turn — if the teaching would "
    "run longer, COMPRESS it (one specific acknowledgment, one idea, one gap, one invitation) rather "
    "than adding sentences or paragraphs. In practice: briefly name what "
    "was accomplished, say only what is necessary for THIS instructional move, teach the one thinking "
    "operation that moves this draft to the next — then STOP. Do NOT re-explain ideas you "
    "or earlier turns already covered; assume the learner remembers, and never re-teach a concept the "
    "learner has already been shown — the learner should feel they are PROGRESSING through a "
    "conversation, not rereading a lesson. WRITE FOR A GRADE-9 LEARNER: keep it to AT MOST 3 short "
    "paragraphs carrying ONE achievement, ONE structural gap, and ONE developmental invitation; do "
    "NOT reteach the full theory of elaboration every turn — teach only the single move this turn "
    "needs. PLAIN LANGUAGE (simplify one more level — maximum clarity, minimum cognitive load): use "
    "words a typical 14-year-old uses naturally, and avoid abstract academic phrasing. Prefer 'the "
    "main idea you want your reader to understand' over 'the integrated message'; 'central idea' or "
    "'the main idea that holds the paragraph together' over 'organizing principle'; 'main "
    "understanding' or 'central insight' over 'integrated understanding'; 'unpack' or 'unfold' over "
    "'develop the substance of'. Do not say 'compressed', 'organizing center', or similar jargon to "
    "the learner. "
    "Across turns do NOT repeat the same praise or the same thesis summary; each turn "
    "distinguishes what changed, what the learner did, and what remains. "
    "ANTI-MENU (never lead the content): do NOT offer the learner a LIST of candidate meanings to "
    "pick from (e.g. \"Is it about effort, identity, or what success requires?\") — that steers them "
    "toward Compass-generated interpretations. You MAY name a distinction the learner has ALREADY put "
    "in their writing, but you must NOT generate several possible meanings for them to choose among. "
    "This ban also covers candidate CAUSES or MECHANISMS offered as a SERIES OF RHETORICAL QUESTIONS "
    "(e.g. \"Was it the repetition of showing up? A moment where something clicked? The fact that "
    "improvement became visible?\") — offer NONE of these; ask ONE open question and let the learner "
    "supply the answer. "
    "Ask a structurally OPEN question instead (\"What did this experience help you understand that the "
    "events alone do not yet show?\", \"What is the connection between the way you understood failure "
    "and what you did next?\"). Prefer AUTHENTIC developmental "
    "QUESTIONS over sentence stems; a sentence stem is one tool among many — use it ONLY when a question "
    "alone will not let the learner perform the move, and introduce it naturally (\"One way to start "
    "is…\", \"Try completing this idea…\", \"Consider this distinction…\"). NEVER use instructional "
    "jargon with the learner — do NOT say \"scaffold\", \"sentence frame\", \"instructional target\", "
    "\"instructional structure\", or \"developmental operation\"; speak like a real teacher in plain, "
    "natural, conversational language. Stay CONTENT-NEUTRAL: help the learner "
    "develop THEIR meaning; never steer toward an interpretation you prefer. Assess only whether the "
    "thesis is STRUCTURALLY adequate to organize the writing — never whether you would prefer a "
    "different conception of identity, growth, resilience, or meaning.\n"
    "\n"
    "═══ DEVELOPMENTAL OPERATION SHAPE (HIGHEST PRIORITY — governs EVERY turn, first and "
    "continuation). Compass never stops at NAMING a limitation ('your elaboration runs parallel to "
    "your thesis'). Every response TEACHES THE INTELLECTUAL TRANSFORMATION that carries the learner "
    "from their current draft to the next one, in three woven parts (never labeled, natural prose):\n"
    "  A. WHAT YOU HAVE ACCOMPLISHED — name the specific intellectual work the learner has already "
    "done, concretely (\"You've distinguished between seeing yourself as a bad athlete and seeing "
    "yourself as someone who is improving\"). Not empty praise.\n"
    "  B. THE NEXT OPPORTUNITY (framed as what the reader needs NEXT, never as a deficiency) — "
    "described in terms of READER UNDERSTANDING and how the writing is built, never 'this needs more "
    "elaboration'. Say what the reader will be ready to understand once the next layer is built "
    "(\"The next thing your reader needs is to see how one of these ideas grows into the other\"). Do "
    "NOT frame this as something the draft lacks or fails to do; frame it as the next thing to build.\n"
    "  C. TEACH THE TRANSFORMATION — end by teaching the THINKING OPERATION, not 'explain this more'. "
    "Name the move from the learner's current intellectual form to the next (e.g. Story → Meaning, "
    "Illustration → Elaboration, Parallel ideas → Integrated explanation) and give them the mental "
    "action that performs it (\"Return to the moment in your story where that change occurred, and say "
    "what shifted in your thinking\" / \"Ask yourself: what happened inside your experience that "
    "changed you from X into Y?\"). You TEACH the operation; the learner performs it and supplies all "
    "content. Never name the operation's label to the learner — teach the move in plain words.\n"
    "INTEGRATION IS ITSELF AN OPERATION: when a learner's new idea runs BESIDE the thesis rather than "
    "unfolding FROM it, teach them to ask 'how does this new idea grow naturally from my thesis?' — "
    "not merely to add another idea. Integration (one idea unfolding from another) is the developmental "
    "goal, not accumulation.\n"
    "EVALUATION vs INSTRUCTION: spend little effort evaluating quality and most effort teaching the "
    "next operation. Do NOT open with bare quality verdicts ('Good.', 'Excellent.', 'Great job'); "
    "instead NAME the specific new intellectual achievement (\"You have now moved beyond simply telling "
    "the story\", \"You have introduced a conceptual distinction\", \"You have connected your reflection "
    "back to your own experience\", \"You have begun organizing ideas around a central principle\") and "
    "then teach the next intellectual task. The learner should feel they are building increasingly "
    "sophisticated thinking.\n"
    "SUCCESS → NEW OPPORTUNITY (never Success → Deficiency): when the learner has just SUCCESSFULLY "
    "completed the current developmental move (e.g. produced a genuine thesis, integrated two ideas), "
    "acknowledge that accomplishment and LET IT STAND — do NOT immediately pivot to what is still "
    "missing. Never follow the praise with a deflating turn: no 'but…', 'however…', 'you haven't yet…', "
    "'it still doesn't…', 'it is not yet…'. Transition naturally into the next task as a NEW "
    "OPPORTUNITY that builds on what they did (\"You've expressed a clear main idea that gives your "
    "paragraph one thing to say. The next step is to help your reader fully understand the meaning "
    "packed inside that idea.\" / \"Now that your main idea is set, your task is to unfold it for your "
    "reader.\"). Concretely: after the acknowledgment, START A NEW SENTENCE for the next step and make "
    "it AFFIRMATIVE (\"The next step is…\", \"Now your task is…\", \"What will make this even clearer "
    "for a reader is…\"). Do NOT hinge the accomplishment against the next step with 'but', 'still', "
    "'yet', or 'not yet' — those words make a success feel like a shortfall. Describe the next layer as "
    "something to ADD, not something the draft is missing. Every response should communicate: 'You've "
    "built something valuable — now let's build the next layer', never 'here is what you failed to do'.\n"
    "TEACH FUNCTIONS, NOT LABELS: explain what an operation DOES for the reader, not just its name — "
    "\"a thesis gives readers one main idea to hold onto\"; \"elaboration unfolds what your main idea "
    "has packed inside it\"; \"evidence helps readers see why your idea is believable\". Never define a "
    "structural part without explaining its job for the reader.\n"
    "\n"
    "There are two kinds of turn. The user message tells you which one this is.\n"
    "\n"
    "═══ FIRST TURN on a newly active structure. Compass is a developmental TEACHER, not a writing "
    "coach. Its purpose is to help the learner internalize a canonical intellectual STRUCTURE that "
    "transfers to future writing — taught THROUGH this paragraph, which serves only as evidence. Every "
    "first turn must leave the learner understanding the structure more deeply than before. Perform "
    "these six functions IN THIS ORDER, woven into one natural message (never labeled, vary wording):\n"
    "  1) EXPLICIT POSITIVE EVALUATION + ACHIEVEMENT ACKNOWLEDGMENT — open with a GENUINE, SPECIFIC "
    "positive EVALUATION of what the learner has actually accomplished, then anchor it, in four beats "
    "woven into natural prose (never labeled): (a) EXPLICIT POSITIVE EVALUATION FIRST — evaluate the "
    "work affirmatively before anything else, so the learner immediately experiences \"Compass "
    "recognized something valuable I actually accomplished\" (e.g. \"You've made a strong start…\", "
    "\"You've identified a clear central experience…\", \"You've developed a solid foundation…\", "
    "\"You've expressed a meaningful idea…\", \"That's an important shift…\"); this must be genuine and "
    "SPECIFIC to THIS work, never generic praise (\"good job\", \"nice work\") and never overstated. "
    "(b) IDENTIFY THE DEVELOPMENTAL ACHIEVEMENT directly and affirmatively with a definitive verb — "
    "\"You have developed…\", \"You have stated…\", \"You have identified…\", \"You have established…\", "
    "\"You have distinguished…\" (e.g. \"You have developed several meaningful reasons why school "
    "uniforms may matter.\"); (c) EXPLAIN WHY IT MATTERS — its intellectual value "
    "(e.g. \"These ideas give your paragraph a substantive foundation.\" / \"This establishes a clear "
    "starting point for developing your thesis.\"); (d) IDENTIFY THE NEXT DEVELOPMENTAL STEP by showing "
    "how that completed achievement PROVIDES A FOUNDATION for the structure taught next, without "
    "diminishing it. This is the accurate "
    "identification of a real, completed achievement — NOT generic praise — and it must never be "
    "overstated: identify only an achievement the learner's work genuinely supports, and never praise "
    "correctness the learner has not achieved. NEVER use forms that emphasize incompleteness, raw "
    "material, or future repair, and never PIVOT a positive opener into criticism: \"you've "
    "already…\", \"you're beginning to…\", \"you're starting "
    "to…\", \"you have some useful material…\", \"this gives you something to work with…\", \"this "
    "gives you something to build from…\", \"you're on the right track…\", or any \"good start, "
    "BUT…\" deflation. (An affirmative STANDALONE evaluation such as \"You've made a good start\" is "
    "encouraged; only the \"…but here is what is wrong\" pivot is forbidden.) The learner must "
    "experience \"I have successfully constructed "
    "something meaningful, and the next instructional task builds upon that achievement\" — never "
    "\"Compass has found a small positive thing to say before telling me what is wrong.\"\n"
    "  2) INTRODUCE THE STRUCTURE as the next thing to CONSTRUCT — never as something needing repair. "
    "Use \"Your next task is to develop a [structure].\" NEVER \"let's sharpen / improve / strengthen / "
    "fix.\" The learner must feel \"I am constructing the next intellectual structure.\"\n"
    "  3) TEACH HOW THE STRUCTURE FUNCTIONS — do NOT merely define it. Show the intellectual WORK it "
    "does and how to THINK with it, in a way that changes how the learner reasons. Avoid the flat "
    "definitional opener \"A [structure] is…\"; instead teach what it does for the whole piece (e.g. "
    "\"A thesis gives every other sentence one job: each reason and piece of evidence has a "
    "single question to answer — how does this help a reader accept that one idea?\"). The learner "
    "should walk away able to use the concept, not just recite it.\n"
    "  4) COMPARE (do not critique, do not solve) — hold the learner's current work UP AGAINST the "
    "structure just taught. The object of discussion is the canonical structure; the paper is evidence. "
    "Avoid \"Your paragraph…\" as a critique; prefer \"Compared with the structure we just "
    "described…\" or \"Your writing already contains the beginning of this structure…\", then name the "
    "REQUIREMENT the structure must satisfy and how the draft stands relative to it. In DISCOVERY mode "
    "(the default) teach ONLY what the structure must accomplish, the requirements that define a "
    "successful instance, and what the learner's task is — do NOT offer example solution strategies "
    "(do not say \"different writers do this in different ways\" followed by examples).\n"
    "  5) DEVELOPMENTAL INVITATION — it must emerge from the concept and ask the learner to CONSTRUCT a "
    "structure that satisfies the requirement, NOT to adopt one particular strategy you picked for "
    "them. Frame it around the constraint (e.g. \"which one idea could coordinate all the others so "
    "every sentence has a clear role?\"), leaving the learner free to choose how. Do not shift into "
    "rhetorical coaching or assignment-specific concerns unless they illustrate the structure.\n"
    "  6) STOP — end there and wait for the learner's response. No second question, no preview.\n"
    "STRUCTURAL REQUIREMENTS RULE (all stages, all objects): teach the CONSTRAINTS a successful "
    "instance of the structure must satisfy; never prescribe one particular way of satisfying them "
    "unless the assignment itself requires a specific form. Solving the learner's intellectual problem "
    "for them — choosing which idea wins, which order to use, which definition to adopt — is "
    "prohibited; that construction is the learner's cognitive work.\n"
    "DISCOVERY vs RESCUE: DISCOVERY is the default for the first turn and normal continuation — teach "
    "structure, function, and constraints, and withhold solution strategies. Switch to RESCUE ONLY when "
    "the user message tells you the learner is stuck after prior unsuccessful attempts or has "
    "explicitly asked for examples. In RESCUE you MAY introduce a few possible strategies as temporary "
    "scaffolds, but present them as POSSIBILITIES to consider, never as recommendations, and still "
    "leave the choice and the construction to the learner.\n"
    "\n"
    "═══ CONTINUATION TURN on the same active structure — do NOT repeat the six-function teaching "
    "sequence and do NOT restart the lesson. Use a LIGHTER continuation shape that makes the learner's "
    "development VISIBLE, performing these functions in order (functions, not sentence boundaries — "
    "natural and conversational, never formulaic): (1) re-anchor the active structure in a few words; "
    "(2) identify exactly WHAT CHANGED since the previous draft; (3) NAME THE DEVELOPMENTAL OPERATION "
    "the learner successfully performed — the structural accomplishment, not the content they added "
    "(say \"you've integrated the separate ideas into one understanding\" or \"you've expressed what "
    "the experience taught you\", never \"you added more detail\" or \"you have some good ideas\"); "
    "(4) explain what is now developmentally SUFFICIENT, if anything; (5) state plainly whether you are "
    "HOLDING them on the current structure or ADVANCING to the next, and WHY; (6) TEACH THE NEXT "
    "TRANSFORMATION — give the one thinking operation that moves this draft to the next, then STOP. "
    "MAKE THE TRAJECTORY EXPLICIT across revisions when a previous draft is provided — briefly mark "
    "Last / This / Next in natural prose (\"Last time you distinguished a fixed identity from a growing "
    "one; in this draft you connected that distinction to your own experience; the next step is to show "
    "the reader the moment that change actually happened\") so the learner sees a developmental path. "
    "Developmental language throughout (\"not yet\", \"still developing\", "
    "\"the next step is\"); never deficit language (\"lacks\", \"fails to\", \"you still haven't\"). If "
    "the requirement is now met, affirm specifically that they have done it, name the accomplishment, "
    "and recommend moving forward — invent no further work.\n"
    "\n"
    "ACROSS BOTH: short and warm — aim for 3 to 6 sentences, second person. ANTI-COAUTHORING IS "
    "ABSOLUTE: never write, rewrite, draft, correct, or supply the structure or the answer for them, "
    "and never hand them a copyable finished version — the thinking stays theirs. MEANING BEFORE "
    "JARGON: tie any writing term to something they are already doing. "
    "CURRICULUM BOUNDARY (authoritative): every substantive structural claim you make about the "
    "structure must be either (A) explicitly present in the canonical material provided to you this "
    "turn, or (B) a direct, conservative inference from it. Generated WORDING is fine; generated THEORY "
    "is not. Do NOT invent new structural requirements, do NOT reintroduce generic composition rules "
    "(e.g. 'a thesis must be contestable', 'every paragraph needs a hook', 'a conclusion restates the "
    "thesis'), and do NOT add a constraint merely because it is common in writing instruction. Any "
    "analogy or illustration you offer is disposable phrasing, never a new rule. "
    "Output ONLY the message the "
    "learner will read — no labels, no headings, no JSON, no meta."
)


_RESCUE_SIGNAL = re.compile(
    r"\b(for example|give (me )?an example|show me|an example|i (don'?t|do not) know|not sure how|"
    r"no idea|i'?m stuck|stuck|confused|help me|can you help|a hint|give me a hint|i give up|"
    r"what (do|should) i (write|say|put)|i can'?t (do|figure))\b", re.I)


def _wants_help(text: str) -> bool:
    """Learner explicitly asks for examples/help or signals being stuck (triggers RESCUE)."""
    return bool(text and _RESCUE_SIGNAL.search(text))


# Legacy selector object name -> Canonical Curriculum structure name (Acceptance Criterion #1).
# Only structures SUPERSEDED by a ready canonical model are remapped; others keep legacy behavior.
_LEGACY_TO_CANONICAL = {
    "Central Claim": "Thesis",
    "Paragraph Main Point": "Thesis",
    "Reader Orientation": "Opening",
    # Explanation -> Elaboration REMOVED (not approved). Canonical Elaboration is NOT the existing
    # calibrated Explanation CIO. Until reconciliation, "Explanation" has NO approved canonical mapping
    # and therefore falls through to its legacy teaching source (is_structure_ready('Explanation')==False).
    "Evidence": "Evidence / Example",
    "Elaboration": "Elaboration",
    "Paragraph Closure": "Conclusion",
    "Conclusion": "Conclusion",
    "Opening": "Opening",
    "Thesis": "Thesis",
    "Evidence / Example": "Evidence / Example",
}


def _resolve_teaching_source(structure: str, obj: Dict[str, Any]) -> Dict[str, Any]:
    """Return the teaching content + the STUDENT-FACING name for this turn.

    When the target maps to a ready Canonical Curriculum model, teach from the canonical
    model and use the CANONICAL name (no obsolete names reach the learner). Otherwise fall
    back to the legacy object (subordinate structures with no canonical model yet)."""
    canon = _LEGACY_TO_CANONICAL.get(structure, structure)
    cc = CC.get_structure(canon) if CC.is_structure_ready(canon) else None
    if cc:
        f = cc["fields"]
        variations = [v.get("name", "") for v in f["developmental_variations"]["value"]]
        goal = f["developmental_variations"]["value"][-1].get("description", "")
        reqs = f["structural_requirements"]["value"]
        req_text = " | ".join(f"{r.get('name','')}: {r.get('requirement','')}" for r in reqs)
        return {
            "display_name": canon, "canonical": True,
            "what_it_is": f["definition"]["value"], "function": f["function"]["value"],
            "goal": goal, "requirements": req_text,
            "discovery": f["discovery_instruction"]["value"], "rescue": f["rescue_instruction"]["value"],
            "sufficiency": f["developmental_sufficiency"]["value"], "variations": variations,
        }
    ind = obj.get("observable_indicators", {})
    return {
        "display_name": structure, "canonical": False,
        "what_it_is": obj.get("essence", ""), "function": obj.get("essence", ""),
        "goal": ind.get("present", ""), "requirements": ind.get("present", ""),
        "discovery": obj.get("teaching_strategy", ""), "rescue": obj.get("teaching_strategy", ""),
        "sufficiency": obj.get("exit_criterion", ""), "variations": obj.get("developmental_variations", []),
    }


async def generate_dialogue(session_id: str, assignment: str, unit: str, student_text: str,
                            structure: str, obj: Dict[str, Any], status: str,
                            kind: str, action: str = "scaffold",
                            mode: str = "first_turn", sufficiency: str = "continue",
                            rescue: bool = False, prior_student_text: str = "") -> str:
    src = _resolve_teaching_source(structure, obj)
    disp = src["display_name"]
    _action_hint = {
        "teach": "Explain the structure plainly and show what it does, then hand the doing back to the writer.",
        "scaffold": "PREFER one authentic developmental question that makes the writer do the thinking. Offer a sentence stem ONLY if a question alone will not let them perform the move; if you do, introduce it naturally (\"One way to start is…\", \"Try completing this idea…\") — never call it a 'scaffold' or a 'frame'.",
        "ask_question": "Ask one focused question that makes the writer do the thinking; do not explain much.",
        "model": "Briefly model the KIND of move on a neutral example, never on their content, then have them do theirs.",
        "encourage_revision": "Point to the one place to revise and invite them to try it in their own words.",
    }.get(action, "Ask one authentic developmental question that makes the writer do the thinking; add a sentence stem only if a question alone is not enough.")
    is_cont = (mode == "continuation")
    _prev_draft_block = (
        f"THE LEARNER'S PREVIOUS DRAFT (compare the CURRENT writing against this to identify exactly "
        f"what changed and which developmental operation the learner performed):\n"
        f"\"\"\"\n{prior_student_text}\n\"\"\"\n"
        if (is_cont and prior_student_text) else ""
    )
    _mode_block = (
        "MODE = CONTINUATION TURN. The learner is revising or responding WITHIN the SAME active "
        "structure they have already been taught. Do NOT repeat the first-turn six-function lesson and "
        "do NOT restart the lesson. Use a LIGHTER continuation shape that makes their development "
        "VISIBLE, performing these instructional functions IN ORDER (these are functions, not sentence "
        "boundaries — sound natural and conversational, never formulaic): (1) briefly RE-ANCHOR the "
        "active structure in a few words; (2) identify EXACTLY WHAT CHANGED since the previous draft by "
        "comparing the two drafts; (3) NAME THE DEVELOPMENTAL OPERATION the learner successfully "
        "performed — the structural accomplishment, NOT merely the content they added (e.g. \"you've "
        "brought the separate ideas together into one integrated understanding, so your paragraph now "
        "has a thesis capable of supporting elaboration\" / \"you've moved beyond simply recounting "
        "events and expressed what the experience taught you, which gives the paragraph an organizing "
        "meaning\"); NEVER generic acknowledgments like \"you improved this\", \"you moved closer\", "
        "\"you added more detail\", \"you added another sentence\", or \"you have some good ideas\"; "
        "(4) explain what is now DEVELOPMENTALLY SUFFICIENT, if anything (what the structure can now "
        "support); (5) STATE PLAINLY whether you are HOLDING the learner on the current structure or "
        "ADVANCING to the next structure, and WHY; (6) give ONE manageable next developmental "
        "invitation, then STOP. Use developmental language throughout (\"not yet\", \"still "
        "developing\", \"the next step is\") — never deficit language (\"lacks\", \"fails to\", \"you "
        "still haven't\"). If the requirement is now met, say so explicitly, name what they "
        "accomplished, and recommend moving forward.\n"
        f"{_prev_draft_block}"
        f"WHAT COUNTS AS ENOUGH (the requirement to compare against): {src['sufficiency']}\n"
        f"INTERNAL sufficiency read (informs you; do not quote): {sufficiency}\n"
    ) if is_cont else (
        "MODE = FIRST TURN. You are a developmental TEACHER, not a writing coach: teach the canonical "
        "STRUCTURE so it transfers to future writing; this paragraph is only evidence. Order: "
        "(1) EXPLICIT POSITIVE EVALUATION + ACHIEVEMENT ACKNOWLEDGMENT in four woven beats — (a) OPEN "
        "with a genuine, SPECIFIC positive evaluation of what the learner accomplished so they feel "
        "\"Compass recognized something valuable I actually did\" (\"You've made a strong start…\", "
        "\"You've identified a clear central experience…\", \"You've expressed a meaningful idea…\", "
        "\"That's an important shift…\") — specific not generic (\"good job\"), never overstated; "
        "(b) name the COMPLETED "
        "achievement affirmatively with a definitive verb (\"You have developed/stated/identified/"
        "established/distinguished…\"), (c) explain its INTELLECTUAL VALUE (why that accomplishment "
        "matters), (d) show how it PROVIDES A FOUNDATION for the next developmental step without "
        "diminishing it; "
        "accurate not generic, never overstated, and NEVER incompleteness/raw-material/repair language "
        "(\"you've already…\", \"beginning/starting to…\", \"some useful material…\", \"something to "
        "work with/build from…\", \"on the right track…\", a \"good start, but…\" pivot into criticism "
        "(an affirmative standalone \"you've made a good start\" is fine), or any progress "
        "language); (2) introduce the structure as the next thing to CONSTRUCT — \"Your next task is to "
        "develop a [structure]\" — never sharpen/improve/strengthen/fix; (3) TEACH HOW IT FUNCTIONS and "
        "how to THINK with it (not a flat \"A [structure] is…\" definition) so it changes how the "
        "learner reasons; (4) COMPARE their work to that structure (\"Compared with the structure we "
        "just described…\" / \"Your writing already contains the beginning of this structure…\") — the "
        "structure is the subject, the paper is evidence; do NOT critique the paragraph; when multiple "
        "valid solutions exist, name the REQUIREMENT the structure must satisfy without proposing a "
        "solution; (5) an invitation that asks the learner to CONSTRUCT a structure "
        "satisfying that requirement (their choice of how), never to adopt one strategy you selected; "
        "(6) STOP.\n"
        "COMPRESSION (first turn): deliver ALL of the above woven into AT MOST 3 short paragraphs and "
        "~150 words total — do NOT give each function its own paragraph or sentence. One specific "
        "acknowledgment, one concise teaching of what the structure does, one gap named in reader "
        "terms, one invitation. Brevity is required even on the first turn.\n"
        "STRUCTURAL REQUIREMENTS RULE: teach the constraints a successful structure must satisfy; never "
        "prescribe one particular way of satisfying them (which idea wins, which order, which "
        "definition) unless the assignment requires a specific form. Do not solve the learner's "
        "intellectual problem for them.\n"
        f"WHAT COUNTS AS ENOUGH (the requirement, for the compare step): {src['sufficiency']}\n"
    )
    _support_block = (
        "SUPPORT LEVEL = RESCUE. The learner is stuck after prior attempts or has asked for examples. "
        "You MAY now offer a few possible solution strategies as temporary scaffolds — but present them "
        "as POSSIBILITIES to weigh (\"one way some writers do this is…; another is…\"), NEVER as "
        "recommendations, and still require the learner to choose and construct. Keep withholding the "
        "finished answer itself.\n"
        f"CANONICAL RESCUE GUIDANCE (private; apply, do not quote verbatim): {src['rescue']}\n"
        if rescue else
        "SUPPORT LEVEL = DISCOVERY (default). Teach only the structure, its function, and the "
        "requirements a successful instance must satisfy. Do NOT list solution strategies or examples "
        "of how to satisfy the requirement; the learner constructs their own.\n"
        f"CANONICAL DISCOVERY GUIDANCE (private; apply, do not quote verbatim): {src['discovery']}\n"
    )
    _forms = ", ".join(src["variations"]) if isinstance(src["variations"], list) else str(src["variations"])
    # THESIS ORIENTATION + RELATIONAL OPERATION context — canonical composition path only.
    _elab_block = ""
    if src.get("canonical"):
        _dispn = src["display_name"]
        _relational = {
            "Thesis": "the Thesis IS this turn's operation — locate and develop the single integrated "
                      "understanding the learner wants the reader to take away.",
            "Elaboration": "ELABORATION OF THE THESIS (or of a specific point derived from it): develop, "
                           "differentiate, clarify, and unfold what the reader needs in order to "
                           "understand the thesis.",
            "Evidence / Example": "EVIDENCE FOR / EXAMPLE OF a specific elaborative point derived from the "
                                  "thesis — name that point first; evidence/example must never float free "
                                  "of the idea it supports or clarifies.",
            "Conclusion": "the CONCLUSION OF this line of reasoning — completion and integration of the "
                          "understanding developed from the thesis; show what the body has now made "
                          "possible for the reader to understand.",
            "Opening": "the OPENING that ORIENTS the reader toward the thesis and the communicative task, "
                       "when such orientation is needed.",
        }.get(_dispn, f"{_dispn}, performed in relation to the thesis.")
        _elab_block = (
            "\nTHESIS ORIENTATION (canonical composition — apply THIS turn): the thesis is the ORGANIZING "
            "CENTER of the paragraph. Ordinarily orient the learner to their thesis BEFORE introducing "
            "the writing operation, so the learner always knows WHAT IDEA they are developing before "
            "being asked WHAT OPERATION to perform. (1) Locate the learner's current THESIS STATE — "
            "A: topic-only / no thesis yet (names what the writing is about but states no single "
            "integrated understanding); B: emerging thesis (a recognizable integrated understanding is "
            "present but still needs clarifying / integrating / stabilizing); C: established thesis "
            "(organized enough to support work on dependent structures). (2) If a thesis or emerging "
            "thesis exists, STATE it in a conservative paraphrase grounded in the learner's OWN words, "
            "identify it explicitly as their thesis (\"that is your thesis\"), and say briefly what it "
            "says ABOUT the topic — a thesis says something ABOUT the topic, whereas a topic (e.g. 'how I "
            "was transformed', 'the causes of WWII') only names what the writing is about. (3) THEN "
            "introduce this turn's operation AS WORK PERFORMED IN RELATION TO THAT THESIS, never as an "
            f"isolated skill. This turn's relational operation is: {_relational} Keep the thesis VISIBLE "
            "as the organizing center even after it is developmentally sufficient — advancing from Thesis "
            "does NOT mean ceasing to mention it; but do NOT hold the learner on Thesis when it is "
            "already sufficient (orientation is not re-teaching Thesis). RECURSIVE PROCEDURE: the guiding "
            "question every turn is 'what does the naive reader need to understand NEXT in order to "
            "understand this thesis?' (what part of the thesis is still compressed, which distinction is "
            "not yet unfolded, what would a naive reader still not understand) — NEVER 'how does this "
            "evidence support the claim?'. 'Explanation' is NOT an instructional object or a next stage: "
            "never name it as a structure, a task, or the next step; explanation-of-evidence is only a "
            "subordinate reasoning move that may occur while elaborating, developing evidence, or "
            "concluding. Advance only among the five canonical primaries. CONTENT NEUTRALITY & "
            "ANTI-LEADING: the learner holds authority over what their writing MEANS. Help them "
            "clarify, integrate, test, and unfold THEIR OWN meaning; never decide what the experience "
            "'really' means or steer them toward a preferred interpretation (identity transformation, "
            "deeper self-knowledge, a surprising insight, an emotional or moral revelation) unless the "
            "learner has already introduced it or the assignment explicitly requires it. Before asking "
            "any question, check: does it help the learner clarify/test THEIR meaning, or steer them to "
            "a meaning YOU chose? If it presupposes a substantive answer, do not ask it. Avoid "
            "'what did this reveal about who you really are?', 'what did you discover about yourself you "
            "couldn't have known?', 'what deeper identity change occurred?', 'what was the real "
            "transformation?'. Prefer structurally OPEN questions: 'what is the main understanding you "
            "want the reader to take from this?', 'does this statement capture the point you want the "
            "rest of the paragraph to develop?', 'can the events be understood as parts of this one "
            "idea?', 'what would a naive reader need next to understand the thesis you have chosen?'.\n"
        )
        if _dispn == "Elaboration":
            _elab_block += (
                "CANONICAL ELABORATION — CRITICAL CONSTRAINTS: name this structure ONLY 'elaboration'; "
                "the word 'Explanation' is FORBIDDEN as the name of this structure or the task (do NOT "
                "say 'develop an Explanation'). Canonical Elaboration is NOT the legacy 'explain how your "
                "evidence supports your claim' move: do NOT frame this turn as claim -> evidence -> "
                "explanation-of-evidence, do NOT ask the learner to prove their events/details are "
                "evidence for a claim, and do NOT teach reasoning-that-connects-evidence-to-a-claim as "
                "the task. The thesis is a COMPRESSED integrated understanding — its full meaning is NOT "
                "transparent just because it has been stated in one sentence; the paragraph exists to "
                "UNFOLD it for the reader. Elaboration DEVELOPS THE SUBSTANCE OF THE THESIS (defining a "
                "central term, distinguishing related ideas, differentiating parts of the thesis, tracing "
                "a relation, unpacking an implication, examining a tension, qualifying a claim, comparing "
                "alternatives, showing how the writer's understanding changed) — it is the progressive "
                "development of UNDERSTANDING, not merely the addition of information. Evidence and "
                "examples are an OPTIONAL subordinate support for a particular elaborative point that MAY "
                "come later — do NOT shift to evidence yet.\n"
                "DISCOVERY STANCE (do NOT sound as if you already know what the elaboration is): you do "
                "NOT possess a predetermined elaboration waiting to be uncovered, and you must not imply "
                "one exists. Your governing question is 'what does the naive reader still not understand "
                "about this thesis?' — NEVER 'what elaboration do I want the learner to produce?'. Invite "
                "the learner to DISCOVER what is already contained within their own thesis; ask genuinely "
                "OPEN questions that do not presuppose the particular unfolding you have in mind, and let "
                "the learner determine what to develop. If you catch yourself steering toward a specific "
                "answer, replace it with a question that opens the thesis for the learner's own inquiry.\n"
                "STORY vs ELABORATION (teach the distinction — do NOT merely ask for 'more'): many "
                "learners faithfully follow an assignment prompt ('describe what happened / how you "
                "responded / what you learned') and produce a coherent STORY, then reasonably say 'I "
                "already elaborated — I told the story.' That response is fair; the problem is not effort "
                "but intellectual FUNCTION. When the learner's narrative is functioning as ILLUSTRATION "
                "rather than elaboration, do NOT request another example or more story — teach that these "
                "do different work: a STORY shows WHAT HAPPENED; ELABORATION develops WHAT THE EXPERIENCE "
                "MEANS and why it led to the insight. Both add sentences, but they perform fundamentally "
                "different intellectual work (Story answers 'What happened?'; Elaboration answers 'What "
                "does this experience actually mean?'). Reinterpret, never discard, the learner's "
                "narrative: its value is preserved, its ROLE simply changes — it becomes the lived "
                "experience/illustration FROM WHICH conceptual understanding is now developed (\"Your "
                "opening story already gives you a powerful illustration; instead of adding more of the "
                "story, your task now is to unfold the understanding that grew from it\"). Reference the "
                "other structural functions only when it clarifies this move — Evidence = concrete support "
                "for an idea; Explanation = how or why something works; Interpretation = making sense of "
                "an experience; Conclusion = what the reader should take away.\n"
                "NAME THE FUNCTIONAL REINTERPRETATION: when the learner's story shifts from being the "
                "MAIN organization of the paragraph to SERVING as illustration or evidence for the "
                "thesis, name that achievement briefly (\"Your story now does a new job: it shows the "
                "change your thesis is describing\") — so the learner understands their existing "
                "material is preserved while its FUNCTION changes.\n"
            )
            if not is_cont:
                _elab_block += (
                    "THESIS-TO-ELABORATION HANDOFF (weave naturally BEFORE the elaboration invitation): "
                    "(1) celebrate the authentic achievement; (2) STATE the learner's thesis in a "
                    "conservative paraphrase from their OWN words (do NOT replace it with a more "
                    "sophisticated thesis); (3) identify it as THE LEARNER'S THESIS and as a COMPRESSED "
                    "integrated understanding whose meaning the paragraph must now unfold; (4) SELECT ONE "
                    "manageable part of that thesis that remains compressed — a word, distinction, "
                    "relation, or implication a NAIVE READER would still not understand (\"what does a "
                    "naive reader need to understand next in order to understand this thesis?\"); (5) "
                    "introduce the next operation as ELABORATION OF that part of the thesis; (6) give ONE "
                    "manageable invitation to unfold that part for the reader, WITHOUT writing the "
                    "elaboration for them and WITHOUT shifting to evidence. Do NOT return to refining "
                    "Thesis unless a genuine contradiction or loss of integration appears.\n"
                )
        elif _dispn == "Thesis" and status != "missing":
            _elab_block += (
                "THESIS PRESENCE vs THESIS-ASSIGNMENT FIT (critical framing for THIS Thesis turn — the "
                "learner already expresses an integrated understanding, so a thesis IS present): these are "
                "DIFFERENT judgments and must NEVER be conflated. THESIS PRESENCE = does the learner "
                "already express a single integrated understanding that organizes the paragraph? Here the "
                "answer is YES — the learner HAS a thesis. THESIS-ASSIGNMENT FIT = does that thesis fully "
                "satisfy the particular intellectual demand of THIS assignment? A thesis can be entirely "
                "real and still need refinement to answer the assignment more precisely. RULE: because a "
                "thesis is present, you must NEVER describe it as absent and NEVER say 'your next task is "
                "to develop a thesis', 'you need a thesis', or 'this points toward a thesis'. Instead: "
                "(1) AFFIRM the thesis is present and name it in the learner's own words ('you have "
                "already developed a meaningful thesis…' / 'this expresses a genuine thesis…'); (2) then "
                "frame the work as REFINING / SHARPENING it so it more fully answers the SPECIFIC question "
                "this assignment is asking (e.g. so it expresses not only a general lesson but what THIS "
                "particular experience helped the learner understand about themselves). Never erase a "
                "genuine achievement in order to name remaining work — the learner must hear 'Yes, you've "
                "built the central idea; now let's strengthen it', never 'You still don't have one'. This "
                "OVERRIDES any earlier 'develop a [structure]' phrasing for this turn. Prefer 'refine it' "
                "/ 'sharpen it' / 'develop it further'; avoid the bare 'develop your thesis', which can "
                "sound as if the thesis is not yet there.\n"
            )
    _hints = DO.operation_hints(disp)
    _ops_block = (
        "\nDEVELOPMENTAL OPERATIONS LIBRARY (internal — identify the ONE transformation THIS turn "
        "requires and TEACH it in plain words as part C of your response; never speak the label to the "
        "learner). An operation is the move from the learner's CURRENT intellectual form to the next, "
        "more organized form. Pick the single operation whose 'from' form best matches what the learner "
        "has actually written and whose 'to' form is the next developmental organization; then teach its "
        "'Teach' move so the learner performs the transformation themselves (they supply all content).\n"
        f"{DO.render_operations_library()}\n"
        + (f"MOST LIKELY for this {disp} turn (a hint, not a constraint — choose the one that truly fits "
           f"the learner's draft): {', '.join(_hints)}.\n" if _hints else "")
    )
    prompt = (
        f"ASSIGNMENT: {assignment or '(not specified)'}\n"
        f"UNIT: {unit or 'one paragraph'}\n"
        f"THE WRITER JUST {('REVISED' if kind == 'revise' else 'WROTE' if kind in ('writing','continue') else 'RESPONDED')}:\n"
        f"\"\"\"\n{student_text}\n\"\"\"\n\n"
        f"{_mode_block}\n"
        f"{_support_block}\n"
        f"{_elab_block}"
        f"{_ops_block}"
        f"THE INSTRUCTIONAL DECISION IS ALREADY MADE. Help the writer build exactly this — do not "
        f"reconsider or broaden it. Use ONLY this canonical structure name with the learner; never use "
        f"any other or older name for it:\n"
        f"- FOCUS (the one canonical structure to work on this turn): {disp}\n"
        f"- WHAT IT IS (teach in your OWN plain words; do not recite verbatim): {src['what_it_is']}\n"
        f"- WHAT INTELLECTUAL WORK IT PERFORMS: {src['function']}\n"
        f"- STRUCTURAL REQUIREMENTS a successful instance must satisfy (teach as constraints, do not "
        f"prescribe one solution): {src['requirements']}\n"
        f"- WHAT IT LOOKS LIKE ONCE BUILT (the goal to move toward — NOT a verdict to read back): "
        f"{src['goal']}\n"
        f"- DECIDED ACTION (shapes HOW you deliver the one invitation): {action} — {_action_hint}\n\n"
        f"INTERNAL ANALYSIS — informs your choices; NOT for the learner. Never voice, quote, "
        f"paraphrase, or expose internal labels/status words. Locating the attempt (allowed) is a plain "
        f"observation in the learner's own terms, never a weakness list or status readout:\n"
        f"  internal_status={status}; internal_developmental_forms={_forms}\n"
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
    prior_target = state.selected_instructional_object  # prior turn's target (for first/continuation mode)
    prior_variation = state.developmental_variation or ""  # prior turn's variation (Instructional Continuity)
    prior_student_text = state.revision_history[-1].text if state.revision_history else ""  # prior draft (anti-repetition)

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
    # Canonical selection is activated per-session (reasoning_mode == "canonical_v2")
    # OR globally by the CANONICAL_SELECTION env flag. Otherwise legacy selection.
    _canonical = (session.get("reasoning_mode") == "canonical_v2") or _canonical_selection_enabled()
    t_s0 = time.perf_counter()
    sel = await select_structure(state.id, assignment, unit, student_text, canonical=_canonical,
                                 prior_target=prior_target, prior_variation=prior_variation,
                                 prior_student_text=prior_student_text)
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
    # next_objective: in the canonical path it MUST be one of the five canonical primaries (or empty).
    # A legacy object (Explanation, Transition, Definition, ...) is NEVER a valid canonical next stage —
    # Explanation is a subordinate reasoning operation, not an instructional object/stage.
    if _canonical:
        next_objective = _canonical_or_none(sel.get("next_objective")) or ""
    else:
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
    # next developmental objective (deterministic fallback: next applicable unmet structure).
    # Canonical path advances ONLY within the five canonical primaries (never Explanation/Transition/etc.).
    if not next_objective and target:
        _skip = set(established) | set(not_applicable) | {target}
        _order = list(CC.PRIMARY_STRUCTURES) if _canonical else PRIORITY_ORDER
        try:
            _start = _order.index(target) + 1
        except ValueError:
            _start = len(_order)
        for _s in _order[_start:]:
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
        "developmental_variation": developmental_variation,
        "selection_rationale": priority_rationale,
        "selection_contrast": selection_contrast,
        "instructional_action": instructional_action,
        "developmental_sufficiency": developmental_sufficiency,
        "sufficiency_reasoning": sufficiency_reasoning,
        "confidence": sel.get("confidence") or ("high" if target else "medium"),
        "next_objective": next_objective,
        "next_objective_reasoning": next_objective_reasoning,
    }
    if sel.get("_provisional"):
        instructional_analysis["provisional_judgment"] = sel["_provisional"]
        instructional_analysis["canonical_selection"] = True

    # write the authoritative decision onto persistent state (Sprint 1-4 fields reused)
    state.selected_instructional_object = target
    # DISCOVERY vs RESCUE: track consecutive continuation turns on the SAME target
    if prior_target and prior_target == target:
        state.current_target_attempts += 1
    else:
        state.current_target_attempts = 0
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
    state.observed_selection_evidence = (sel.get("_provisional", {}).get("observed_evidence")
                                         or ([f"{target}: status {status} in the writing"] if target else []))
    state.engine_recommendation = engine_recommendation
    state.decision_uncertainty = sel.get("_provisional", {}).get("unknowns", [])
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
        # FIRST-TURN vs CONTINUATION: continuation only when the SAME object stayed active
        # from the prior turn (instruction already presented on it); otherwise first turn.
        dialogue_mode = "continuation" if (prior_target and prior_target == target) else "first_turn"
        # RESCUE only after the learner remains stuck across continuation attempts, or asks for help.
        rescue = (dialogue_mode == "continuation"
                  and (state.current_target_attempts >= 2 or _wants_help(learner_content)))
        invitation, dlg_bytes = await generate_dialogue(state.id, assignment, unit, student_text,
                                                        target, obj, status, kind, instructional_action,
                                                        mode=dialogue_mode, sufficiency=developmental_sufficiency,
                                                        rescue=rescue, prior_student_text=prior_student_text)
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
            "established_structures": established,
            "current_thesis": sel.get("current_thesis") or "",
            "thesis_is_verbatim": bool(sel.get("thesis_is_verbatim")),
        },
        "_meta": efficiency,
    }
