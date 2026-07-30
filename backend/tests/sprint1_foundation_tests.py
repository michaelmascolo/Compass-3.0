"""Sprint 1 acceptance tests A-G for the Instructional State / Evidence / Audit foundation.
Runs against the external API URL. Prints PASS/FAIL per test with detail.
"""
import os, sys, json, time, urllib.request, urllib.error

API = os.environ.get("API_URL") or "http://localhost:8001"
BASE = API.rstrip("/") + "/api"


def call(method, path, body=None, expect=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            code = r.status
            payload = json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        code = e.code
        try:
            payload = json.loads(e.read().decode() or "null")
        except Exception:
            payload = None
    return code, payload


results = []
def record(name, ok, detail):
    results.append((name, ok, detail))
    print(("PASS" if ok else "FAIL"), name, "::", detail)


SUF = str(int(time.time()))
student = f"stud-{SUF}"
assignment = f"assign-{SUF}"

# ---- create a state ----
code, st = call("POST", "/instructional-state", {
    "student_id": student, "teacher_id": "teacher-1", "assignment_id": assignment,
    "assignment_purpose": "persuade", "intended_reader": "school board", "genre": "op-ed",
    "grade_level": "9", "current_student_text": "Homework should be reduced.",
})
sid = st["id"]

# ---- A: revision persists across refresh ----
code, _ = call("POST", f"/instructional-state/{sid}/revision", {"text": "Homework should be reduced because rest improves learning."})
code, reload = call("GET", f"/instructional-state/{sid}")
a_ok = (reload["current_student_text"].startswith("Homework should be reduced because")
        and len(reload["revision_history"]) >= 2 and reload["version"] >= 2)
record("A_revision_persists_across_refresh", a_ok,
       f"version={reload['version']} revisions={len(reload['revision_history'])}")

# ---- B: OBSERVED and HYPOTHESIZED stored separately, categories distinct ----
code, ev_obs = call("POST", f"/instructional-state/{sid}/evidence", {
    "category": "OBSERVED", "description": "The draft states a claim in the first sentence.",
    "text_span": "Homework should be reduced", "source": "student_text",
    "candidate_instructional_object": "Thesis"})
code, ev_hyp = call("POST", f"/instructional-state/{sid}/evidence", {
    "category": "HYPOTHESIZED", "description": "The student may not yet grasp contestability of a thesis.",
    "source": "system_state", "candidate_instructional_object": "Thesis", "confidence": "low"})
code, reload = call("GET", f"/instructional-state/{sid}")
b_ok = (ev_obs["evidence"]["category"] == "OBSERVED"
        and ev_hyp["evidence"]["category"] == "HYPOTHESIZED"
        and len(reload["observed_evidence"]) == 1
        and len(reload["provisional_hypotheses"]) == 1)
record("B_observed_vs_hypothesized_separated", b_ok,
       f"observed={len(reload['observed_evidence'])} hypothesized={len(reload['provisional_hypotheses'])}")

# ---- C: missing evidence -> UNKNOWN, not fabricated ----
code, ev_unk = call("POST", f"/instructional-state/{sid}/evidence", {
    "category": "UNKNOWN", "description": "Whether the student understands audience is not yet observable.",
    "source": "system_state"})
c_ok = (ev_unk["evidence"]["category"] == "UNKNOWN")
record("C_missing_evidence_is_UNKNOWN", c_ok, f"category={ev_unk['evidence']['category']}")

# extra: DS-02 guard — prohibited attribution as OBSERVED must be REJECTED
code_bad, bad = call("POST", f"/instructional-state/{sid}/evidence", {
    "category": "OBSERVED", "description": "This student is lazy and not a writer.", "source": "teacher_input"})
ds02_ok = (code_bad == 422 and isinstance(bad, dict) and bad.get("detail", {}).get("requirement_id") == "DS-02")
record("DS02_prohibited_attribution_rejected", ds02_ok, f"http={code_bad}")

# ---- D: teacher override recorded + visible after refresh (trace) ----
code, _ = call("POST", f"/instructional-state/{sid}/override", {
    "teacher_id": "teacher-1", "field": "scaffolding_level", "from_value": "UNKNOWN",
    "to_value": "high_support", "reason": "student new to op-eds"})
code, trace = call("GET", f"/instructional-state/{sid}/trace?viewer_role=teacher")
d_ok = (trace.get("current_support_level") == "high_support"
        and len(trace.get("teacher_overrides", [])) >= 1)
record("D_teacher_override_visible_after_refresh", d_ok,
       f"support={trace.get('current_support_level')} overrides={len(trace.get('teacher_overrides',[]))}")

# authorization: student must NOT see the trace
code_forbidden, _ = call("GET", f"/instructional-state/{sid}/trace?viewer_role=student")
record("trace_restricted_from_student", code_forbidden == 403, f"http={code_forbidden}")

# ---- E: audit event links requirement IDs ----
code, audit = call("GET", f"/instructional-state/{sid}/audit?viewer_role=teacher")
with_reqs = [e for e in audit["events"] if e.get("requirement_ids")]
e_ok = len(with_reqs) >= 1
record("E_audit_links_requirement_ids", e_ok,
       f"events={audit['count']} with_reqs={len(with_reqs)} sample={with_reqs[0]['requirement_ids'] if with_reqs else []}")

# ---- happy-path advance on this state (has OBSERVED evidence) ----
code_adv, adv = call("POST", f"/instructional-state/{sid}/advance", {
    "target_instructional_object": "Thesis", "requested_exit_status": "met"})
happy_ok = (code_adv == 200 and adv.get("advancement_decision") == "advance")
record("advance_happy_path_with_observed_support", happy_ok, f"http={code_adv} decision={adv.get('advancement_decision') if isinstance(adv,dict) else adv}")

# ---- F: contradictory state blocks advancement (exit=met, NO observed evidence) ----
code, st2 = call("POST", "/instructional-state", {
    "student_id": f"stud2-{SUF}", "teacher_id": "teacher-1", "assignment_id": f"assign2-{SUF}",
    "current_student_text": "Some text."})
sid2 = st2["id"]
code_f, blocked = call("POST", f"/instructional-state/{sid2}/advance", {
    "target_instructional_object": "Thesis", "requested_exit_status": "met"})
code, reload2 = call("GET", f"/instructional-state/{sid2}")
f_ok = (code_f == 409 and "VA-07" in (blocked.get("detail", {}).get("failed_requirements", []))
        and reload2["advancement_decision"] == "blocked" and reload2["last_diagnostic_notice"])
record("F_contradiction_blocks_advancement", f_ok,
       f"http={code_f} decision={reload2['advancement_decision']} notice={bool(reload2['last_diagnostic_notice'])}")

# ---- G: migration keeps existing records accessible ----
code_m, mig = call("POST", "/admin/foundation/migrate?viewer_role=admin&limit=50")
g_ok = (code_m == 200 and isinstance(mig, dict) and ("created" in mig))
record("G_migration_preserves_and_maps_existing", g_ok,
       f"http={code_m} created={mig.get('created')} skipped={mig.get('skipped_already_migrated')} limitations={mig.get('total_migration_limitations_logged')}")

# append-only audit: a correction supersedes but does not erase
if with_reqs:
    orig_id = audit["events"][0]["id"]
    code, corr = call("POST", f"/instructional-state/{sid}/audit/correct?supersedes_id={orig_id}&rationale=test&viewer_role=teacher")
    code, audit2 = call("GET", f"/instructional-state/{sid}/audit?viewer_role=teacher")
    orig_still = next((e for e in audit2["events"] if e["id"] == orig_id), None)
    append_ok = (audit2["count"] > audit["count"] and orig_still is not None
                 and orig_still.get("superseded_by"))
    record("audit_append_only_correction", append_ok,
           f"before={audit['count']} after={audit2['count']} original_preserved={orig_still is not None}")

print("\n==== SUMMARY ====")
passed = sum(1 for _, ok, _ in results if ok)
print(f"{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
