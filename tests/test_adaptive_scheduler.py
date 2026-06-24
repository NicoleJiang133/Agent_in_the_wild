"""Live shape test for the Adaptive Scheduler — costs ~1 Gemini Flash call."""
import os

import pytest

skip_no_key = pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set — skipping live API test",
)


@skip_no_key
def test_reschedule_returns_expected_shape():
    from lens.agents.adaptive_scheduler import reschedule
    from lens.manifest import STUB_MANIFEST

    captured = ["sponsor_logo"]
    result = reschedule(
        STUB_MANIFEST,
        captured=captured,
        elapsed_seconds=4800,
        event_duration_seconds=7200,
    )

    expected_keys = {"event_phase", "priority_order", "urgency_notes", "drop"}
    missing = expected_keys - set(result.keys())
    assert not missing, f"result missing keys: {missing}"

    assert result["event_phase"] in {"opening", "mid", "closing", "wrap_up"}
    assert isinstance(result["priority_order"], list)
    assert isinstance(result["drop"], list)
    assert isinstance(result["urgency_notes"], str)

    all_labels = set(STUB_MANIFEST["required_shots"]) | set(
        STUB_MANIFEST["preferred_shots"]
    )
    captured_set = set(captured)
    for label in result["priority_order"]:
        assert label in all_labels, f"unknown label in priority_order: {label!r}"
        assert label not in captured_set, (
            f"already-captured label appeared in priority_order: {label!r}"
        )
    for label in result["drop"]:
        assert label in all_labels, f"unknown label in drop: {label!r}"
