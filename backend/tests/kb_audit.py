"""Writing Knowledge Base — INSTRUCTIONAL COMPLETENESS audit (Phase II, Step 1).

For every canonical structural element the engine can instruct on, verify the KB
supplies all EIGHT instructional dimensions the hydrator will need:
  1 canonical_explanation   2 purpose               3 structural_relationships
  4 dependency_relationships 5 developmental_difficulties 6 instructional_strategies
  7 observable_indicators    8 exit_criteria

Sources: developmental_exit_criteria.json (canonical_explanations + elements),
instructional_objects.json (35 enriched objects). Cross-referenced by element key.
Writes a markdown report to test_reports/kb_instructional_completeness_audit.md.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT.parent / "test_reports"

EC = json.loads((ROOT / "developmental_exit_criteria.json").read_text())
IO = json.loads((ROOT / "instructional_objects.json").read_text())["instructional_objects"]
CANON_EXPL = EC.get("canonical_explanations", {})
EXIT_BY_ID = {e["id"]: e for e in EC.get("elements", [])}

# instructional_objects indexed by element name + aliases (lowercased)
IO_INDEX = {}
for o in IO:
    IO_INDEX[o["element"].lower()] = o
    for a in o.get("aliases", []):
        IO_INDEX.setdefault(a.lower(), o)

# The operative canonical element set the engine instructs on, mapped to its
# instructional-object element name and exit-criterion id. (Explicit map — the
# three files use different identifier spaces.)
CANONICAL = {
    "communicative_purpose": {"io": "Purpose", "exit": "communicative_purpose"},
    "overall_organization": {"io": "Organization", "exit": "overall_organization"},
    "introduction": {"io": "Introduction", "exit": "introduction"},
    "paragraph_purpose": {"io": "Paragraph", "exit": "paragraph_purpose"},
    "controlling_idea": {"io": "Topic Sentence", "exit": "controlling_idea"},
    "thesis": {"io": "Thesis", "exit": "thesis"},
    "definition": {"io": "Definition", "exit": "definition"},
    "explanation": {"io": "Explanation / Analysis", "exit": "explanation"},
    "evidence": {"io": "Evidence", "exit": "evidence"},
    "example": {"io": "Example", "exit": "example"},
    "transition": {"io": "Transition", "exit": "transition"},
    "reader_guidance": {"io": "Audience Awareness", "exit": "reader_guidance"},
    "synthesis": {"io": "Synthesis", "exit": "synthesis"},
    "closure": {"io": "Conclusion", "exit": "closure"},
    "sentence_purpose": {"io": "Sentence", "exit": "sentence_purpose"},
    "sentence_relationships": {"io": "Coherence", "exit": "sentence_relationships"},
}

DIMS = [
    "canonical_explanation", "purpose", "structural_relationships",
    "dependency_relationships", "developmental_difficulties",
    "instructional_strategies", "observable_indicators", "exit_criteria",
]


def _nonempty(v):
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def check_element(key, m):
    io = IO_INDEX.get((m["io"] or "").lower()) if m["io"] else None
    ex = EXIT_BY_ID.get(m["exit"]) if m["exit"] else None
    r = {}

    # 1 canonical explanation
    r["canonical_explanation"] = ("KB", "canonical_explanations") if _nonempty(CANON_EXPL.get(key)) else (None, None)

    # 2 purpose
    if io and _nonempty(io.get("communicative_purpose")):
        r["purpose"] = ("KB", "io.communicative_purpose")
    elif ex and _nonempty(ex.get("purpose")):
        r["purpose"] = ("KB", "exit.purpose")
    else:
        r["purpose"] = (None, None)

    # 3 structural relationships
    if io and (_nonempty(io.get("related_elements")) or _nonempty(io.get("functional_relationships"))):
        r["structural_relationships"] = ("KB", "io.related_elements/functional_relationships")
    else:
        r["structural_relationships"] = (None, None)

    # 4 dependency relationships — an explicit `dependencies` key (even []) is a
    #   complete authored answer (root elements legitimately have no dependencies).
    if ex is not None and isinstance(ex.get("dependencies"), list):
        r["dependency_relationships"] = ("KB", "exit.dependencies")
    elif io and _nonempty(io.get("functional_relationships")):
        r["dependency_relationships"] = ("PARTIAL", "io.functional_relationships")
    else:
        r["dependency_relationships"] = (None, None)

    # 5 developmental difficulties
    if io and (_nonempty(io.get("common_obstacles")) or _nonempty(io.get("common_difficulties")) or _nonempty(io.get("productive_misconceptions"))):
        r["developmental_difficulties"] = ("KB", "io.common_obstacles/difficulties")
    elif ex and _nonempty(ex.get("failure_modes")):
        r["developmental_difficulties"] = ("KB", "exit.failure_modes")
    else:
        r["developmental_difficulties"] = (None, None)

    # 6 instructional strategies
    if io and (_nonempty(io.get("next_developmental_moves")) or _nonempty(io.get("revision_strategies")) or _nonempty(io.get("developmental_invitations"))):
        r["instructional_strategies"] = ("KB", "io.next_moves/revision_strategies/invitations")
    else:
        r["instructional_strategies"] = (None, None)

    # 7 observable indicators
    if io and (_nonempty(io.get("indicators_of_control")) or _nonempty(io.get("indicators_of_development")) or _nonempty(io.get("recognition_diagnostics"))):
        r["observable_indicators"] = ("KB", "io.indicators/recognition_diagnostics")
    else:
        r["observable_indicators"] = (None, None)

    # 8 exit criteria
    if ex and _nonempty(ex.get("exit_criterion")):
        r["exit_criteria"] = ("KB", "exit.exit_criterion")
    elif io and _nonempty(io.get("stopping_conditions")):
        r["exit_criteria"] = ("PARTIAL", "io.stopping_conditions")
    else:
        r["exit_criteria"] = (None, None)

    return r, io, ex


def main():
    rows = {}
    for key, m in CANONICAL.items():
        rows[key], _, _ = check_element(key, m)

    lines = ["# Writing Knowledge Base — Instructional Completeness Audit\n"]
    lines.append(f"Canonical instructional elements audited: **{len(CANONICAL)}**  ")
    lines.append(f"instructional_objects.json total elements: **{len(IO)}**  ")
    lines.append(f"exit_criteria elements: **{len(EXIT_BY_ID)}** · canonical_explanations: **{len(CANON_EXPL)}**\n")

    # Legend
    lines.append("Legend: ✅ present (KB) · ◐ partial/approx source · ❌ missing\n")

    # Header
    hdr = "| Element | " + " | ".join(d.replace("_", " ") for d in DIMS) + " |"
    sep = "|" + "---|" * (len(DIMS) + 1)
    lines.append(hdr)
    lines.append(sep)

    def cell(v):
        status, _src = v
        return {"KB": "✅", "PARTIAL": "◐", None: "❌"}[status]

    complete = 0
    gaps = []
    for key, r in rows.items():
        cells = [cell(r[d]) for d in DIMS]
        lines.append(f"| `{key}` | " + " | ".join(cells) + " |")
        missing = [d for d in DIMS if r[d][0] is None]
        partial = [d for d in DIMS if r[d][0] == "PARTIAL"]
        if not missing and not partial:
            complete += 1
        if missing or partial:
            gaps.append((key, missing, partial))

    lines.append("")
    lines.append(f"**Fully instructionally complete (all 8, KB source): {complete}/{len(CANONICAL)}**\n")

    lines.append("## Gaps to close (instructional completeness)\n")
    if not gaps:
        lines.append("None — every canonical element resolves all 8 dimensions from the KB.\n")
    for key, missing, partial in gaps:
        lines.append(f"- **`{key}`**")
        if missing:
            lines.append(f"  - ❌ MISSING: {', '.join(missing)}")
        if partial:
            lines.append(f"  - ◐ PARTIAL/approx source: {', '.join(partial)}")

    # Source-map appendix (so the hydrator knows exactly where each field comes from)
    lines.append("\n## Source map (field → KB location) for the hydrator\n")
    for key, m in CANONICAL.items():
        lines.append(f"- `{key}`  →  io=`{m['io']}`  exit_id=`{m['exit']}`  explanation=`canonical_explanations['{key}']`")

    out = REPORTS / "kb_instructional_completeness_audit.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")
    print(f"complete={complete}/{len(CANONICAL)}  gaps={len(gaps)}")
    for key, missing, partial in gaps:
        print(f"  {key}: missing={missing} partial={partial}")


if __name__ == "__main__":
    main()
