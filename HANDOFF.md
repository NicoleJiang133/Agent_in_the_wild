# Lens — Build Plan & Session Handoff

**Last updated:** June 24, 2026
**Active branch:** `claude/youthful-sagan-fbluj3`
**Latest commit:** `<pending>` (Director shape test + friendly missing-key errors)

This doc is the single source of truth for project state. Read it first whenever resuming, on web or local laptop.

---

## Workflow split

The project has two natural surfaces, and they get worked on in different places:

| Surface | Where | When | What |
| --- | --- | --- | --- |
| **Software & infra** | Claude Code on the web | Daytime | Agents, prompts, manifest schema, memory, scheduler, tests, refactors. All of this is text in / text or JSON out via hosted APIs (Anthropic, Gemini) — no camera or audio needed. |
| **I/O validation** | Local laptop (VS Code) | Evenings | Run `01_core_loop.ipynb` end-to-end against a real webcam, real Moondream weights, real TTS. Catch anything that only breaks with actual hardware in the loop. |
| **Pi integration** | Pi 5 + peripherals | Later in the build | Swap to `picamera2` and NeuTTS, wire MAX98357 amplifier, OLED status display, cue device. |

The web and laptop streams run in parallel. The laptop doesn't block the web (we build against the directive contract, not a live camera), and the web doesn't block the laptop (the notebook only depends on what's already merged on `main`).

---

## Resuming on your laptop — sync checklist

When you open the project in VS Code at home, do this in order:

```bash
git fetch origin
git checkout claude/youthful-sagan-fbluj3
git pull
```

Then verify your local env still works:

1. `.env` exists at repo root with `ANTHROPIC_API_KEY=...` and `GOOGLE_API_KEY=...`. The `.env` file is gitignored on purpose — you create it once per device.
2. `pip install -r lens/requirements.txt` inside your venv (re-run if `requirements.txt` changed in the latest pull — check `git log -- lens/requirements.txt`).
3. **Run the shape tests first — fastest signal that the Day-2 agents work:** `pytest tests/ -v` from the repo root. Three tests, each one real API call, ~10 seconds total. Green here means all three Day-2 agents respect their JSON contract. If any are red, fix before touching the notebook.
4. Read the **Current state** section below to see what's new since you last looked.
5. Pick a task from the **Evening I/O queue** to run on the laptop. These are the things only the laptop can do.

When you finish an evening task, push any code changes (if any) and update this doc with what you confirmed working.

---

## Current state

### Built & merged
- Day 1 scaffold (commit `1edb2c3`): `camera.py`, `tts.py`, `memory.py`, `manifest.py`, `agents/environment_monitor.py`, `agents/director.py`, `notebooks/01_core_loop.ipynb`, `requirements.txt`, `.env.example`.
- Project `README.md` (commit `0572091`).
- `agents/context_ingestor.py` + `tests/fixtures/sample_brief.txt` (commit `52fbbfb`) — Haiku turns a brief into a `CoverageManifest` matching `STUB_MANIFEST`'s shape.

### Validated end-to-end on hardware
- Nothing yet on this device. Day 1 was scaffolded last night but never run through to a spoken directive on the new laptop. **First evening task.**

### Stubbed / placeholders
- `manifest.STUB_MANIFEST` — hardcoded test manifest. Real manifests will come from the Context Ingestor.
- TTS falls back to `print()` if both NeuTTS and pyttsx3 are missing.

---

## Build queue

### Web sessions (Claude Code, no hardware required)

In suggested order — each is independently shippable:

- [x] **`agents/context_ingestor.py`** — shipped in `52fbbfb`. Public surface: `ingest_brief(brief_text: str) -> dict`. Fixture: `tests/fixtures/sample_brief.txt`. **Untested live** — needs a laptop run with `ANTHROPIC_API_KEY` set to confirm the JSON parses end-to-end against `STUB_MANIFEST`'s shape.
- [x] **`agents/footage_analyzer.py`** — shipped. Public surface: `analyze_frame(image: PIL.Image, manifest: dict) -> dict`. Uses `gemini-2.5-flash`. The agent is stateless — the caller (notebook / scheduler) is responsible for taking a non-null `satisfies` value and calling `CoverageMemory.add_capture(label)`. **Untested live** — needs a laptop run with `GOOGLE_API_KEY` set.
- [x] **`agents/adaptive_scheduler.py`** — shipped. Public surface: `reschedule(manifest, captured, elapsed_seconds, event_duration_seconds) -> dict`. Uses `gemini-2.5-flash`. Returns a schedule-update `{event_phase, priority_order, urgency_notes, drop}`. **Stateless** — the multi-agent notebook is the right place to actually re-order the manifest and persist to `data/coverage_manifest.json`. **Untested live.**
- [ ] **`notebooks/03_multi_agent.ipynb`** — wires all five agents together using fixtures (sample brief, sample frames) so the full flow can be exercised without a camera.
- [x] **Tests:** shape checks for **all four LLM agents** (Context Ingestor, Director, Footage Analyzer, Adaptive Scheduler). Each makes one real API call. Skip cleanly when keys are missing.
- [x] **Friendly missing-key errors.** `lens._env.require()` replaces `os.environ[KEY]` everywhere; misconfiguration now raises a clear `RuntimeError` pointing at `.env` instead of `KeyError`.
- [ ] **Hardening:** graceful failure when API keys are missing (right now `director.py` raises `KeyError` on first call); structured logging instead of `print()`.

### Evening I/O queue (laptop only)

- [ ] **Day-1 exit criterion:** run `lens/notebooks/01_core_loop.ipynb` cells 1 → 3 → 5 → 7 → 9 and confirm a spoken directive. First run downloads Moondream (~1.2GB) — do it on Wi-Fi. Done = you hear the directive.
- [ ] Confirm the continuous loop (cell 11) actually behaves: scene-change gate triggers, 90s cooldown is respected, no runaway TTS.
- [ ] **Smoke-test Context Ingestor.** Quick snippet:
  ```python
  from lens.agents.context_ingestor import ingest_brief
  brief = open("tests/fixtures/sample_brief.txt").read()
  manifest = ingest_brief(brief)
  import json; print(json.dumps(manifest, indent=2))
  ```
  Confirm the dict has keys `event_name`, `themes`, `desired_output`, `key_moments`, `required_shots`, `preferred_shots` — same shape as `STUB_MANIFEST`. Then try a real brief of your own.
- [ ] **Smoke-test Footage Analyzer.** Capture a frame, run it against your manifest, eyeball the label:
  ```python
  from lens.camera import capture_frame
  from lens.agents.footage_analyzer import analyze_frame
  from lens.manifest import STUB_MANIFEST   # or the real one from above
  frame = capture_frame()
  print(analyze_frame(frame, STUB_MANIFEST))
  ```
  Then point the camera at something that *should* match a required shot and confirm `satisfies` and `category` come back correctly.
- [ ] **Smoke-test Adaptive Scheduler.** Pure text, no camera needed:
  ```python
  from lens.agents.adaptive_scheduler import reschedule
  from lens.manifest import STUB_MANIFEST
  print(reschedule(STUB_MANIFEST, captured=["sponsor_logo"], elapsed_seconds=4800, event_duration_seconds=7200))
  ```
  Confirm `priority_order` only contains uncaptured labels and `event_phase` reflects ~66% elapsed (should land on `closing` or `mid` depending on the model's read).
- [ ] Once `03_multi_agent.ipynb` lands: walk through the multi-agent loop on the laptop with the real camera.

### Pi sessions (later)

- [ ] Flash Pi OS, install Moondream + NeuTTS on Pi.
- [ ] Switch `USE_PI_CAMERA=1`, confirm `picamera2` path.
- [ ] Wire MAX98357 I²S amplifier (Pi 5 has no 3.5mm jack).
- [ ] OLED display via `luma.oled` for status (current gap count, last directive, etc.).
- [ ] Cue device wiring (TBD form factor).

---

## Architecture & decisions (stable — don't relitigate)

- **Five agents:** Context Ingestor (Haiku, once) → Environment Monitor (Moondream 0.5B, free, every ~10s) → Director (Haiku + caching, gated on scene change) → Footage Analyzer (Gemini Flash, free tier) → Adaptive Scheduler (Gemini Flash). Steady-state cost target: <$0.50 per event-day.
- **Moondream 0.5B, not 2B.** 2B is ~20–25s/frame on Pi 5 CPU; 0.5B is ~8–10s, which is what makes the 10-second loop feasible.
- **Director gated by `scene_changed()`** — word-overlap similarity in `environment_monitor.py`. Suppresses ~70% of planner calls.
- **Prompt caching on Director** — system prompt + manifest both marked `cache_control: ephemeral`. Steady-state Director calls reuse the cache.
- **Single JSON-file memory** (`data/coverage_memory.json`). Cheap to inspect, cheap to reset.
- **Strict JSON contract from Director** (`directive`, `type`, `severity`, `speak`, `reason`). Everything downstream depends on this shape; preserve it as agents are added.
- **NeuTTS for on-device speech** on the Pi; pyttsx3 fallback on laptops; `print()` fallback in CI / headless containers.

---

## Files to look at first when resuming

- This file.
- `README.md` — the public-facing project description.
- `lens/agents/director.py` — the planner contract.
- `lens/memory.py` — the state everything else reads and writes.
- `lens/notebooks/01_core_loop.ipynb` — the demo loop.

---

## Notes for future-you

- Don't recreate work that already shipped. Check `git log --oneline` since you last looked.
- The `.env` file is per-device and gitignored. If a fresh clone seems "broken," 90% of the time it's a missing `ANTHROPIC_API_KEY`.
- Moondream weights re-download per machine (~1.2GB) — they're gitignored. Always do the first run on Wi-Fi.
- If you change the Director's JSON output shape, also update `CoverageMemory`, `tts.py`'s `speak` call site, and the multi-agent notebook in the same commit. That contract is load-bearing.
