"""Phase II Step 1 — close the instructional-completeness gaps the audit found.
Safe load -> modify -> write for the two JSON KB files. Idempotent.

Gaps closed:
  1. Add a `Synthesis` instructional object (was entirely missing an IO).
  2. Add a whole-essay `thesis` exit criterion (had only io.stopping_conditions).
Grounded in the existing canonical_explanations + exit_criteria sources.
`sentence_relationships` is a MAPPING fix (-> Coherence IO), handled in server/audit, not here.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IO_PATH = ROOT / "instructional_objects.json"
EC_PATH = ROOT / "developmental_exit_criteria.json"

# ---- 1. Synthesis instructional object ----
SYNTHESIS_IO = {
    "domain": "writing",
    "element": "Synthesis",
    "aliases": ["integration", "bringing ideas together"],
    "definition": "Showing the reader how several developed ideas fit together into a larger point.",
    "communicative_purpose": "Show how multiple ideas work together to create a meaning larger than any one of them alone.",
    "performance_structure": "Gather the developed ideas that belong together; name the relationship among them; state the larger point that emerges from combining them; show the reader why the whole means more than the parts.",
    "recognition_diagnostics": "The draft lists or explains several ideas but never states what they add up to; the reader is left to assemble the larger meaning alone.",
    "common_obstacles": "Mere summary instead of integration; disconnected points left side by side; restating each idea without naming the larger point they create together.",
    "next_developmental_moves": "Ask the student which ideas belong together and what larger point those ideas make when combined; invite them to write the one sentence that states the meaning created by the combination.",
    "indicators_of_control": "The student independently draws developed ideas together into a stated larger meaning, rather than summarizing them one by one.",
    "related_elements": ["Explanation / Analysis", "Organization", "Conclusion", "Thesis", "Supporting Claim", "Unity"],
    "functional_relationships": {
        "explanation": "Synthesis builds on ideas the student has already explained; it names what those explanations add up to.",
        "organization": "Synthesis depends on the ideas being developed and arranged clearly enough to be combined.",
        "conclusion": "Synthesis often prepares closure by establishing the larger meaning the ending completes.",
    },
    "common_difficulties": ["mere summary", "disconnected points"],
    "revision_strategies": [
        "Underline the separate ideas, then write one sentence stating what they mean together.",
        "Replace a summary sentence with a sentence that names the relationship among the ideas.",
    ],
    "indicators_of_development": "Begins to state a combined meaning rather than re-listing ideas.",
    "stopping_conditions": [
        "Learner independently states the larger meaning created by combining developed ideas.",
        "Diminishing returns — the element performs its canonical function for this reader and purpose.",
    ],
    "canonical_source": "developmental_exit_criteria.json:synthesis + canonical_explanations.synthesis",
    "enrichment_version": "phase2-step1-gapfill-v1",
}

# ---- 2. Whole-essay thesis exit criterion ----
THESIS_EXIT = {
    "id": "thesis",
    "n": 100,  # appended; ordering by 'n' is presentational only
    "name": "Thesis (Whole-Essay Controlling Idea)",
    "level": "whole_composition",
    "purpose": "State the single central idea the whole essay exists to establish.",
    "cognitive_operation": "Commit to one arguable, supportable central claim that answers the task.",
    "exit_criterion": "Can every part of the essay be organized around this one central claim, and could a thoughtful reader restate it?",
    "dependencies": ["Communicative purpose"],
    "failure_modes": ["topic instead of claim", "fact or question instead of a position", "claim the body does not develop", "scope too broad to support"],
    "next_operation": "Overall organization",
}


def main():
    # instructional_objects
    io_doc = json.loads(IO_PATH.read_text())
    objs = io_doc["instructional_objects"]
    if not any(o.get("element") == "Synthesis" for o in objs):
        objs.append(SYNTHESIS_IO)
        IO_PATH.write_text(json.dumps(io_doc, indent=2, ensure_ascii=False))
        print("added Synthesis instructional object")
    else:
        print("Synthesis IO already present — skipped")

    # exit criteria
    ec_doc = json.loads(EC_PATH.read_text())
    els = ec_doc["elements"]
    if not any(e.get("id") == "thesis" for e in els):
        els.append(THESIS_EXIT)
        EC_PATH.write_text(json.dumps(ec_doc, indent=2, ensure_ascii=False))
        print("added thesis exit criterion")
    else:
        print("thesis exit criterion already present — skipped")


if __name__ == "__main__":
    main()
