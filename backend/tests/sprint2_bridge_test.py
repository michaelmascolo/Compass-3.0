"""Sprint 2 — Engine Bridge e2e test. Runs a REAL live coaching turn and verifies the
frozen engine both READ and WROTE persistent instructional state, with the generated
invitation tied to the structured decision. Localhost."""
import json, time, urllib.request, urllib.error

BASE = "http://localhost:8001/api"

def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode() or "null")
        except Exception: return e.code, None

results = []
def rec(name, ok, detail=""):
    results.append(ok); print(("PASS" if ok else "FAIL"), name, "::", detail)

# 1. create a real session
code, sess = call("POST", "/sessions", {
    "assignment": "Argue whether social media improves or harms teen friendships.",
    "assignment_prompt": "Take a clear position and defend it.",
    "pedagogical_purpose": "Help the student form and clarify a central claim that organizes the response.",
    "current_writing_task": "Draft your response.",
    "teacher_notes": "",
    "reasoning_mode": "exhaustive",  # Sprint-2 bridge is the legacy/rollback path; V2 (consolidated_v2) bypasses it by design
})
sid = sess["id"]
print("session", sid)

# 2. run a real interact turn
draft = "Social media is bad. It makes teens feel lonely and they compare themselves to others."
code, _ = call("POST", f"/sessions/{sid}/interact", {"content": draft, "kind": "writing"})

# 3. poll until the AI turn completes
ai_done, invitation = False, ""
for _ in range(60):
    time.sleep(3)
    code, s = call("GET", f"/sessions/{sid}")
    ai = [t for t in s["turns"] if t["role"] == "ai"]
    if ai and ai[-1]["status"] == "complete" and ai[-1]["content"]:
        ai_done = True; invitation = ai[-1]["content"]; break
    if ai and ai[-1]["status"] == "failed":
        break
rec("live_turn_completed", ai_done, f"invitation_len={len(invitation)}")

# 4. instructional state produced by the bridge (keyed by session)
code, st = call("GET", f"/instructional-state-by-session/{sid}")
have_state = bool(st)
rec("bridge_produced_instructional_state", have_state and st.get("turns_recorded", 0) >= 1,
    f"turns_recorded={st.get('turns_recorded') if st else None}")

if have_state:
    required = {
        "current_instructional_object": st.get("current_instructional_object"),
        "reason_for_selection": st.get("reason_for_selection"),
        "prerequisite_status": st.get("prerequisite_status"),
        "dialogue_state": st.get("dialogue_state"),
        "scaffolding_level(support)": st.get("scaffolding_level"),
        "current_learner_task": st.get("current_learner_task"),
        "last_learner_response": st.get("last_learner_response"),
        "exit_criterion_status": st.get("exit_criterion_status"),
        "advancement_decision": st.get("advancement_decision"),
        "revision_history": st.get("revision_history"),
    }
    for k, v in required.items():
        print(f"    {k}: {json.dumps(v)[:120]}")
    obj_ok = bool(st.get("current_instructional_object"))
    rec("selected_object_persisted", obj_ok, f"object={st.get('current_instructional_object')}")
    rec("learner_response_persisted", (draft[:20] in (st.get("last_learner_response") or "")),
        "learner draft captured")
    rec("exit_status_valid", st.get("exit_criterion_status") in ("met", "not_met", "UNKNOWN"),
        st.get("exit_criterion_status"))
    # epistemic separation present
    rec("epistemic_lists_present",
        isinstance(st.get("observed_strengths"), list) and isinstance(st.get("provisional_hypotheses"), list)
        and isinstance(st.get("unknowns"), list),
        f"obs={len(st.get('observed_strengths',[]))} hyp={len(st.get('provisional_hypotheses',[]))} unk={len(st.get('unknowns',[]))}")

    # 5. audit: turn_started (consumer read) + instructional_turn (producer write)
    code, audit = call("GET", f"/instructional-state/{st['id']}/audit?viewer_role=teacher")
    events = audit["events"]
    types = [e["event_type"] for e in events]
    rec("consumer_read_logged", "turn_started" in types, f"types={set(types)}")
    turn_evts = [e for e in events if e["event_type"] == "instructional_turn"]
    rec("producer_write_logged", len(turn_evts) >= 1, f"instructional_turn events={len(turn_evts)}")
    if turn_evts:
        te = turn_evts[-1]
        rec("audit_has_requirement_ids", bool(te["requirement_ids"]), str(te["requirement_ids"]))
        rec("audit_has_validation_results", len(te["validation_results"]) >= 4,
            f"{len(te['validation_results'])} guards")
        # 6. the generated invitation is tied to the structured decision (not text-only)
        gen = te.get("generated_response", "")
        rec("generated_text_tied_to_state", bool(gen) and gen[:60] == invitation[:60],
            "audit.generated_response matches AI turn invitation")
        rec("audit_output_state_complete",
            all(k in te["output_state"] for k in
                ("current_instructional_object", "reason_for_selection", "prerequisite_status",
                 "support_level", "current_learner_task", "exit_criterion_status", "advancement_decision")),
            "all required decision fields present in audit output_state")

print("\n==== SUMMARY ====")
print(f"{sum(results)}/{len(results)} checks passed")
