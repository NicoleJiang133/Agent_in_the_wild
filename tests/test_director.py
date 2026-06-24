"""Live shape test for the Director — costs ~1 Haiku call.

The Director's JSON contract is load-bearing: the TTS layer, the memory
layer, and the upcoming multi-agent notebook all consume this exact
shape. The Director also has a parse-error fallback, so even a totally
malformed model response should still satisfy this test — that's the
contract worth verifying.
"""
import os

import pytest

skip_no_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API test",
)


@skip_no_key
def test_get_directive_returns_expected_shape():
    from lens.agents.director import get_directive
    from lens.manifest import STUB_MANIFEST

    directive = get_directive(
        manifest=STUB_MANIFEST,
        scene=(
            "A conference room with rows of empty chairs, a podium at the "
            "front, soft ambient lighting, no people visible yet."
        ),
        memory_summary=(
            "Captured 0 shots. Urgent gaps: ['sponsor_logo', 'crowd_reaction', "
            "'speaker_wide']. Current scene: empty room. Last directive: ''"
        ),
        last_directive="",
    )

    expected_keys = {"directive", "type", "severity", "speak", "reason"}
    missing = expected_keys - set(directive.keys())
    assert not missing, f"directive missing keys: {missing}"

    assert directive["type"] in {"coverage", "environment", "moment", "none"}
    assert directive["severity"] in {"info", "nudge", "urgent"}
    assert isinstance(directive["speak"], bool)
    assert isinstance(directive["directive"], str)
    assert isinstance(directive["reason"], str)
