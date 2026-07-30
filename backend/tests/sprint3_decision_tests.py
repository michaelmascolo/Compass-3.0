"""Sprint 3 — Instructional Decision Engine certification tests 1-12 + guards DE-01..DE-05, TC-02."""
import sys, json, time, urllib.request, urllib.error
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
import compass_decision_engine as DE
from compass_decision_engine import EvidenceView as EV

BASE = "http://localhost:8001/api"
results = []
def rec(name, ok, detail=""):
    results.append(ok); print(("PASS" if ok else "FAIL"), name, "::", detail)

def obs(o, pol, desc): return EV("OBSERVED", o, pol, desc)
def hyp(desc): return EV("HYPOTHESIZED", None, "na", desc)
def unk(desc): return EV("UNKNOWN", None, "na", desc)

def guards_ok(d):
    observed = []  # rebuilt inside; use d.observed_selection_evidence check via run_guards
    return all(g["passed"] for g in DE.run_guards(d, [EV("OBSERVED", d.selected_instructional_object, "present", s) for s in d.observed_selection_evidence]))

# T1 — no thesis, polished sentences -> Thesis (not Sentence Construction)
d = DE.decide([obs("Sentence Construction", "present", "Sentences are grammatically polished."),
               obs("Thesis", "absent", "No sentence states an identifiable central claim.")])
rec("T1_no_thesis_polished_sentences", d.selected_instructional_object == "Thesis"
    and d.decision_status == "READY", f"selected={d.selected_instructional_object} status={d.decision_status}")

# T2 — clear claim, no evidence -> Evidence (claim confirmed identifiable)
d = DE.decide([obs("Thesis", "present", "A clear central claim is stated."),
               obs("Evidence", "absent", "No supporting evidence is provided.")])
rec("T2_claim_no_evidence", d.selected_instructional_object == "Evidence"
    and d.structural_prerequisite_status == "MET", f"selected={d.selected_instructional_object} prereq={d.structural_prerequisite_status}")

# T3 — evidence present, relationship unexplained -> Explanation (don't request more evidence)
d = DE.decide([obs("Thesis", "present", "Claim is stated."),
               obs("Evidence", "present", "Relevant evidence is provided."),
               obs("Explanation", "absent", "The relationship between claim and evidence is not made explicit.")])
rec("T3_relationship_unexplained", d.selected_instructional_object == "Explanation"
    and "Evidence" not in d.candidate_instructional_objects, f"selected={d.selected_instructional_object}")

# T4 — several competing paragraph ideas -> Paragraph Main Point (before sentence refinement)
d = DE.decide([obs("Sentence Construction", "present", "Sentences are fluent."),
               obs("Paragraph Main Point", "absent", "Several competing ideas; no single governing point.")])
rec("T4_competing_ideas", d.selected_instructional_object == "Paragraph Main Point", f"selected={d.selected_instructional_object}")

# T5 — mechanical transition, unclear relationship -> underlying relationship (not a new transition word)
d = DE.decide([obs("Thesis", "present", "Idea one is present."),
               obs("Evidence", "present", "Idea two is present."),
               obs("Transition", "weak", "A transition word is used but the relationship between the two ideas is unclear.")])
rec("T5_transition_relationship", d.selected_instructional_object == "Explanation"
    and d.selected_instructional_object != "Transition", f"selected={d.selected_instructional_object} rationale={d.priority_rationale[:60]}")

# T6 — strong writing -> no invented weakness
d = DE.decide([obs("Thesis", "present", "Strong contestable claim."),
               obs("Evidence", "present", "Well-chosen evidence."),
               obs("Explanation", "present", "Clear reasoning."),
               obs("Conclusion", "present", "Effective conclusion.")])
rec("T6_strong_writing_no_invented_weakness",
    d.selected_instructional_object is None and d.decision_status == "READY"
    and d.instructional_need == "NO_CURRENT_INSTRUCTIONAL_TARGET",
    f"selected={d.selected_instructional_object} status={d.decision_status} need={d.instructional_need}")

# T7 — insufficient evidence -> block, record UNKNOWN
d = DE.decide([hyp("Student may not understand thesis contestability."), unk("Audience awareness not observable.")])
rec("T7_insufficient_evidence_blocked",
    d.decision_status == "BLOCKED_INSUFFICIENT_EVIDENCE" and d.selected_instructional_object is None
    and d.strength_status == "UNKNOWN", f"status={d.decision_status}")

# T8 — contradictory evidence -> block/uncertain, don't silently choose
d = DE.decide([obs("Thesis", "present", "States a clear claim."),
               obs("Thesis", "absent", "No identifiable claim present.")])
rec("T8_contradictory_evidence_blocked",
    d.decision_status == "BLOCKED_CONTRADICTORY_EVIDENCE" and d.selected_instructional_object is None,
    f"status={d.decision_status}")

# T9 — multiple weaknesses -> store multiple candidates, select exactly one
d = DE.decide([obs("Thesis", "present", "Claim present."),
               obs("Evidence", "absent", "No evidence."),
               obs("Explanation", "absent", "No reasoning."),
               obs("Transition", "absent", "No transitions."),
               obs("Sentence Construction", "absent", "Some run-ons.")])
one = (d.selected_instructional_object is not None) and len(d.deferred_targets) >= 1
rec("T9_multiple_weaknesses_one_target", one and d.selected_instructional_object == "Evidence"
    and len(d.candidate_instructional_objects) >= 3,
    f"selected={d.selected_instructional_object} candidates={d.candidate_instructional_objects} deferred={d.deferred_targets}")

# T10 — teacher override -> preserve original recommendation, honor teacher selection
d = DE.decide([obs("Thesis", "present", "Claim present."), obs("Evidence", "absent", "No evidence.")],
              teacher_override={"field": "selected_instructional_object", "to_value": "Thesis"})
rec("T10_teacher_override_preserves_original",
    d.decision_status == "TEACHER_OVERRIDE" and d.selected_instructional_object == "Thesis"
    and d.engine_recommendation == "Evidence",
    f"selected={d.selected_instructional_object} engine_rec={d.engine_recommendation}")

# T11 — personal attribution suppressed from selection evidence
d = DE.decide([obs("Thesis", "present", "Claim present."),
               obs("Evidence", "absent", "No evidence."),
               obs(None, "present", "The student is careless and unmotivated.")])
attribution_in_evidence = any("careless" in s.lower() or "unmotivated" in s.lower() for s in d.observed_selection_evidence)
de05 = [g for g in DE.run_guards(d, []) if g["requirement_id"] == "DE-05"][0]["passed"]
rec("T11_personal_attribution_suppressed",
    d.selected_instructional_object == "Evidence" and not attribution_in_evidence and de05
    and any("suppressed" in u.lower() for u in d.decision_uncertainty),
    f"selected={d.selected_instructional_object} attribution_leaked={attribution_in_evidence}")

# ---- guards on representative decisions ----
for label, dd in [("ready", DE.decide([obs("Thesis","present","c"), obs("Evidence","absent","e")])),
                  ("blocked", DE.decide([])),
                  ("no_target", DE.decide([obs("Thesis","present","c"), obs("Evidence","present","e"), obs("Explanation","present","x")]))]:
    obs_list = [EV("OBSERVED", dd.selected_instructional_object, "present", s) for s in dd.observed_selection_evidence]
    gs = DE.run_guards(dd, obs_list)
    rec(f"guards_all_pass_{label}", all(g["passed"] for g in gs), str({g["requirement_id"]: g["passed"] for g in gs}))

# ============ T12 — live persistence-before-presentation (real turn) ============
def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode() or "null")
        except Exception: return e.code, None

code, sess = call("POST", "/sessions", {
    "assignment": "Should schools start later in the morning?",
    "assignment_prompt": "Take a position and support it.",
    "pedagogical_purpose": "Help the student form and support a central claim.",
    "current_writing_task": "Draft your response.", "teacher_notes": ""})
sid = sess["id"]
call("POST", f"/sessions/{sid}/interact", {"content": "Later start times. Teens are tired. School is early.", "kind": "writing"})
done = False
for _ in range(60):
    time.sleep(3)
    code, s = call("GET", f"/sessions/{sid}")
    ai = [t for t in s["turns"] if t["role"] == "ai"]
    if ai and ai[-1]["status"] == "complete" and ai[-1]["content"]:
        done = True; break
    if ai and ai[-1]["status"] == "failed": break
code, st = call("GET", f"/instructional-state-by-session/{sid}")
decision_present = bool(st) and bool(st.get("decision_status")) and bool(st.get("decision_requirement_ids"))
rec("T12_persistence_before_presentation",
    done and decision_present,
    f"turn_complete={done} decision_status={st.get('decision_status') if st else None} selected={st.get('selected_instructional_object') if st else None}")

# TC-02 live: teacher target override on the real state, preserving engine recommendation
if st:
    engine_rec = st.get("selected_instructional_object")
    code, ov = call("POST", f"/instructional-state/{st['id']}/target-override?teacher_id=t1&to_object=Conclusion&reason=class%20focus&viewer_role=teacher")
    code, st2 = call("GET", f"/instructional-state/{st['id']}")
    rec("TC02_teacher_override_separately_recorded",
        st2.get("selected_instructional_object") == "Conclusion"
        and st2.get("engine_recommendation") == engine_rec
        and st2.get("decision_status") == "TEACHER_OVERRIDE"
        and len(st2.get("teacher_overrides", [])) >= 1,
        f"selected={st2.get('selected_instructional_object')} engine_rec={st2.get('engine_recommendation')}")

print("\n==== SUMMARY ====")
print(f"{sum(results)}/{len(results)} checks passed")
