from __future__ import annotations

import os
from pathlib import Path

HOME = Path(os.getenv("LEGOPI_HOME", "/home/ty")).expanduser()
REPO = Path(__file__).resolve().parents[1]

# Runtime paths are intentionally centralized. The compatibility launchers in /home/ty
# only import from this package, so there is one source of truth for paths and settings.
REAL_INVENTORY_DB = Path(os.getenv("LEGOPI_REAL_INVENTORY_DB", HOME / "legopi-data/lego_inventory.db"))
DEMO_INVENTORY_DB = Path(os.getenv("LEGOPI_DEMO_INVENTORY_DB", REPO / "demo/demo_inventory.db"))
REAL_CATALOG_DB = Path(os.getenv("LEGOPI_REAL_CATALOG_DB", REPO / "data/db/legopi.sqlite3"))
DEMO_CATALOG_DB = Path(os.getenv("LEGOPI_DEMO_CATALOG_DB", REPO / "demo/legopi_demo.sqlite3"))
DEMO_STATE_FILE = Path(os.getenv("LEGOPI_DEMO_STATE", REPO / "demo/demo_state.json"))

OPENAI_ENV = Path(os.getenv("LEGOPI_OPENAI_ENV", HOME / ".config/legopi/openai.env"))
ELEVENLABS_ENV = Path(os.getenv("LEGOPI_ELEVENLABS_ENV", HOME / ".config/legopi/elevenlabs.env"))

VENV_PYTHON = Path(os.getenv("LEGOPI_VENV_PYTHON", HOME / "legopi-venv/bin/python"))

OLLAMA_URL = os.getenv("LEGOPI_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("LEGOPI_OLLAMA_MODEL", "qwen2.5:1.5b")
# Common commands never wait on Ollama. This timeout only applies to ambiguous commands.
OLLAMA_TIMEOUT = float(os.getenv("LEGOPI_OLLAMA_TIMEOUT", "3.0"))

VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
VOICE_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

LIVE_HOST = os.getenv("LEGOPI_LIVE_HOST", "0.0.0.0")
LIVE_PORT = int(os.getenv("LEGOPI_LIVE_PORT", "5000"))

CAMERA_WIDTH = int(os.getenv("LEGOPI_CAMERA_WIDTH", "1280"))
CAMERA_HEIGHT = int(os.getenv("LEGOPI_CAMERA_HEIGHT", "720"))
CAMERA_FPS = int(os.getenv("LEGOPI_CAMERA_FPS", "20"))
# Corrects for the camera being physically mounted rotated (e.g. to fit inside an
# enclosure). One of: none, 90_cw, 90_ccw, 180. Applied in software after every capture,
# so it affects the live view and everything derived from it (scan, vision, color
# classification) identically.
CAMERA_ROTATE = os.getenv("LEGOPI_CAMERA_ROTATE", "none")

# Some third-party camera modules (e.g. Arducam's IMX519) get center-cropped by libcamera
# when a small output size is requested, instead of using the full sensor and scaling
# down. Set to the sensor's native resolution as "WIDTHxHEIGHT" (e.g. "4656x3496" for
# IMX519) to force Picamera2 to read the whole sensor. Leave unset to keep Picamera2's
# automatic mode selection (correct for the official Raspberry Pi camera modules).
_sensor_size_raw = os.getenv("LEGOPI_CAMERA_SENSOR_SIZE", "").strip().lower()
if _sensor_size_raw:
    _sensor_w, _sensor_h = _sensor_size_raw.split("x")
    CAMERA_SENSOR_SIZE: tuple[int, int] | None = (int(_sensor_w), int(_sensor_h))
else:
    CAMERA_SENSOR_SIZE = None

WAKE_THRESHOLD = float(os.getenv("LEGOPI_WAKE_THRESHOLD", "0.80"))
WAKE_MODEL_PATH = Path(os.getenv(
    "LEGOPI_WAKE_MODEL",
    HOME / "legopi-venv/lib/python3.13/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx",
))
VOSK_MODEL_PATH = Path(os.getenv("LEGOPI_VOSK_MODEL", HOME / "vosk-model"))
AUDIO_DEVICE = int(os.getenv("LEGOPI_AUDIO_DEVICE", "0")) if os.getenv("LEGOPI_AUDIO_DEVICE", "0").isdigit() else os.getenv("LEGOPI_AUDIO_DEVICE")
CAPTURE_RATE = 48000
STT_RATE = 16000
BLOCK_SIZE = 3840
COMMAND_MAX_SECONDS = 6.0
COMMAND_SILENCE_SECONDS = 0.75

VOLUME_COMMAND = os.getenv("LEGOPI_VOLUME_COMMAND", "/usr/local/bin/legopi-volume")
TTS_SCRIPT = Path(os.getenv("LEGOPI_TTS_SCRIPT", HOME / "elevenlabs-speak-final.py"))

CAPABILITIES_RESPONSE = (
    "I can see, identify, and keep track of your LEGO. "
    "I can tell you what a piece is, where you have it stored, "
    "add pieces to your inventory, and help you rebuild sets. "
    "You can control me by voice, and in Demo Mode I can demonstrate "
    "all of that without touching your real inventory. "
    "Just ask me what you want to try."
)
