"""Agent 1: Context Ingestor — Claude Haiku turns an event brief into a CoverageManifest."""
import json
import re
from typing import Optional

import anthropic

from lens._env import require

_client: Optional[anthropic.Anthropic] = None

SYSTEM_PROMPT = """You are Lens's Context Ingestor. You read a free-form event brief from a creator
and turn it into a structured CoverageManifest that the rest of Lens uses to direct coverage.

Output ONLY a valid JSON object matching this exact schema — no markdown, no commentary:
{
  "event_name": "<string>",
  "themes": ["<theme>", ...],
  "desired_output": "<one-sentence description of the deliverable>",
  "key_moments": [
    {
      "time": "<when, e.g. 'opening', '19:00', 'now'>",
      "label": "<short name>",
      "priority": "high | medium | low",
      "shot_types": ["<shot type>", ...]
    }
  ],
  "required_shots": ["<snake_case label>", ...],
  "preferred_shots": ["<snake_case label>", ...]
}

Rules:
- "required_shots" are non-negotiable for the deliverable — if missing, the deliverable fails.
- "preferred_shots" add polish but aren't critical.
- Use snake_case labels for shots: "sponsor_logo", "crowd_reaction", "speaker_wide", "candid_audience".
- 3-7 themes, 3-8 required_shots, 3-10 preferred_shots, 2-6 key_moments.
- Infer reasonable defaults if the brief is sparse — commit, don't ask for clarification.
- If the brief is empty or nonsensical, return event_name "Unknown" with empty arrays."""


def ingest_brief(brief_text: str) -> dict:
    """Turn a free-form event brief into a CoverageManifest dict."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=require("ANTHROPIC_API_KEY"))

    response = _client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[{"role": "user", "content": f"Event brief:\n{brief_text}"}],
    )

    raw = response.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise ValueError(f"Context Ingestor returned invalid JSON: {raw[:200]}")
