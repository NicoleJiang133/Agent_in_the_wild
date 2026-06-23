"""Agent 2: Environment Monitor — Moondream 0.5B scene description (free, on-device)."""
from __future__ import annotations

from PIL import Image

_model = None
_tokenizer = None


def _load_moondream():
    global _model, _tokenizer
    if _model is not None:
        return
    from transformers import AutoModelForCausalLM, AutoTokenizer
    print("Loading Moondream 0.5B (first run takes ~30s)...")
    _tokenizer = AutoTokenizer.from_pretrained(
        "vikhyatk/moondream2", revision="2025-01-09", trust_remote_code=True
    )
    _model = AutoModelForCausalLM.from_pretrained(
        "vikhyatk/moondream2", revision="2025-01-09", trust_remote_code=True
    )
    _model.eval()
    print("Moondream ready.")


def describe_scene(image: Image.Image) -> str:
    """Return a short scene description from a camera frame."""
    _load_moondream()
    enc = _model.encode_image(image)
    answer = _model.query(
        enc,
        "Describe this scene briefly: who is present, what are they doing, "
        "what is the energy level (calm / active / intense), "
        "and what location cues are visible (stage, tables, corridor, etc.).",
    )["answer"]
    return answer.strip()


def scene_changed(new_scene: str, last_scene: str, threshold: float = 0.35) -> bool:
    """
    Return True if the scene has changed enough to warrant a Director call.
    Uses simple word-overlap similarity — no extra dependencies.
    """
    def tokens(s: str) -> set[str]:
        return set(s.lower().split())

    a, b = tokens(new_scene), tokens(last_scene)
    if not a or not b:
        return True
    overlap = len(a & b) / max(len(a), len(b))
    return overlap < (1 - threshold)
