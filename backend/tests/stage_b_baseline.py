"""Step 3 — Phase A/C/D baseline capture + judgment comparator for the 66-case benchmark.

Usage:
  python3 tests/stage_b_baseline.py capture <out.json> [limit]   # run corpus, save judgments+coaching
  python3 tests/stage_b_baseline.py compare <baseline.json> <candidate.json>  # certify equivalence

Certification compares INSTRUCTIONAL JUDGMENT (not text): object, bottleneck, evidence, strategy,
dependency, sequence, exit, next, plus coaching presence. Deterministic fields (exit, relationships)
are expected to be IDENTICAL post-migration because they are hydrated from the KB.
"""
import sys, json, asyncio, time, hashlib, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from server import Session, Telos, InteractRequest

CORPUS = Path(__file__).resolve().parents[1] / "test_cases" / "instructional_test_cases.json"
REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PY = Path(__file__).resolve().parents[1] / "server.py"


def _git(args):
    try:
        return subprocess.check_output(["git"] + args, cwd=str(REPO_ROOT),
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def provenance() -> dict:
    """Permanently tie a benchmark run to the exact code that produced it.
    Records the git commit, working-tree cleanliness, the byte-hash of server.py,
    and the SYSTEM_MESSAGE hash actually loaded into this process."""
    dirty = _git(["status", "--porcelain"]) or ""
    sys_msg = getattr(server, "SYSTEM_MESSAGE", "") or ""
    return {
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git_commit": _git(["rev-parse", "HEAD"]),
        "git_short": _git(["rev-parse", "--short", "HEAD"]),
        "git_working_tree_dirty": bool(dirty.strip()),
        "git_dirty_files": [l.strip() for l in dirty.splitlines() if l.strip()],
        "server_py_sha256": hashlib.sha256(SERVER_PY.read_bytes()).hexdigest(),
        "system_message_sha256_16": hashlib.sha256(sys_msg.encode()).hexdigest()[:16],
    }


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


async def run_capture(out_path, limit=None, ids=None):
    prov = provenance()
    print("PROVENANCE:", json.dumps(prov))
    corpus = json.loads(CORPUS.read_text())
    cases = corpus if isinstance(corpus, list) else corpus.get("cases", corpus)
    if ids:
        idset = set(ids)
        cases = [c for c in cases if c.get("id") in idset]
    elif limit:
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
    Path(out_path).write_text(json.dumps({"provenance": prov, "results": results}, indent=2, ensure_ascii=False))
    print("wrote", out_path)


def _load_results(path):
    """Accept both the new provenance-wrapped format and the legacy bare-list format."""
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        return data.get("results", []), data.get("provenance")
    return data, None


def _sim(a, b):
    """Token-overlap (Jaccard) for free-text fields — instructional-content similarity,
    not textual identity."""
    sa = {w for w in _norm(a).split() if len(w) > 3}
    sb = {w for w in _norm(b).split() if len(w) > 3}
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def compare(baseline_path, candidate_path):
    b_results, b_prov = _load_results(baseline_path)
    c_results, c_prov = _load_results(candidate_path)
    B = {r["id"]: r for r in b_results if "error" not in r}
    C = {r["id"]: r for r in c_results if "error" not in r}
    print("=== PROVENANCE ===")
    print("  BASELINE :", json.dumps(b_prov) if b_prov else "(legacy — no provenance recorded)")
    print("  CANDIDATE:", json.dumps(c_prov) if c_prov else "(legacy — no provenance recorded)")
    if b_prov and c_prov and b_prov.get("server_py_sha256") == c_prov.get("server_py_sha256"):
        print("  NOTE: identical server.py sha256 in both files → this is a NOISE-FLOOR comparison (same code).")
    print()
    ids = [i for i in B if i in C]
    # categorical instructional judgments — equivalence is meaningful (exact after _key/_norm)
    keys_cat = ["object", "dependency", "sequence", "sufficiency"]
    # free-text judgments/deterministic — compare by content SIMILARITY (not identity)
    keys_text = ["bottleneck", "exit", "next"]
    agree = {k: 0 for k in keys_cat}
    sim = {k: [] for k in keys_text}
    diffs = []
    for i in ids:
        b, c = B[i], C[i]
        row_diff = {}
        for k in keys_cat:
            if _norm(b.get(k)) == _norm(c.get(k)):
                agree[k] += 1
            else:
                row_diff[k] = {"baseline": b.get(k), "candidate": c.get(k)}
        for k in keys_text:
            sim[k].append(_sim(b.get(k), c.get(k)))
        if row_diff:
            diffs.append({"id": i, "diff": row_diff})
    n = len(ids)
    print(f"compared {n} cases")
    print("  -- categorical instructional judgment (exact equivalence) --")
    for k in keys_cat:
        print(f"    {k:12s}: {agree[k]}/{n}  ({100*agree[k]//max(1,n)}%)")
    print("  -- free-text fields (content similarity, mean Jaccard) --")
    for k in keys_text:
        m = sum(sim[k]) / max(1, len(sim[k]))
        print(f"    {k:12s}: {m:.2f}")
    print(f"  cases with any categorical diff: {len(diffs)}/{n}")
    Path("/tmp/baseline_compare.json").write_text(json.dumps({"n": n, "agree": agree, "diffs": diffs}, indent=2, ensure_ascii=False))
    print("details -> /tmp/baseline_compare.json")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "capture"
    if cmd == "capture":
        out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/stage_b_baseline.json"
        arg3 = sys.argv[3] if len(sys.argv) > 3 else None
        if arg3 and not arg3.isdigit():
            asyncio.run(run_capture(out, ids=[x.strip() for x in arg3.split(",") if x.strip()]))
        else:
            asyncio.run(run_capture(out, int(arg3) if arg3 else None))
    elif cmd == "compare":
        compare(sys.argv[2], sys.argv[3])
