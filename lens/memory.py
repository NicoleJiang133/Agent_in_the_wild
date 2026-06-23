"""CoverageMemory — tracks what's been captured vs. what's still needed."""
import json
import time
from pathlib import Path
from typing import Optional


class CoverageMemory:
    def __init__(self, path: str = "data/coverage_memory.json"):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return {
            "captured": [],
            "gaps": [],
            "clips_analyzed": 0,
            "last_directive": "",
            "last_directive_ts": 0,
            "current_scene": "",
            "event_status": "on_schedule",
            "scene_history": [],
        }

    def save(self) -> None:
        self._path.write_text(json.dumps(self._state, indent=2))

    def update_scene(self, scene: str) -> None:
        self._state["current_scene"] = scene
        self._state["scene_history"].append({"ts": time.time(), "scene": scene})
        if len(self._state["scene_history"]) > 20:
            self._state["scene_history"] = self._state["scene_history"][-20:]
        self.save()

    def add_capture(self, label: str) -> None:
        if label not in self._state["captured"]:
            self._state["captured"].append(label)
        if label in self._state["gaps"]:
            self._state["gaps"].remove(label)
        self.save()

    def set_gaps(self, gaps: list[str]) -> None:
        self._state["gaps"] = gaps
        self.save()

    def record_directive(self, directive: str) -> None:
        self._state["last_directive"] = directive
        self._state["last_directive_ts"] = time.time()
        self.save()

    def seconds_since_last_directive(self) -> float:
        return time.time() - self._state["last_directive_ts"]

    def get_gaps(self) -> list[str]:
        return self._state["gaps"]

    def summary(self) -> str:
        caps = len(self._state["captured"])
        gaps = self._state["gaps"][:5]
        scene = self._state["current_scene"]
        last = self._state["last_directive"]
        return (
            f"Captured {caps} shots. "
            f"Urgent gaps: {gaps if gaps else 'none'}. "
            f"Current scene: {scene or 'unknown'}. "
            f"Last directive: '{last}'"
        )

    @property
    def state(self) -> dict:
        return self._state
