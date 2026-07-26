"""Fast unit test of the Experience Compass single-objective state machine.
No LLM calls — feeds a synthetic engine `result` dict into the wrapper helpers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server as S
from server import (
    Session, ExperienceControl, InteractRequest, DevelopmentalTheory,
    _update_experience_control,
)


def make_result(element="Central Claim / Thesis", target="clarify the central claim",
                development_detected="", cycle_status=""):
    theory = DevelopmentalTheory()
    theory.instructional_reasoning.active_instructional_element = element
    theory.scaffolding_control.primary_target = target
    theory.scaffolding_control.cycle_status = cycle_status
    theory.revision_development.development_detected = development_detected
    return {"theory": theory}


def fresh_session():
    s = Session(assignment="a", pedagogical_purpose="p", current_writing_task="t",
                is_preview=True, experience_control=ExperienceControl())
    return s


def test_non_preview_untouched():
    s = Session(assignment="a", pedagogical_purpose="p", current_writing_task="t")
    assert s.experience_control is None
    _update_experience_control(s, InteractRequest(content="x", kind="writing"), make_result(), False)
    assert s.experience_control is None
    print("PASS non_preview_untouched")


def test_lock_once_and_never_changes():
    s = fresh_session()
    _update_experience_control(s, InteractRequest(content="seed", kind="writing"),
                               make_result(element="Central Claim / Thesis"), False)
    ec = s.experience_control
    assert ec.objective_locked is True
    assert ec.objective_element == "Central Claim / Thesis"
    # a later turn proposes a DIFFERENT element — must NOT change the locked one
    _update_experience_control(s, InteractRequest(content="?", kind="answer"),
                               make_result(element="Evidence"), False)
    assert s.experience_control.objective_element == "Central Claim / Thesis"
    print("PASS lock_once_and_never_changes")


def test_support_cap_transitions_to_reflection():
    s = fresh_session()
    _update_experience_control(s, InteractRequest(content="seed", kind="writing"), make_result(), False)
    for i in range(3):
        assert s.experience_control.phase == "active"
        _update_experience_control(s, InteractRequest(content="help", kind="answer"), make_result(), False)
    ec = s.experience_control
    assert ec.support_count == 3
    assert ec.phase == "reflection"
    assert ec.resolved is False
    r = ec.reflection
    assert r.completion_reason == "support_cap"
    # must NOT falsely claim mastery / change
    how = r.how_your_writing_changed.lower()
    assert not any(w in how for w in ("strengthened", "sharpened", "mastered", "improved", "made your"))
    # must clearly signal the passage was not yet revised
    assert any(m in how for m in ("haven't revised", "still as you first wrote", "revising it"))
    # all four sections present
    assert r.objective and r.how_your_writing_changed and r.why_it_helps_your_reader and r.carry_it_forward
    print("PASS support_cap_transitions_to_reflection")


def test_unresolved_revision_stays_active():
    s = fresh_session()
    _update_experience_control(s, InteractRequest(content="seed", kind="writing"), make_result(), False)
    _update_experience_control(s, InteractRequest(content="draft2", kind="revise"),
                               make_result(development_detected="no", cycle_status="continue"), True)
    ec = s.experience_control
    assert ec.phase == "active"
    assert ec.revision_count == 1
    assert ec.support_count == 0
    print("PASS unresolved_revision_stays_active")


def test_resolved_revision_transitions_to_reflection_yes():
    s = fresh_session()
    _update_experience_control(s, InteractRequest(content="seed", kind="writing"), make_result(), False)
    _update_experience_control(s, InteractRequest(content="draft2", kind="revise"),
                               make_result(development_detected="yes, clearer claim",
                                           cycle_status="continue"), True)
    ec = s.experience_control
    assert ec.phase == "reflection"
    assert ec.resolved is True
    assert ec.reflection.completion_reason == "resolved"
    print("PASS resolved_revision_transitions_to_reflection (development_detected=yes)")


def test_resolved_revision_via_cycle_status():
    for cs in ("consolidate_and_return", "stop"):
        s = fresh_session()
        _update_experience_control(s, InteractRequest(content="seed", kind="writing"), make_result(), False)
        _update_experience_control(s, InteractRequest(content="draft2", kind="revise"),
                                   make_result(development_detected="partial", cycle_status=cs), True)
        assert s.experience_control.phase == "reflection", cs
        assert s.experience_control.resolved is True, cs
    print("PASS resolved_revision_via_cycle_status (consolidate_and_return / stop)")


def test_support_counter_resets_on_revision():
    s = fresh_session()
    _update_experience_control(s, InteractRequest(content="seed", kind="writing"), make_result(), False)
    _update_experience_control(s, InteractRequest(content="?", kind="answer"), make_result(), False)
    _update_experience_control(s, InteractRequest(content="?", kind="explain"), make_result(), False)
    assert s.experience_control.support_count == 2
    _update_experience_control(s, InteractRequest(content="draft2", kind="revise"),
                               make_result(development_detected="no", cycle_status="continue"), True)
    assert s.experience_control.support_count == 0
    assert s.experience_control.phase == "active"
    print("PASS support_counter_resets_on_revision")


if __name__ == "__main__":
    test_non_preview_untouched()
    test_lock_once_and_never_changes()
    test_support_cap_transitions_to_reflection()
    test_unresolved_revision_stays_active()
    test_resolved_revision_transitions_to_reflection_yes()
    test_resolved_revision_via_cycle_status()
    test_support_counter_resets_on_revision()
    print("\nALL EXPERIENCE-CONTROL UNIT TESTS PASSED")
