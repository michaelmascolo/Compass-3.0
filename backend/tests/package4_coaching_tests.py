"""Revision Package 4 — coaching-driven-by-decision certification tests (Cases 1-4) + live check."""
import sys, json, time, urllib.request, urllib.error
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
import compass_coaching_controller as CC

BASE = "http://localhost:8001/api"
results = []
def rec(n, ok, d=""):
    results.append(ok); print(("PASS" if ok else "FAIL"), n, "::", d)

# CASE 1 — READY + NEEDS_INSTRUCTION, target Thesis -> teach only Thesis (frozen invitation)
inv = "You've made a start. Let's work on your thesis: try turning it into one contestable claim."
r = CC.select_response({"decision_status": "READY", "instructional_need": "NEEDS_INSTRUCTION",
                        "selected_instructional_object": "Thesis", "demonstrated_strengths": ["clear topic"]}, inv)
rec("P4_case1_teaches_only_thesis",
    r["coaching_path"] == "CASE_1_TEACH_ONE_TARGET" and r["learner_text"] == inv
    and r["one_target"] and r["instructional_target_presented"] == "Thesis"
    and r["consistent_with_decision"], f"path={r['coaching_path']} consistent={r['consistent_with_decision']}")

# CASE 2 — READY + NO_CURRENT_INSTRUCTIONAL_TARGET -> invent no weakness
r = CC.select_response({"decision_status": "READY", "instructional_need": "NO_CURRENT_INSTRUCTIONAL_TARGET",
                        "selected_instructional_object": None,
                        "demonstrated_strengths": ["a clear contestable thesis", "well-chosen evidence"]}, "")
no_weakness = ("don't see one clear" in r["learner_text"].lower()) and ("you need to" not in r["learner_text"].lower())
rec("P4_case2_invents_no_weakness",
    r["coaching_path"] == "CASE_2_NO_CURRENT_TARGET" and r["instructional_target_presented"] is None
    and no_weakness and r["cognitive_ownership_ok"], f"path={r['coaching_path']}")

# CASE 3 — BLOCKED -> gather evidence only, no instruction
for st in ("BLOCKED_INSUFFICIENT_EVIDENCE", "BLOCKED_CONTRADICTORY_EVIDENCE", "BLOCKED_PREREQUISITE_UNKNOWN"):
    r = CC.select_response({"decision_status": st, "instructional_need": "NEEDS_INSTRUCTION",
                            "selected_instructional_object": None, "demonstrated_strengths": []}, "IGNORED ENGINE TEXT")
    ok = (r["coaching_path"] == "CASE_3_BLOCKED_GATHER_EVIDENCE" and r["instructional_target_presented"] is None
          and r["learner_text"] != "IGNORED ENGINE TEXT" and r["cognitive_ownership_ok"])
    rec(f"P4_case3_gather_only[{st}]", ok, f"path={r['coaching_path']}")

# CASE 4 — TEACHER_OVERRIDE -> follow teacher target
r = CC.select_response({"decision_status": "TEACHER_OVERRIDE", "instructional_need": "NEEDS_INSTRUCTION",
                        "selected_instructional_object": "Conclusion",
                        "selected_object_definition": "Consolidates the argument's meaning.",
                        "engine_recommendation": "Evidence", "demonstrated_strengths": []}, "engine taught Evidence")
rec("P4_case4_follows_teacher_target",
    r["coaching_path"] == "CASE_4_TEACHER_OVERRIDE" and r["instructional_target_presented"] == "Conclusion"
    and "conclusion" in r["learner_text"].lower() and r["cognitive_ownership_ok"], f"presented={r['instructional_target_presented']}")

# cognitive ownership: controller-authored text never does the learner's work
allbad = []
for st, need, tgt in [("READY","NO_CURRENT_INSTRUCTIONAL_TARGET",None),
                      ("BLOCKED_INSUFFICIENT_EVIDENCE","NEEDS_INSTRUCTION",None),
                      ("TEACHER_OVERRIDE","NEEDS_INSTRUCTION","Thesis")]:
    r = CC.select_response({"decision_status":st,"instructional_need":need,"selected_instructional_object":tgt,
                            "demonstrated_strengths":[]}, "")
    if not r["cognitive_ownership_ok"]: allbad.append(st)
rec("P4_cognitive_ownership_preserved", not allbad, f"violations={allbad}")

# ============ LIVE — dialogue is the decision-driven text (persisted before presentation) ============
def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as x: return x.status, json.loads(x.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode() or "null")
        except Exception: return e.code, None

code, sess = call("POST", "/sessions", {
    "assignment": "Is a four-day school week a good idea?", "assignment_prompt": "Argue a position.",
    "pedagogical_purpose": "Help the student form and support a central claim.",
    "current_writing_task": "Draft your response.", "teacher_notes": ""})
sid = sess["id"]
call("POST", f"/sessions/{sid}/interact", {"content": "Four day weeks. Good idea. Kids like it.", "kind": "writing"})
ai_text, done = "", False
for _ in range(60):
    time.sleep(3)
    code, s = call("GET", f"/sessions/{sid}")
    ai = [t for t in s["turns"] if t["role"] == "ai"]
    if ai and ai[-1]["status"] == "complete" and ai[-1]["content"]:
        ai_text = ai[-1]["content"]; done = True; break
    if ai and ai[-1]["status"] == "failed": break
code, st = call("GET", f"/instructional-state-by-session/{sid}")
code, trace = call("GET", f"/instructional-state/{st['id']}/trace?viewer_role=teacher") if st else (0, {})
code, audit = call("GET", f"/instructional-state/{st['id']}/audit?viewer_role=teacher") if st else (0, {"events": []})
cd = [e for e in audit.get("events", []) if e["event_type"] == "coaching_dialogue"]
path_set = bool(trace.get("coaching_path"))
tied = bool(cd) and (cd[-1]["generated_response"][:60] == (ai_text or "")[:60])
rec("P4_live_coaching_path_recorded", done and path_set, f"path={trace.get('coaching_path')}")
rec("P4_live_presented_text_is_decision_driven", tied,
    "audit coaching_dialogue.generated_response == presented AI turn text")

print("\n==== SUMMARY ====")
print(f"{sum(results)}/{len(results)} checks passed")
