"""CoverageManifest — loads and validates the event coverage plan."""
import json
from pathlib import Path

STUB_MANIFEST = {
    "event_name": "Test Event",
    "themes": ["technology", "networking"],
    "desired_output": "2-minute highlight reel",
    "key_moments": [
        {"time": "now", "label": "opening remarks", "priority": "high", "shot_types": ["wide", "speaker_close"]},
        {"time": "later", "label": "networking", "priority": "medium", "shot_types": ["candid", "b_roll"]},
    ],
    "required_shots": ["sponsor_logo", "crowd_reaction", "speaker_wide"],
    "preferred_shots": ["hallway_chat", "product_demo", "people_laughing"],
}


def load_manifest(path: str = "data/coverage_manifest.json") -> dict:
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text())
    return STUB_MANIFEST


def save_manifest(manifest: dict, path: str = "data/coverage_manifest.json") -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, indent=2))
