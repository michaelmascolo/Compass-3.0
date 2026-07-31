"""
Canonical Paragraph Curriculum — PHASE 1 infrastructure (authoritative internal library).

Authoritative internal library that will (in a later, separately-approved phase) govern
instructional decisions, dialogue, Teacher Review, Composition Studio, and Organization of
Thought. Phase 1 is BUILD + MAP + POPULATE-FROM-SUPPLIED-MODELS only.

HARD RULES (per directive):
  * STRUCTURED INTERNAL KNOWLEDGE, not prompt fragments.
  * NO theory is invented. NO field is reconstructed from the existing CIOs or from generic
    composition knowledge. Each primary structure's nine fields stay PENDING_CANONICAL_INPUT
    until the curriculum authority supplies that structure's canonical model, which is inserted
    VERBATIM (no normalization toward conventional composition pedagogy).
  * Wired to NOTHING — importing this module changes no runtime behavior.

Provenance tags per field:
  - "canonical_supplied" : inserted verbatim from an authority-supplied canonical model. Authoritative.
  - "pending"            : PENDING_CANONICAL_INPUT — awaiting the supplied model. Never invented.
"""
from typing import Any, Dict, List
import json
import os

PENDING = "PENDING_CANONICAL_INPUT"

# The nine canonical fields every PRIMARY structure must define.
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

# Primary paragraph curriculum (exact names, directive order).
PRIMARY_STRUCTURES: List[str] = ["Opening", "Thesis", "Elaboration", "Evidence / Example", "Conclusion"]

# Order in which the authority will supply and I will insert the authoritative models.
MODEL_SUPPLY_ORDER: List[str] = ["Thesis", "Elaboration", "Evidence / Example", "Conclusion", "Opening"]

# Lighter schema for SUBORDINATE structures (per directive D.5). Not modeled in Phase 1.
SUBORDINATE_FIELDS: List[str] = [
    "name", "definition", "function", "activation_conditions",
    "structural_requirements", "developmental_sufficiency",
    "relationship_to_primary", "provenance_status",
]

# Subordinate registry — status/relationship notes ONLY; NO full models built this phase (D.4).
# Existing live-engine CIOs are left UNCHANGED; these notes record reconciliation intent only.
SUBORDINATE_STRUCTURES: Dict[str, Dict[str, Any]] = {
    "Definition": {
        "status": "subordinate; existing calibrated Definition CIO left UNCHANGED in live engine",
        "activation_conditions": ("Active only when a load-bearing term's meaning is required for the "
                                  "thesis to be understood, for elaboration to function, or for the "
                                  "intended audience to understand the integrated message. NOT required "
                                  "by every thesis."),
        "relationship_to_primary": ["Thesis", "Elaboration"],
        "provenance_status": "reconciliation_pending",
    },
    "Explanation": {
        "status": "existing calibrated Explanation CIO left UNCHANGED; it is NOT canonical Elaboration",
        "activation_conditions": PENDING,
        "relationship_to_primary": ("eventual subordinate placement — within Elaboration, or as an "
                                    "Evidence/Example relation, or a distinct lower-level object — "
                                    "decided during reconciliation"),
        "provenance_status": "reconciliation_pending",
    },
    "Transition": {"status": "subordinate; not modeled in Phase 1", "activation_conditions": PENDING,
                   "relationship_to_primary": PENDING, "provenance_status": "pending"},
    "Qualification": {"status": "subordinate; not modeled in Phase 1", "activation_conditions": PENDING,
                      "relationship_to_primary": PENDING, "provenance_status": "pending"},
    "Comparison": {"status": "subordinate; not modeled in Phase 1", "activation_conditions": PENDING,
                   "relationship_to_primary": PENDING, "provenance_status": "pending"},
    "Analogy": {"status": "subordinate; not modeled in Phase 1", "activation_conditions": PENDING,
                "relationship_to_primary": PENDING, "provenance_status": "pending"},
}

# Reconciliation notes — NOT authoritative curriculum content; record the authority's Phase-1
# decisions so the later reconciliation/migration phase has them.
RECONCILIATION_NOTES: Dict[str, Any] = {
    "Paragraph Main Point": ("Folds conceptually into Thesis at the single-paragraph level; existing "
                             "CIO left UNCHANGED in the live engine; NOT created as a primary curriculum "
                             "structure."),
    "Elaboration_working_definition_from_authority": ("The progressive differentiation and integration "
                             "of the integrated message expressed in the thesis, guided by: 'What does a "
                             "naive reader have to know in order to understand this point?' Elaboration is "
                             "the principal developmental work of the paragraph. FULL canonical model still "
                             "PENDING supply — not treated as authoritative field content yet."),
    "generic_assumptions_to_reject": [
        "every opening requires a hook",
        "every conclusion merely restates the thesis",
        "every conclusion must state significance",
        "every opening must occur before the thesis",
    ],
    "existing_generic_objects_not_authoritative": ["Reader Orientation", "Conclusion"],
}


def _pending_primary() -> Dict[str, Any]:
    return {
        "status": "awaiting_canonical_model",
        "fields": {f: {"value": PENDING, "provenance": "pending"} for f in CANONICAL_FIELDS},
    }


# The authoritative registry. Every primary structure awaits its supplied model. Wired to NOTHING.
CURRICULUM: Dict[str, Dict[str, Any]] = {name: _pending_primary() for name in PRIMARY_STRUCTURES}

# Authority-supplied models are stored verbatim as JSON under canonical_models/ and loaded on import.
_MODEL_DIR = os.path.join(os.path.dirname(__file__), "canonical_models")
_MODEL_FILES: Dict[str, str] = {
    "Thesis": "thesis.json",
    "Elaboration": "elaboration.json",
    "Evidence / Example": "evidence_example.json",
    "Conclusion": "conclusion.json",
    "Opening": "opening.json",
}


# ---------------------------------------------------------------------------
# Insertion + validation API (used ONLY to store authority-supplied models verbatim).
# ---------------------------------------------------------------------------
def validate_model(model: Dict[str, Any]) -> Dict[str, Any]:
    """Check a supplied canonical model against the nine-field schema. No content judgment."""
    keys = set(model.keys())
    required = set(CANONICAL_FIELDS)
    missing = sorted(required - keys)
    extra = sorted(keys - required)
    empty = sorted(f for f in CANONICAL_FIELDS if f in model and (model[f] is None or model[f] == ""))
    return {"ok": not missing and not extra and not empty,
            "missing": missing, "extra": extra, "empty": empty}


def insert_primary_model(name: str, model: Dict[str, Any]) -> Dict[str, Any]:
    """Insert an authority-supplied model VERBATIM (no normalization). Returns the validation result."""
    if name not in CURRICULUM:
        raise KeyError(f"'{name}' is not a primary canonical structure: {PRIMARY_STRUCTURES}")
    result = validate_model(model)
    if not result["ok"]:
        return result
    CURRICULUM[name] = {
        "status": "canonical",
        "fields": {f: {"value": model[f], "provenance": "canonical_supplied"} for f in CANONICAL_FIELDS},
    }
    return result


# ---------------------------------------------------------------------------
# Query API (for later phases; read-only).
# ---------------------------------------------------------------------------
def get_structure(name: str):
    return CURRICULUM.get(name)


def get_field(name: str, field: str):
    s = CURRICULUM.get(name)
    return s["fields"].get(field) if s else None


def observable_decision_questions(name: str):
    f = get_field(name, "observable_decision_questions")
    return f["value"] if f else None


def is_field_ready(name: str, field: str) -> bool:
    f = get_field(name, field)
    return bool(f and f["provenance"] == "canonical_supplied" and f["value"] != PENDING)


def is_structure_ready(name: str) -> bool:
    return all(is_field_ready(name, f) for f in CANONICAL_FIELDS)


def pending_report() -> Dict[str, Any]:
    return {name: {"status": entry["status"],
                   "fields": {f: entry["fields"][f]["provenance"] for f in CANONICAL_FIELDS}}
            for name, entry in CURRICULUM.items()}


def _load_supplied_models() -> None:
    """Ingest authority-supplied JSON models verbatim on import. Missing files stay PENDING."""
    for name, fname in _MODEL_FILES.items():
        path = os.path.join(_MODEL_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            model = json.load(fh)
        result = insert_primary_model(name, model)
        if not result["ok"]:
            # keep PENDING and surface the problem loudly rather than inserting a broken model
            CURRICULUM[name]["status"] = f"INVALID_SUPPLIED_MODEL: {result}"


_load_supplied_models()
