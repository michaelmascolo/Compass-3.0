"""Developmental Operations Library (Canonical Mode).

An internal catalogue of the intellectual TRANSFORMATIONS Compass teaches — the move
from a learner's current form of thought (e.g. a story, an observation, an example)
to the next, more organized form (e.g. its meaning, a thesis, a principle).

Compass does not merely identify a problem ("this needs elaboration"); it teaches the
OPERATION that carries the learner from their current draft to the next. Each entry
names the two intellectual forms, the reader-understanding gap between them, and a
coaching strategy for teaching the transformation (a strategy to ADAPT, never a fixed
sentence to recite). The dialogue model selects the ONE operation a turn requires and
teaches it; these are guidance, not templates. Content stays the learner's own.
"""

from typing import List

DEVELOPMENTAL_OPERATIONS = [
    {
        "name": "Story → Meaning",
        "from_form": "a narrative that recounts what happened",
        "to_form": "an articulated understanding of what the experience means",
        "reader_gap": "the reader can follow the events but does not yet understand what they signify",
        "teach": "Point the learner back to the moment of change in their story and ask them to say what shifted in their thinking — name the understanding the events point to.",
    },
    {
        "name": "Observation → Thesis",
        "from_form": "a noticing or description of something true",
        "to_form": "a single organizing claim the paragraph will develop",
        "reader_gap": "the reader sees the observation but not the one idea it all adds up to",
        "teach": "Ask what single idea these observations amount to, and invite the learner to state it as a claim.",
    },
    {
        "name": "Example → Principle",
        "from_form": "a single instance or case",
        "to_form": "the general truth the instance illustrates",
        "reader_gap": "the reader sees the instance but not the wider principle it demonstrates",
        "teach": "Ask what this example is an example OF — the principle it demonstrates beyond the single case.",
    },
    {
        "name": "Illustration → Elaboration",
        "from_form": "an image or scene that shows an idea",
        "to_form": "developed meaning of that idea (definition, distinction, implication)",
        "reader_gap": "the reader can picture it but does not yet understand the idea's meaning",
        "teach": "Keep the illustration, then ask the learner to develop what it means — define the key term, distinguish the parts, or unfold the implication.",
    },
    {
        "name": "Description → Interpretation",
        "from_form": "details of what something is like",
        "to_form": "an account of what those details mean",
        "reader_gap": "the reader can picture it but not what it signifies",
        "teach": "Ask what the description reveals — invite the learner to make sense of it, not just render it.",
    },
    {
        "name": "Claim → Justification",
        "from_form": "an asserted position",
        "to_form": "the reasoning that grounds the claim",
        "reader_gap": "the reader hears the claim but not why it should be accepted",
        "teach": "Ask what makes the claim hold — the reasoning behind it, not a restatement or a louder assertion.",
    },
    {
        "name": "Evidence → Explanation",
        "from_form": "facts, data, or quotations offered as support",
        "to_form": "an explicit account of how that evidence supports the idea",
        "reader_gap": "the reader sees the evidence but not how it bears on the claim",
        "teach": "Ask the learner to make the connection explicit — how does this evidence actually support the point it sits beside?",
    },
    {
        "name": "Experience → Generalization",
        "from_form": "one lived, particular experience",
        "to_form": "what the experience shows that is true beyond itself",
        "reader_gap": "the reader understands the particular but not what it means beyond this one case",
        "teach": "Ask what this experience shows that would be true beyond this single instance.",
    },
    {
        "name": "Generalization → Personal Meaning",
        "from_form": "a general truth stated abstractly",
        "to_form": "what that truth came to mean for this particular writer",
        "reader_gap": "the reader grasps the general idea but not what it means to THIS writer",
        "teach": "Ask what this general truth came to mean for the learner specifically, grounded in their own experience.",
    },
    {
        "name": "Abstract idea → Concrete experience",
        "from_form": "an abstract statement with nothing to hold onto",
        "to_form": "a specific moment, image, or instance that makes it real",
        "reader_gap": "the reader understands the words but has nothing concrete to attach them to",
        "teach": "Ask for the particular moment, image, or instance that makes the abstract idea real for a reader.",
    },
    {
        "name": "Parallel ideas → Integrated explanation",
        "from_form": "two ideas placed side by side (running parallel)",
        "to_form": "one idea that unfolds from the other, showing the relation between them",
        "reader_gap": "the reader understands each idea separately but not how one becomes or relates to the other",
        "teach": "Ask how the second idea grows out of the first — the mechanism or relation that connects them — so the paragraph unfolds FROM the thesis rather than listing a new idea beside it.",
    },
]

_BY_NAME = {op["name"]: op for op in DEVELOPMENTAL_OPERATIONS}

# Which operations are most likely to be the transformation a given focus requires.
# A hint that biases the model's selection; the model still identifies the actual one.
_HINTS_BY_FOCUS = {
    "Thesis": ["Observation → Thesis", "Story → Meaning", "Experience → Generalization",
               "Generalization → Personal Meaning"],
    "Elaboration": ["Illustration → Elaboration", "Story → Meaning", "Parallel ideas → Integrated explanation",
                    "Example → Principle", "Description → Interpretation", "Abstract idea → Concrete experience"],
    "Evidence / Example": ["Evidence → Explanation", "Claim → Justification", "Example → Principle"],
    "Conclusion": ["Generalization → Personal Meaning", "Experience → Generalization"],
    "Opening": ["Abstract idea → Concrete experience"],
}


def render_operations_library() -> str:
    """Compact one-line-per-operation menu for injection into the dialogue prompt."""
    lines = []
    for op in DEVELOPMENTAL_OPERATIONS:
        lines.append(
            f"- {op['name']}: from {op['from_form']} to {op['to_form']}. "
            f"Reader gap: {op['reader_gap']}. Teach: {op['teach']}"
        )
    return "\n".join(lines)


def operation_hints(focus: str) -> List[str]:
    """Operation names most likely relevant to the current instructional focus."""
    return _HINTS_BY_FOCUS.get(focus, [])
