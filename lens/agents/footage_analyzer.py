"""Agent 4: Footage Analyzer — Gemini Flash labels a captured clip against the manifest."""
import json
import re

import google.generativeai as genai
from PIL import Image

from lens._env import require

_model = None
_configured = False

PROMPT_TEMPLATE = """You are Lens's Footage Analyzer. You receive a representative frame from a clip
the operator just captured, plus the event's CoverageManifest. Decide whether this
frame satisfies any of the required_shots or preferred_shots in the manifest.

Output ONLY a valid JSON object — no markdown, no commentary:
{{
  "satisfies": "<exact snake_case label from required_shots or preferred_shots, or null>",
  "category": "required | preferred | none",
  "confidence": "low | medium | high",
  "reason": "<one short sentence>"
}}

Rules:
- "satisfies" must EXACTLY match a label in required_shots or preferred_shots, or be null.
- "category" is "required" if the label is in required_shots, "preferred" if in preferred_shots, "none" if null.
- "confidence" is "high" only when the frame clearly and squarely depicts what the label asks for.
- If the frame is blurry, ambiguous, or the subject is incidental, prefer "low" confidence or null.
- Pick at most one label. Pick the most specific match if multiple plausibly apply.

CoverageManifest:
{manifest}
"""


def _ensure_model() -> None:
    global _model, _configured
    if not _configured:
        genai.configure(api_key=require("GOOGLE_API_KEY"))
        _configured = True
    if _model is None:
        _model = genai.GenerativeModel("gemini-2.5-flash")


def analyze_frame(image: Image.Image, manifest: dict) -> dict:
    """Decide which manifest shot (if any) the frame satisfies."""
    _ensure_model()
    prompt = PROMPT_TEMPLATE.format(manifest=json.dumps(manifest, indent=2))
    response = _model.generate_content([prompt, image])
    raw = response.text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise ValueError(f"Footage Analyzer returned invalid JSON: {raw[:200]}")
