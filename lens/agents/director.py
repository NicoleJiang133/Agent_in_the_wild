"""Agent 3: Director — Claude Haiku 4.5 with prompt caching for coverage directives."""
import json
from typing import Optional

import anthropic

from lens._env import require

_client: Optional[anthropic.Anthropic] = None

SYSTEM_PROMPT = """You are Lens, an AI event coverage director. Your job is to guide a human
cameraperson to capture the right shots at the right time during a live event.

You receive:
- The event's CoverageManifest (what shots are required/preferred)
- The current scene description (what the Pi camera sees in the room)
- The coverage memory (what has been captured, what gaps remain)

You must output ONLY valid JSON — no markdown, no commentary:
{
  "directive": "<short imperative, max 12 words, natural spoken English>",
  "type": "coverage | environment | moment | none",
  "severity": "info | nudge | urgent",
  "speak": true,
  "reason": "<one sentence why>"
}

Rules:
- "none" + speak:false when nothing needs saying. Don't over-direct.
- "urgent" only for once-in-event moments (keynote opening, award announcement).
- "nudge" for missing required shots. "info" for preferred shots.
- Directives should be actionable and specific ("Head to the sponsor wall" not "get more shots").
- Never repeat the last directive verbatim."""


def get_directive(
    manifest: dict,
    scene: str,
    memory_summary: str,
    last_directive: str = "",
) -> dict:
    """
    Call Claude Haiku with cached system prompt + manifest.
    Returns parsed directive dict.
    """
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=require("ANTHROPIC_API_KEY"))

    manifest_text = json.dumps(manifest, indent=2)

    user_content = (
        f"Current scene (Pi camera): {scene}\n\n"
        f"Coverage memory: {memory_summary}\n\n"
        f"Last directive given: {last_directive or 'none yet'}\n\n"
        "Issue the next directive as JSON."
    )

    response = _client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": f"CoverageManifest:\n{manifest_text}",
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Extract JSON from response if wrapped in markdown
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {"directive": "", "type": "none", "severity": "info", "speak": False, "reason": "parse error"}
