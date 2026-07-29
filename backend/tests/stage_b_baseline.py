"""Step 3 — Phase A/C/D baseline capture + judgment comparator for the 66-case benchmark.

Usage:
  python3 tests/stage_b_baseline.py capture <out.json> [limit]   # run corpus, save judgments+coaching
  python3 tests/stage_b_baseline.py compare <baseline.json> <candidate.json>  # certify equivalence

Certification compares INSTRUCTIONAL JUDGMENT (not text): object, bottleneck, evidence, strategy,
dependency, sequence, exit, next, plus coaching presence. Deterministic fields (exit, relationships)
are expected to be IDENTICAL post-migration because they are hydrated from the KB.
"""
import sys, json, asyncio, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from server import Session, Telos, InteractRequest

CORPUS = Path(__file__).resolve().parents[1] / "test_cases" / "instructional_test_cases.json"


def _norm(s):
    return " ".join(str(s or "").lower().split())


def _key(el):
    return server._element_key_for(el or "")


def build_session(case) -> Session:
    return Session(
        assignment=case.get("assignment", ""),
        assignment_prompt=case.get("assignment", ""),
        pedagogical_purpose=case.get("pedagogical_purpose", ""),
        current_writing_task=case.get("current_writing_task", ""),
        is_preview=False,
        telos=Telos(governing_pedagogical_purpose=case.get("pedagogical_purpose", ""),
                    immediate_task_purpose=case.get("current_writing_task", ""),
                    assignment_context=case.get("assignment", "")),
    )


def capture_judgment(case, parsed) -> dict:
    th = parsed.get("theory")
    d = th.model_dump() if hasattr(th, "model_dump") else (th or {})
    ir = d.get("instructional_reasoning", {})
    sr = d.get("structural_reasoning", {})
    sc = d.get("scaffolding_control", {})
    return {
        "id": case.get("id"), "name": case.get("name"),
        "object": _key(sc.get("primary_target") or ir.get("active_instructional_element")),
        "object_raw": sc.get("primary_target") or ir.get("active_instructional_element"),
        "bottleneck": _norm(ir.get("primary_developmental_tension")),
        "diagnosed": [_norm(x) for x in (sc.get("diagnosed_opportunities") or [])],
        "evidence": [_norm(x) for x in (d.get("supporting_evidence") or [])],
        "strategy": [_norm(x) for x in (ir.get("selected_developmental_resources") or [])],
        "dependency": _key(ir.get("required_dependency")) if ir.get("required_dependency") else "",
        "dependency_status": _norm(ir.get("dependency_status")),
        "sequence": _norm(ir.get("continue_consolidate_release_or_shift")),
        "sufficiency": _norm(ir.get("sufficiency_for_next_step")),
        "exit": _norm(sr.get("active_exit_criterion")),
        "next": _norm(ir.get("next_developmental_step")),
        "coaching": (parsed.get("_stage_b_invitation") and parsed.get("invitation")) or parsed.get("invitation", ""),
        "coaching_words": len((parsed.get("invitation") or "").split()),
    }


async def run_capture(out_path, limit=None):
    corpus = json.loads(CORPUS.read_text())
    cases = corpus if isinstance(corpus, list) else corpus.get("cases", corpus)
    if limit:
        cases = cases[:limit]
    results = []
    for i, case in enumerate(cases):
        draft = case.get("initial_draft") or (case.get("responses") or [""])[0]
        session = build_session(case)
        req = InteractRequest(content=draft, kind="writing")
        t0 = time.perf_counter()
        try:
            parsed = await server._run_engine(session, req)
            row = capture_judgment(case, parsed)
            row["_secs"] = round(time.perf_counter() - t0, 1)
            results.append(row)
            print(f"[{i+1}/{len(cases)}] {case.get('id')} object={row['object']!r} dep={row['dependency']!r} {row['_secs']}s")
        except Exception as e:
            print(f"[{i+1}/{len(cases)}] {case.get('id')} ERROR {e}")
            results.append({"id": case.get("id"), "error": str(e)})
    Path(out_path).write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print("wrote", out_path)


def compare(baseline_path, candidate_path):
    B = {r["id"]: r for r in json.loads(Path(baseline_path).read_text()) if "error" not in r}
    C = {r["id"]: r for r in json.loads(Path(candidate_path).read_text()) if "error" not in r}
    ids = [i for i in B if i in C]
    keys_exact = ["object", "dependency", "exit"]          # object/dependency judgment + hydrated exit
    keys_soft = ["sequence", "sufficiency"]                 # short categorical judgments
    agree = {k: 0 for k in keys_exact + keys_soft}
    diffs = []
    for i in ids:
        b, c = B[i], C[i]
        row_diff = {}
        for k in keys_exact + keys_soft:
            if _norm(b.get(k)) == _norm(c.get(k)):
                agree[k] += 1
            else:
                row_diff[k] = {"baseline": b.get(k), "candidate": c.get(k)}
        if row_diff:
            diffs.append({"id": i, "diff": row_diff})
    n = len(ids)
    print(f"compared {n} cases")
    for k in keys_exact + keys_soft:
        print(f"  {k:14s} equivalence: {agree[k]}/{n}  ({100*agree[k]//max(1,n)}%)")
    print(f"  cases with any judgment diff: {len(diffs)}/{n}")
    Path("/tmp/baseline_compare.json").write_text(json.dumps({"n": n, "agree": agree, "diffs": diffs}, indent=2, ensure_ascii=False))
    print("details -> /tmp/baseline_compare.json")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "capture"
    if cmd == "capture":
        out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/stage_b_baseline.json"
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else None
        asyncio.run(run_capture(out, lim))
    elif cmd == "compare":
        compare(sys.argv[2], sys.argv[3])
