---
## Session Handoff — Lens Hackathon (Agents in the Wild) — June 23, 2026

**Project:** Lens — multi-agent event coverage assistant on Raspberry Pi
**Repo:** /Users/Nicole/Agent_in_the_wild/ (branch: main)
**Goal:** 5-agent system where a Pi + camera watches an event room and directs a human cameraperson via voice toward missing shots, guided by an uploaded event brief.

### Completed this session
- All Day 1 files scaffolded under `lens/`:
  - `camera.py` — webcam (laptop) / picamera2 (Pi) auto-switch via `USE_PI_CAMERA=1`
  - `tts.py` — NeuTTS → pyttsx3 → print fallback chain
  - `memory.py` — CoverageMemory (tracks captured shots, gaps, last directive, 90s cooldown)
  - `manifest.py` — CoverageManifest loader + STUB_MANIFEST for testing
  - `agents/environment_monitor.py` — Moondream 0.5B scene description (~8-10s/frame on Pi)
  - `agents/director.py` — Claude Haiku 4.5 with prompt caching (system prompt + manifest cached)
  - `notebooks/01_core_loop.ipynb` — Day 1 notebook: webcam → Moondream → Claude Haiku → TTS
  - `requirements.txt`, `.env.example`
- Fixed `.env` path resolution in notebook: cell 1 uses `find_dotenv()` so it works from any subdirectory
- `ANTHROPIC_API_KEY` goes in `.env` at repo root (not committed — create it fresh on each device)

### In progress / next steps
- [ ] **RIGHT NOW — Day 1 exit criteria:** Open `lens/notebooks/01_core_loop.ipynb` in VS Code. Run Cell 1 (confirms API key SET), Cell 3 (webcam frame), Cell 5 (Moondream downloads ~1.2GB first run — do on WiFi), Cell 7 (Claude Haiku directive), Cell 9 (speaks aloud). Done when you hear a spoken directive.
- [ ] Install deps if not already done: `pip install -r lens/requirements.txt`
- [ ] Get free Gemini API key at https://aistudio.google.com — add as `GOOGLE_API_KEY` in `.env` (needed Day 2)
- [ ] Day 2 (June 24): Build `agents/context_ingestor.py` (Haiku → CoverageManifest from event brief text), `agents/footage_analyzer.py` (Gemini Flash), `agents/adaptive_scheduler.py` (Gemini Flash), wire in `notebooks/03_multi_agent.ipynb`
- [ ] Day 3 (June 25): Flash Pi OS, install Moondream + NeuTTS on Pi, swap camera to picamera2, wire MAX98357 amplifier
- [ ] Day 4 (June 26): OLED display (`luma.oled`), tuning, graceful error handling
- [ ] Day 5 (June 27–28): Demo video + submission

### Key context & decisions
- **Pi camera is STATIONARY in room** — not worn. Watches the whole event. Human carries their own camera and gets directed via voice earpiece.
- **5 agents:** Context Ingestor (Haiku, once at start) → Environment Monitor (Moondream 0.5B, free, every ~10s) → Director (Haiku + caching) → Footage Analyzer (Gemini Flash, free) → Adaptive Scheduler (Gemini Flash, free). Total cost: <$0.50/event day.
- **Moondream 0.5B not 2B** — 0.5B runs in ~8-10s on Pi CPU. 2B takes 20–25s (too slow).
- **Smart scene diff before calling Director** — `scene_changed()` in `environment_monitor.py` does word-overlap similarity; only calls Claude when scene meaningfully changed (~70% cost reduction).
- **NeuTTS (Neuphonic)** — open-source, on-device, no API key. Qualifies for £250 Neuphonic Voice prize.
- **Prize targets:** Neuphonic Voice £250, Raspberry Pi 2×Pi500, Lightbringer Creative £250, Overall £1,000.
- **Hardware to collect from event hosts:** OLED display, MAX98357 I2S amplifier (Pi 5 has no 3.5mm jack), breadboard, jumper wires. Confirm Pi is Pi 5 4GB.
- **Moondream re-downloads on each new machine** (~1.2GB, model weights are gitignored) — run Cell 5 on WiFi.
- **Full 5-day plan** at `/Users/Nicole/.claude/plans/you-are-the-best-fizzy-flamingo.md` (local only, not in repo)

### Files to look at first
- `lens/notebooks/01_core_loop.ipynb` — run this first to validate Day 1 end-to-end
- `lens/agents/director.py` — core Claude Haiku call with prompt caching
- `lens/agents/environment_monitor.py` — Moondream 0.5B integration + scene_changed() logic

### Start here
Create `.env` at repo root with `ANTHROPIC_API_KEY=your_key`. Open `lens/notebooks/01_core_loop.ipynb` in VS Code, confirm Cell 1 prints `ANTHROPIC_API_KEY: SET`, then run cells 3 → 5 → 7 → 9 in order. Cell 5 downloads Moondream (~1.2GB) on first run — leave it running. Day 1 is done when you hear a spoken directive from Cell 9.
---
