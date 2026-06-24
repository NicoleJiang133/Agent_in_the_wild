"""Live shape test for the Context Ingestor — costs ~1 Haiku call."""
import os
from pathlib import Path

import pytest

skip_no_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API test",
)


@skip_no_key
def test_ingest_brief_returns_manifest_shape():
    from lens.agents.context_ingestor import ingest_brief

    brief = Path("tests/fixtures/sample_brief.txt").read_text()
    manifest = ingest_brief(brief)

    expected_keys = {
        "event_name",
        "themes",
        "desired_output",
        "key_moments",
        "required_shots",
        "preferred_shots",
    }
    missing = expected_keys - set(manifest.keys())
    assert not missing, f"manifest missing keys: {missing}"

    assert isinstance(manifest["event_name"], str) and manifest["event_name"]
    assert isinstance(manifest["desired_output"], str)
    assert isinstance(manifest["themes"], list)
    assert all(isinstance(t, str) for t in manifest["themes"])
    assert isinstance(manifest["required_shots"], list)
    assert all(isinstance(s, str) for s in manifest["required_shots"])
    assert isinstance(manifest["preferred_shots"], list)
    assert isinstance(manifest["key_moments"], list)

    for moment in manifest["key_moments"]:
        assert {"time", "label", "priority", "shot_types"}.issubset(moment.keys())
        assert moment["priority"] in {"high", "medium", "low"}
        assert isinstance(moment["shot_types"], list)
