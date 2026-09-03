from __future__ import annotations

import subprocess

from .config import VOLUME_COMMAND


def set_volume(level: int) -> bool:
    if not 0 <= int(level) <= 10:
        return False
    return subprocess.run([VOLUME_COMMAND, str(int(level))], check=False).returncode == 0
