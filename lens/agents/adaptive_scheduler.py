"""Agent 5: Adaptive Scheduler — Gemini Flash reprioritizes remaining gaps based on event phase."""
import json
import os
import re

import google.generativeai as genai

_model = None
_configured = False

PROMPT_TEMPLATE = """You are Lens's Adaptive Scheduler. The event is in progress. Given the
CoverageManifest, what's already been captured, and how much event time has elapsed,
decide what to push hardest in the time remaining.

Output ONLY a valid JSON object — no markdown, no commentary:
{{
  "event_phase": "opening | mid | closing | wrap_up",
  "priority_order": ["<snake_case label>", ...],
  "urgency_notes": "<one short sentence to the operator>",
  "drop": ["<snake_case label>", ...]
}}

Rules:
- "event_phase" is your read of where we are in the event arc, given elapsed % and key_moments.
- "priority_order" is the list of UNCAPTURED required_shots and preferred_shots, ordered from
  most urgent (first) to least urgent (last). Missing required_shots rank above preferred ones
  unless a preferred shot's window is about to close.
- "drop" lists labels that are no longer realistic to capture (a moment has passed, time is up).
  Use sparingly — drop only with a clear reason in your head.
- "urgency_notes" is one sentence for the operator about what matters most right now.

CoverageManifest:
{manifest}

Captured so far: {captured}
Elapsed: {elapsed}s of estimated {duration}s (~{percent}% through)
"""


def _ensure_model() -> None:
    global _model, _configured
    if not _configured:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        _configured = True
    if _model is None:
        _model = genai.GenerativeModel("gemini-2.5-flash")


def reschedule(
    manifest: dict,
    captured: list[str],
    elapsed_seconds: float,
    event_duration_seconds: float,
) -> dict:
    """Re-rank remaining gaps. Returns a schedule-update dict; caller applies it."""
    _ensure_model()
    percent = round(100 * elapsed_seconds / max(event_duration_seconds, 1))
    prompt = PROMPT_TEMPLATE.format(
        manifest=json.dumps(manifest, indent=2),
        captured=captured or "(none yet)",
        elapsed=int(elapsed_seconds),
        duration=int(event_duration_seconds),
        percent=percent,
    )
    response = _model.generate_content(prompt)
    raw = response.text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise ValueError(f"Adaptive Scheduler returned invalid JSON: {raw[:200]}")
