import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from demo import demo_database
from runtime import config


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_demo_reset_never_changes_real_inventory(tmp_path, monkeypatch):
    # config.REAL_INVENTORY_DB is resolved once at import time, so monkeypatch.setenv on
    # LEGOPI_HOME here would have no effect on the already-bound Path (and no such file
    # exists off-Pi anyway). Patch the attribute directly with a real, throwaway file
    # instead, matching how the app actually reads this constant.
    fake_real_db = tmp_path / "lego_inventory.db"
    fake_real_db.write_bytes(b"stand-in for the real inventory database")
    monkeypatch.setattr(config, "REAL_INVENTORY_DB", fake_real_db)

    before = sha(fake_real_db)
    demo_database.reset_demo()
    assert sha(fake_real_db) == before
    assert demo_database.get_mode() == "NORMAL"
