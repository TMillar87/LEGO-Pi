# LEGO Pi — Clean Stack

**LEGO Pi** is a voice- and vision-controlled assistant ("Jarvis") that runs on a Raspberry
Pi. It watches your LEGO bricks through a camera, identifies them, tells you which storage
bin they live in, adds new pieces to inventory, and helps you track progress rebuilding
owned sets — all hands-free, triggered by the wake word **"Hey Jarvis"**.

This is the rebuilt runtime stack (2026-08-29). It intentionally preserves the proven
hardware path and HTTP routes of the original prototype while moving all runtime logic
into one importable `runtime/` package with a single source of truth for paths and
settings (`runtime/config.py`).

## Key features

- **Voice control** — wake word detection ("Hey Jarvis") followed by a bounded 6-second
  command capture with early silence stop, so the assistant doesn't sit there listening.
- **Fast local intent routing** — common commands (scan, lookup, add, demo mode, volume,
  rebuild, "what can you do") are matched and executed immediately by a local rule router,
  with no model inference or added latency. Only genuinely ambiguous phrasing falls back to
  a local LLM.
- **Brick identification** — a live camera feed is sent to [Brickognize](https://brickognize.com/)
  for part recognition, combined with an HSV-calibrated color classifier to identify both
  the part number and color.
- **General camera vision** — free-form "what do you see" questions are answered by OpenAI's
  vision model against the live camera frame.
- **Inventory tracking** — look up where a scanned brick is stored, or add it to inventory
  (existing part, new color, or brand-new part), with locations drawn from a 960-bin
  location table and every change recorded to history.
- **Set rebuild assistant** — start a rebuild session for an owned set and check active
  rebuild status, backed by a Rebrickable parts/sets catalog.
- **Demo Mode** — a fully isolated sandbox (separate inventory and catalog databases) so you
  can demo scanning, lookup, and add flows without ever touching your real inventory.
  Toggle on/off/status/reset by voice.
- **Voice replies** — spoken responses via ElevenLabs text-to-speech.
- **Voice volume control** — "volume three" / "volume up" / "volume down" mapped to ALSA
  playback levels.
- **Live web view** — an MJPEG camera stream and health/mode endpoints exposed over HTTP,
  plus debug endpoints for tuning color detection (`/color-test`, `/color-test-frame`,
  `/color-sample`, `/camera-metadata`).
- **Physical reboot button** — hold a GPIO button for 2 seconds to reboot the Pi.

## How it works

```text
"Hey Jarvis"
   |
   v
openWakeWord (local wake-word detection)
   |
   v
6-second max command capture, stops early on silence
   |
   v
OpenAI gpt-4o-mini-transcribe (speech-to-text)
   |
   v
Fast local rule router
   |------------------------------|
   | known command                | ambiguous command
   v                               v
immediate action              local Qwen 1.5B via Ollama (bounded fallback)
                                   |
                                   v
                              JSON action (fixed action list only)
   |
   +--> /scan ------------------> Brickognize --> color classifier --> spoken result
   +--> /inventory -------------> Brickognize --> color --> selected inventory DB
   +--> /inventory/add ---------> Brickognize --> color --> selected inventory DB
   +--> /vision ----------------> OpenAI vision --> spoken result
   +--> rebuild ----------------> selected Rebrickable catalog DB
   +--> demo -------------------> atomic Normal/Demo mode switch
   +--> volume -----------------> local ALSA control (legopi-volume)
```

The LLM fallback can only ever select from a fixed set of actions — it never executes
arbitrary commands or shell code. See `docs/ARCHITECTURE.md` for the full design and
`docs/COMMANDS.md` for the voice command reference.

## Hardware

| Component | Role |
|---|---|
| Raspberry Pi (running Raspberry Pi OS, Python 3.13) | Runs both services and the wake-word/voice loop |
| Raspberry Pi Camera Module (via `picamera2`) | Live video feed for brick scanning and general vision, with autofocus and manual white balance calibration |
| Microphone (USB or I2S, ALSA-addressable) | Captures the wake word and voice commands |
| I2S DAC / speaker (e.g. PCM5102A or HifiBerry) | Plays TTS responses through ALSA (`legopi-volume`) |
| Physical push button on GPIO 17 | Hold 2 seconds to trigger a full system reboot (`reboot-button.py`, via `gpiozero`/`lgpio`) |

## Software stack

- **Wake word:** [openWakeWord](https://github.com/dscripka/openWakeWord) (`hey_jarvis` ONNX model)
- **Speech-to-text:** OpenAI `gpt-4o-mini-transcribe`
- **General vision:** OpenAI vision (Responses API)
- **Brick recognition:** [Brickognize](https://brickognize.com/) API
- **Text-to-speech:** [ElevenLabs](https://elevenlabs.io/)
- **Local NLU fallback:** [Ollama](https://ollama.com/) running `qwen2.5:1.5b` (bounded timeout, never blocks common commands)
- **Web/camera server:** Flask + OpenCV + Picamera2
- **Storage:** SQLite (inventory, rebuild/catalog databases), managed under `runtime/`
- **Catalog data:** [Rebrickable](https://rebrickable.com/) bulk CSV export (`data/rebrickable/`)
- **Process management:** systemd units under `systemd/`

## Configuration requirements

### Secrets (never committed)

Two private, `chmod 600` environment files are expected on the Pi and loaded at process
start:

- `/home/ty/.config/legopi/openai.env` — must set `OPENAI_API_KEY`
- `/home/ty/.config/legopi/elevenlabs.env` — must set `ELEVENLABS_API_KEY`, and may set
  `ELEVENLABS_VOICE_ID` / `ELEVENLABS_MODEL`

Neither file, nor any other API key/password/token, is present in this repository. See
`SECURITY.md`.

### Runtime environment variables

All other settings are centralized in `runtime/config.py` and overridable via environment
variables (see `config/runtime.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `LEGOPI_HOME` | `/home/ty` | Base directory for the deployed stack and secrets |
| `LEGOPI_REAL_INVENTORY_DB` | `$LEGOPI_HOME/legopi-data/lego_inventory.db` | Live/physical inventory database |
| `LEGOPI_DEMO_INVENTORY_DB` | `demo/demo_inventory.db` | Demo-mode inventory database |
| `LEGOPI_REAL_CATALOG_DB` | `data/db/legopi.sqlite3` | Live rebuild/catalog database |
| `LEGOPI_DEMO_CATALOG_DB` | `demo/legopi_demo.sqlite3` | Demo-mode rebuild/catalog database |
| `LEGOPI_OLLAMA_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint |
| `LEGOPI_OLLAMA_MODEL` | `qwen2.5:1.5b` | Local fallback NLU model |
| `LEGOPI_OLLAMA_TIMEOUT` | `3.0` | Seconds before the fallback gives up (never applies to fast-routed commands) |
| `LEGOPI_LIVE_HOST` / `LEGOPI_LIVE_PORT` | `0.0.0.0` / `5000` | Flask camera/vision server bind address |
| `LEGOPI_CAMERA_WIDTH` / `HEIGHT` / `FPS` | `1280` / `720` / `20` | Camera capture configuration |
| `LEGOPI_CAMERA_ROTATE` | `none` | Corrects the live feed/scan/vision frames for a physically rotated camera mount. One of `none`, `90_cw`, `90_ccw`, `180` |
| `LEGOPI_WAKE_THRESHOLD` | `0.80` | openWakeWord confidence threshold |
| `LEGOPI_WAKE_MODEL` | bundled `hey_jarvis_v0.1.onnx` path | Wake-word model path |
| `LEGOPI_AUDIO_DEVICE` | `0` | ALSA input device index/name for the microphone |
| `LEGOPI_VOLUME_COMMAND` | `/usr/local/bin/legopi-volume` | Volume control executable |

Database selection (real vs. demo) is resolved dynamically per request, so Demo Mode fully
isolates both inventory writes and rebuild-session writes from the real data.

### Services

Four systemd units (installed from `systemd/`) run the stack:

- `legopi-jarvis.service` — the voice loop (`jarvis-full.py`)
- `legopi-live.service` — the Flask camera/vision server (`legopi-live-server-final.py`), required by `legopi-jarvis.service`
- `legopi-ollama-warm.service` — keeps the local Qwen model warm after boot
- `legopi-reboot-button.service` — the physical reboot button listener

## Repository layout

See `docs/FILE_MAP.md` for the full breakdown. Highlights:

- `runtime/` — all runtime logic (config, intent routing, dispatch, voice, live server,
  inventory, rebuild, mode/demo selection, TTS, volume)
- `jarvis-full.py`, `jarvis-intent-router.py`, `legopi-live-server-final.py`,
  `elevenlabs-speak-final.py`, `reboot-button.py` — thin compatibility launchers that import
  from `runtime/`
- `demo/` — demo database seed/reset and isolated demo databases
- `data/rebrickable/` — Rebrickable catalog CSVs (gitignored except the README)
- `bin/` — `legopi-volume` (ALSA control) and `legopi-ollama-warm` (Qwen warm-up)
- `systemd/` — service unit files
- `scripts/install_runtime.sh` — automated Pi deployment with rollback backup
- `docs/` — architecture, deployment, and command reference documentation
- `tests/` — offline unit/syntax/route/isolation tests (standard library only)

## Getting started

1. Provision a Raspberry Pi with a camera module, microphone, and I2S DAC/speaker, wired as
   described in [Hardware](#hardware).
2. Follow `docs/DEPLOYMENT.md` for the full, verified update procedure (backup, install,
   secret placement, verification steps, rollback).
3. Create the two private secret files under `~/.config/legopi/` with your OpenAI and
   ElevenLabs API keys (see [Configuration requirements](#configuration-requirements)).
4. Populate the Rebrickable catalog with `legopi sync-catalog` (and optionally
   `legopi import-owned-sets <csv>` for your owned sets) — see `data/rebrickable/README.md`.
5. Enable and start the systemd services, then verify with the checklist in
   `docs/DEPLOYMENT.md`.

## Testing

The tests themselves only touch the Python standard library (no Flask/OpenCV/camera
dependencies needed), but they're written in pytest style, so run them with `pytest`:

```bash
pip install pytest
python3 -m pytest tests/
```

`test_demo_isolation.py` checks that resetting Demo Mode never touches the real inventory
database, so it expects to find `LEGOPI_REAL_INVENTORY_DB` on disk — it's meant to run on a
deployed Pi and will fail with `FileNotFoundError` in a bare checkout without that file.

## Documentation

- `docs/ARCHITECTURE.md` — runtime architecture, intent routing, database isolation
- `docs/DEPLOYMENT.md` — step-by-step Raspberry Pi deployment and rollback
- `docs/COMMANDS.md` — full voice command reference
- `docs/FILE_MAP.md` — file-by-file breakdown of the stack
- `SECURITY.md` — secrets handling
- `GITHUB.md` — what is/isn't included in this public source distribution
