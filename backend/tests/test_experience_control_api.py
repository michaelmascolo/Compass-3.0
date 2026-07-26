"""Backend API tests for Experience Compass Slice 1.

Fast tests only (no live LLM). Covers:
- POST /api/sessions/preview returns is_preview + experience_control defaults.
- POST /api/sessions (non-preview) leaves experience_control = null.
- POST /api/sessions/{id}/interact returns 409 when phase is 'reflection'
  (we force the flip in Mongo, since a real live cycle takes several minutes).
"""
import os
import asyncio
import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def test_preview_session_creates_experience_control(api):
    r = api.post(f"{BASE_URL}/api/sessions/preview", json={})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("is_preview") is True
    ec = data.get("experience_control")
    assert ec is not None, "preview session missing experience_control"
    assert ec.get("phase") == "active"
    assert ec.get("support_cap") == 3
    assert ec.get("objective_locked") is False
    assert ec.get("reflection") is None
    assert ec.get("support_count") == 0
    assert ec.get("revision_count") == 0
    assert ec.get("objective_element") == ""
    return data["id"]


def _get_any_config_id(api):
    """Grab a config id from the /api/configs endpoint (used by non-preview sessions)."""
    r = api.get(f"{BASE_URL}/api/configs")
    assert r.status_code == 200, r.text
    configs = r.json()
    assert isinstance(configs, list) and configs, "no configs available"
    return configs[0]["id"]


def test_non_preview_session_has_no_experience_control(api):
    payload = {
        "assignment": "TEST_ short essay",
        "pedagogical_purpose": "TEST_ test purpose",
        "current_writing_task": "TEST_ write a passage",
        "teacher_notes": "TEST_",
    }
    r = api.post(f"{BASE_URL}/api/sessions", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("is_preview") is False
    assert data.get("experience_control") is None, \
        f"non-preview must not have experience_control, got: {data.get('experience_control')}"


def test_interact_returns_409_when_phase_is_reflection(api):
    """Create a preview session, force phase=reflection in Mongo, then hit /interact -> expect 409."""
    r = api.post(f"{BASE_URL}/api/sessions/preview", json={})
    assert r.status_code == 200
    session_id = r.json()["id"]

    async def flip():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        res = await db.sessions.update_one(
            {"id": session_id},
            {"$set": {
                "experience_control.phase": "reflection",
                "experience_control.reflection": {
                    "objective_element": "clarity",
                    "objective": "one thing",
                    "how_your_writing_changed": "not yet",
                    "why_it_helps_your_reader": "because",
                    "carry_it_forward": "next time",
                    "completion_reason": "support_cap",
                    "resolved": False,
                },
            }},
        )
        client.close()
        return res.modified_count

    modified = asyncio.get_event_loop().run_until_complete(flip()) \
        if not asyncio.get_event_loop().is_running() else asyncio.run(flip())
    assert modified == 1

    r2 = api.post(
        f"{BASE_URL}/api/sessions/{session_id}/interact",
        json={"kind": "writing", "content": "Some new passage to try."},
    )
    assert r2.status_code == 409, f"expected 409, got {r2.status_code}: {r2.text}"
    body = r2.json()
    assert "complete" in body.get("detail", "").lower() or "cycle" in body.get("detail", "").lower()
