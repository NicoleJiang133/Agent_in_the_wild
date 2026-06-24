"""Live shape test for the Footage Analyzer — costs ~1 Gemini Flash call."""
import os

import pytest
from PIL import Image

skip_no_key = pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set — skipping live API test",
)


@skip_no_key
def test_analyze_frame_returns_expected_shape():
    from lens.agents.footage_analyzer import analyze_frame
    from lens.manifest import STUB_MANIFEST

    # A grey frame won't match any real shot — we're only testing that the
    # contract is respected (keys present, categorical values valid). A null
    # `satisfies` with category "none" is a perfectly correct response here.
    frame = Image.new("RGB", (320, 240), color=(128, 128, 128))
    result = analyze_frame(frame, STUB_MANIFEST)

    expected_keys = {"satisfies", "category", "confidence", "reason"}
    missing = expected_keys - set(result.keys())
    assert not missing, f"result missing keys: {missing}"

    assert result["category"] in {"required", "preferred", "none"}
    assert result["confidence"] in {"low", "medium", "high"}
    assert isinstance(result["reason"], str)

    if result["satisfies"] is not None:
        all_labels = set(STUB_MANIFEST["required_shots"]) | set(
            STUB_MANIFEST["preferred_shots"]
        )
        assert result["satisfies"] in all_labels, (
            f"`satisfies` must be from the manifest: got {result['satisfies']!r}"
        )
