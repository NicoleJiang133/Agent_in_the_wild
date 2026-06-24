# Lens

A real-time, multi-agent coverage director. Lens watches a live camera feed, reasons about what footage is still missing for a planned deliverable, and tells the operator — by voice — what to capture next.

It's designed to run on a Raspberry Pi but works on any laptop for development. The vision stack is on-device (free); only the planning calls hit hosted LLMs, and those are cached.

## What Lens does

You give it a brief — "two-minute highlight reel of a product launch, must include sponsor logos, crowd reactions, and a wide of the speaker." Lens turns that brief into a structured **CoverageManifest**, then runs a continuous loop:

1. Grab a frame from the camera.
2. Describe the scene locally with a small VLM.
3. If the scene has meaningfully changed, ask a planner: *given what's already captured and what's still missing, what should the operator do right now?*
4. Speak the directive out loud (or stay silent if nothing needs saying).
5. As clips are recorded, mark which required shots they satisfy and update the plan.

The result is a producer-in-your-ear that knows the deliverable, tracks the gaps, and only speaks when it has something useful to say.

## Architecture

Five agents, each chosen for cost and latency:

| Agent | Model | Runs | Job |
| --- | --- | --- | --- |
| Context Ingestor | Claude Haiku | Once at start | Turns an event brief into a `CoverageManifest` (themes, required/preferred shots, key moments). |
| Environment Monitor | Moondream 0.5B (on-device) | Every ~10s | Short natural-language description of the current frame. Free, no network. |
| Director | Claude Haiku + prompt caching | Only when the scene changes meaningfully | Reads the manifest, current scene, and coverage memory; emits a single directive as JSON. |
| Footage Analyzer | Gemini Flash | Per captured clip | Classifies which required shot a clip satisfies and updates `CoverageMemory`. |
| Adaptive Scheduler | Gemini Flash | Periodically | Reprioritizes remaining shots based on elapsed time and event phase. |

The manifest and the planner's system prompt are both marked as cached, so steady-state Director calls are cheap. The scene-change gate (a simple word-overlap similarity in `environment_monitor.py`) typically suppresses ~70% of Director calls.

## Repository layout

```
lens/
  camera.py                  # OpenCV webcam (dev) / picamera2 (Pi), gated by USE_PI_CAMERA
  tts.py                     # NeuTTS → pyttsx3 → print fallback chain
  memory.py                  # CoverageMemory: captured shots, gaps, scene history, cooldowns
  manifest.py                # CoverageManifest loader + STUB_MANIFEST for testing
  agents/
    environment_monitor.py   # Moondream 0.5B describe_scene() + scene_changed()
    director.py              # Claude Haiku planner with cached system + manifest
    # context_ingestor.py    (planned)
    # footage_analyzer.py    (planned)
    # adaptive_scheduler.py  (planned)
  notebooks/
    01_core_loop.ipynb       # End-to-end: camera → Moondream → Haiku → TTS
  requirements.txt
  .env.example
```

`data/coverage_memory.json` and `data/coverage_manifest.json` are created at runtime and are gitignored.

## Current status

Built:

- Core loop end-to-end on a laptop: webcam → Moondream → Director → spoken directive.
- `CoverageMemory` with persistence, scene history, and directive cooldown.
- Pi camera path (`picamera2`) and Pi TTS path (`NeuTTS`) wired behind import guards — not exercised on dev machines.
- Prompt caching on the Director call.

Not yet built:

- Context Ingestor (manifest is currently a hardcoded stub).
- Footage Analyzer (nothing closes the loop from "clip recorded" back into `CoverageMemory.add_capture`).
- Adaptive Scheduler.
- Multi-agent notebook (`03_multi_agent.ipynb`).
- Pi hardware integration: I²S amplifier, OLED status display, physical cue device.
- Tests.

## Setup

Tested on Python 3.11+. The vision model is ~1.2GB and downloads on first run, so do that step on Wi-Fi.

```bash
git clone <repo>
cd Agent_in_the_wild
python -m venv .venv && source .venv/bin/activate
pip install -r lens/requirements.txt

cp lens/.env.example .env
# edit .env and set:
#   ANTHROPIC_API_KEY=...
#   GOOGLE_API_KEY=...      (needed once Footage Analyzer / Scheduler land)
```

### Run the core loop

Open `lens/notebooks/01_core_loop.ipynb` and run the cells in order:

1. Env check — confirms API keys are loaded.
2. Capture a frame from the default webcam.
3. Describe the scene with Moondream (first run downloads weights).
4. Ask the Director for a directive.
5. Speak the directive out loud.
6. Continuous loop with the scene-change gate and a 90-second directive cooldown.

## Configuration

| Variable | Default | Effect |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | — | Required for the Director (and the Context Ingestor when it lands). |
| `GOOGLE_API_KEY` | — | Required for the Gemini-based agents. |
| `USE_PI_CAMERA` | `0` | Set to `1` to use `picamera2` instead of OpenCV. |
| `CAPTURE_INTERVAL` | `10` | Seconds between frames in the continuous loop. |
| `DIRECTIVE_COOLDOWN` | `90` | Minimum seconds between spoken directives. |

## Design notes

- **Moondream 0.5B, not 2B.** The 2B variant takes 20–25 seconds per frame on a Pi 5 CPU; the 0.5B variant runs in 8–10 seconds, which is what makes the 10-second loop feasible.
- **Director only fires on real change.** The word-overlap gate is dumb on purpose: it's robust, has no extra deps, and avoids paying for a planner call every loop iteration.
- **Strict JSON contract from the Director.** The directive schema (`directive`, `type`, `severity`, `speak`, `reason`) is what `tts.py` and the upcoming clip-capture flow both depend on; a fenced-JSON fallback in `director.py` handles the occasional markdown wrapper.
- **Memory is a single JSON file.** Cheap to inspect, cheap to reset, no DB to run. Good enough until it isn't.

## License

TBD.
