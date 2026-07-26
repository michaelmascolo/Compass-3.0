"""Live-engine test (slow, ~60-180s). Verifies objective locks after first turn."""
import os
import time
import requests

with open("/app/frontend/.env") as f:
    for line in f:
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

def test_live_objective_locks_after_first_turn():
    r = requests.post(f"{BASE_URL}/api/sessions/preview", json={}, timeout=30)
    assert r.status_code == 200
    sid = r.json()["id"]
    ec0 = r.json()["experience_control"]
    assert ec0["objective_locked"] is False

    seed = ("The mobile phones in schools debate is complicated. Some people say they help "
            "students learn because they can look things up quickly. Other people say phones "
            "are just a distraction and students never focus. I think schools should let "
            "students use them but with rules.")
    r2 = requests.post(
        f"{BASE_URL}/api/sessions/{sid}/interact",
        json={"kind": "writing", "content": seed},
        timeout=30,
    )
    assert r2.status_code == 200, r2.text

    # Poll until AI turn completes
    deadline = time.time() + 240
    last = None
    while time.time() < deadline:
        g = requests.get(f"{BASE_URL}/api/sessions/{sid}", timeout=30)
        assert g.status_code == 200
        last = g.json()
        turns = last.get("turns", [])
        ai_turns = [t for t in turns if t.get("role") == "ai"]
        if ai_turns and ai_turns[-1].get("status") == "complete":
            break
        time.sleep(5)
    else:
        raise AssertionError(f"AI turn didn't complete in time; last status: "
                             f"{[t.get('status') for t in last.get('turns', [])] if last else 'no session'}")

    ec = last.get("experience_control")
    assert ec is not None
    print("experience_control after first turn:", ec)
    assert ec.get("objective_locked") is True, f"objective not locked: {ec}"
    assert ec.get("objective_element"), f"objective_element empty: {ec}"
    assert ec.get("phase") == "active"


if __name__ == "__main__":
    test_live_objective_locks_after_first_turn()
    print("OK")
