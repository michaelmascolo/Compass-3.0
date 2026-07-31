"""
Canonical Paragraph Curriculum — PHASE 1 infrastructure.

Authoritative internal library that will govern instructional decisions, dialogue,
Teacher Review, Composition Studio, and future Organization-of-Thought integration.

HARD RULES (per directive):
  * This is STRUCTURED INTERNAL KNOWLEDGE, not prompt fragments.
  * NO theory is invented here. Any field lacking an authoritative source is set to
    PENDING_CANONICAL_INPUT and must be supplied by the curriculum authority — never
    filled from generic composition knowledge or LLM defaults.
  * PHASE 1 is BUILD + MAP ONLY. Nothing in this module is wired into runtime behavior
    yet; importing it changes no existing behavior.

Each primary structure is a CanonicalStructure with the nine specified fields. Every
field carries a provenance tag so the source of every piece of knowledge is auditable:
  - "calibrated"      lifted 1:1 (verbatim) from a Phase-II CALIBRATED CIO (non-generic,
                      already vetted). Authoritative.
  - "source_material" raw calibrated CIO text is attached for reference, but the value in
                      this canonical field is PENDING because the field is NOT a 1:1 match
                      (it would require authoring/splitting = theory work). Awaiting authority.
  - "pending"         no authoritative source exists at all. Awaiting canonical input.
"""
from typing import Any, Dict, List, Optional

PENDING = "PENDING_CANONICAL_INPUT"

# The nine canonical fields every primary structure must define.
CANONICAL_FIELDS: List[str] = [
    "definition",
    "function",
    "structural_dependencies",
    "structural_requirements",
    "developmental_variations",
    "developmental_sufficiency",
    "discovery_instruction",
    "rescue_instruction",
    "observable_decision_questions",
]

# Primary paragraph curriculum (exact names per directive). Order as given.
PRIMARY_STRUCTURES: List[str] = ["Opening", "Thesis", "Elaboration", "Evidence / Example", "Conclusion"]

# Subordinate structures — activated only when required (directive: "Definitions, transitions,
# qualifications, comparisons, analogies, etc. remain subordinate"). Membership PENDING confirmation.
SUBORDINATE_STRUCTURES: List[str] = [
    "Definition", "Transition", "Qualification", "Comparison", "Analogy",
]


def _field(value: Any, provenance: str, source: Optional[str] = None,
           source_material: Any = None) -> Dict[str, Any]:
    return {"value": value, "provenance": provenance, "source": source,
            "source_material": source_material}


# ---------------------------------------------------------------------------
# PROPOSED mappings onto existing objects (compass_structure_engine.MINIMAL_OBJECTS).
# HIGH-confidence mappings lift calibrated content; ambiguous/unconfirmed mappings keep
# their fields PENDING and are surfaced as open questions in the Phase-1 report.
#
#   Thesis            <- "Central Claim"        (Phase-II CALIBRATED CIO #1)   [confirm]
#   Evidence / Example<- "Evidence"             (Phase-II CALIBRATED CIO #2)   [confirm; "Example" subtype?]
#   Elaboration       <- "Explanation"(#3 cal.) OR "Elaboration"(not cal.) ??  [AMBIGUOUS — ask]
#   Opening           <- "Reader Orientation"   (exists, NOT calibrated)       [ambiguous — ask]
#   Conclusion        <- "Conclusion"           (exists, NOT calibrated)       [ambiguous — ask]
# ---------------------------------------------------------------------------

# Raw calibrated CIO texts are copied in as source_material so the curriculum is
# self-contained (independent of the dialogue/selector prompt fragments).
_CAL = {
    "Central Claim": {
        "essence": "The single contestable position the whole piece exists to establish and defend; it answers the task and gives every other sentence something to serve.",
        "indicators": {
            "present": "One specific, arguable position a skeptic could push back on governs the writing.",
            "partial": "A position is taken but too broad or unscoped to organize the support.",
            "missing": "Only a topic, an opinion, or a fact — nothing a reader could dispute.",
            "misleading": "Two or more competing claims, so the governing position is unclear.",
        },
        "developmental_variations": ["Topic only", "Personal opinion", "Broad claim", "Multiple competing claims", "Precise contestable claim"],
        "exit_criterion": "A single, scoped, contestable claim is on the page that the rest of the writing can organize itself around.",
        "teaching_strategy": "Have the writer name the ONE thing they want a reader to accept, then sharpen it until a reasonable person could disagree; do not supply the claim.",
    },
    "Evidence": {
        "essence": "Specific, relevant, adequate material a reader can check that gives a claim something concrete to stand on — not bare assertion, not off-point material, and not so thin a skeptic could wave it away.",
        "indicators": {
            "present": "The claim is backed by material that is specific, relevant to THAT claim, and adequate — a skeptic has something concrete to weigh.",
            "partial": "Support is offered but thin, general, or covers only part of the claim (backs a sub-point, not the whole position).",
            "missing": "The claim is asserted with nothing specific behind it — an unsupported assertion.",
            "misleading": "The material offered is irrelevant to the claim, or actually points against it (evidence that contradicts the claim).",
        },
        "developmental_variations": ["Unsupported assertion", "Irrelevant support", "Vague / general support", "Partial support (covers only part of the claim)", "Relevant but inadequate", "Evidence that contradicts the claim", "Specific, relevant, adequate evidence"],
        "exit_criterion": "At least one claim is supported by specific, relevant material a reader could examine.",
        "teaching_strategy": "First confirm the claim is clear and answers the task. Then help the writer judge their own material on three axes a skeptic uses: RELEVANT to this exact claim, SPECIFIC (checkable), ADEQUATE (enough to carry the point). Never supply the evidence; the noticing stays theirs.",
    },
}


def _primary_entry(source_cio: Optional[str], mapping_confirmed: bool) -> Dict[str, Any]:
    """Build a nine-field entry.

    When a CONFIRMED calibrated source exists, lift the two fields that map 1:1
    (developmental_variations, developmental_sufficiency) and attach the calibrated
    essence/indicators/teaching_strategy as source_material for the authoring-needed
    fields. Everything else stays PENDING. Nothing is invented.
    """
    cal = _CAL.get(source_cio) if (source_cio and mapping_confirmed) else None
    return {
        "source_cio": source_cio,
        "mapping_confirmed": mapping_confirmed,
        "fields": {
            "definition": _field(
                PENDING, "source_material" if cal else "pending", source_cio,
                cal["essence"] if cal else None),
            "function": _field(
                PENDING, "source_material" if cal else "pending", source_cio,
                cal["essence"] if cal else None),
            "structural_dependencies": _field(PENDING, "pending", source_cio),
            "structural_requirements": _field(
                PENDING, "source_material" if cal else "pending", source_cio,
                {"present_indicator": cal["indicators"]["present"], "exit_criterion": cal["exit_criterion"]} if cal else None),
            "developmental_variations": _field(
                cal["developmental_variations"], "calibrated", source_cio) if cal
                else _field(PENDING, "pending", source_cio),
            "developmental_sufficiency": _field(
                cal["exit_criterion"], "calibrated", source_cio) if cal
                else _field(PENDING, "pending", source_cio),
            "discovery_instruction": _field(
                PENDING, "source_material" if cal else "pending", source_cio,
                cal["teaching_strategy"] if cal else None),
            "rescue_instruction": _field(PENDING, "pending", source_cio),
            "observable_decision_questions": _field(
                PENDING, "source_material" if cal else "pending", source_cio,
                cal["indicators"] if cal else None),
        },
    }


# The authoritative registry. Wired to NOTHING yet.
CURRICULUM: Dict[str, Dict[str, Any]] = {
    "Opening":            _primary_entry("Reader Orientation", mapping_confirmed=False),
    "Thesis":             _primary_entry("Central Claim",      mapping_confirmed=True),
    "Elaboration":        _primary_entry(None,                 mapping_confirmed=False),  # Explanation vs Elaboration — ASK
    "Evidence / Example": _primary_entry("Evidence",           mapping_confirmed=True),
    "Conclusion":         _primary_entry("Conclusion",         mapping_confirmed=False),
}


# ---------------------------------------------------------------------------
# Query API (for the instructional decision layer & Teacher Review in later phases).
# ---------------------------------------------------------------------------
def get_structure(name: str) -> Optional[Dict[str, Any]]:
    return CURRICULUM.get(name)


def get_field(name: str, field: str) -> Optional[Dict[str, Any]]:
    s = CURRICULUM.get(name)
    return s["fields"].get(field) if s else None


def observable_decision_questions(name: str) -> Any:
    f = get_field(name, "observable_decision_questions")
    return f["value"] if f else None


def is_field_ready(name: str, field: str) -> bool:
    f = get_field(name, field)
    return bool(f and f["provenance"] == "calibrated" and f["value"] != PENDING)


def is_structure_ready(name: str) -> bool:
    return all(is_field_ready(name, f) for f in CANONICAL_FIELDS)


def pending_report() -> Dict[str, Dict[str, str]]:
    """Every field's provenance/readiness — the authoritative gap list for Phase 1."""
    out: Dict[str, Dict[str, str]] = {}
    for name, entry in CURRICULUM.items():
        out[name] = {f: entry["fields"][f]["provenance"] for f in CANONICAL_FIELDS}
    return out
