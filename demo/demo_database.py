"""Safe DEMO/NORMAL data selector.

Inventory writes and rebuild-session writes select their database at runtime. DEMO mode
therefore never points an inventory mutation at the real inventory database.
"""
from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.config import DEMO_CATALOG_DB, DEMO_INVENTORY_DB, REAL_CATALOG_DB
from runtime.db_paths import catalog_db_path, inventory_db_path
from runtime.mode import enabled as demo_enabled, mode as get_mode, set_demo  # noqa: F401  (re-exported for API compatibility)

SEED_INVENTORY = [
    ("3001", "Brick 2 x 4", 4, "Red", 12, "U01-D01-Y01-X01"),
    ("3001", "Brick 2 x 4", 1, "Blue", 8, "U01-D01-Y01-X02"),
    ("3003", "Brick 2 x 2", 4, "Red", 8, "U01-D02-Y01-X01"),
    ("3004", "Brick 1 x 2", 4, "Red", 15, "U01-D02-Y01-X02"),
    ("3005", "Brick 1 x 1", 4, "Red", 20, "U01-D02-Y01-X03"),
    ("3010", "Brick 1 x 4", 3, "Yellow", 6, "U01-D03-Y01-X01"),
    ("3020", "Plate 2 x 4", 1, "Blue", 10, "U01-D03-Y01-X02"),
    ("3062", "Brick 1 x 1 Round", 0, "Black", 5, "U01-D03-Y01-X03"),
    ("4073", "Plate 1 x 1 Round", 15, "White", 7, "U01-D03-Y01-X04"),
]


def enable_demo() -> bool:
    set_demo(True)
    return True


def disable_demo() -> bool:
    set_demo(False)
    return True


def _reset_inventory() -> None:
    if not DEMO_INVENTORY_DB.exists():
        raise FileNotFoundError(f"Demo inventory database not found: {DEMO_INVENTORY_DB}")
    backup = DEMO_INVENTORY_DB.with_suffix(".PRE-RESET")
    shutil.copy2(DEMO_INVENTORY_DB, backup)
    con = sqlite3.connect(DEMO_INVENTORY_DB)
    try:
        con.execute("DELETE FROM inventory")
        con.execute("DELETE FROM inventory_history")
        con.execute("DELETE FROM rebrickable_sets")
        con.executemany(
            """
            INSERT INTO inventory(rebrickable_part_num,part_name,color_id,color_name,quantity,location_id,last_verified,notes)
            VALUES(?,?,?,?,?,?,datetime('now'),'LEGO PI DEMO DATA')
            """, SEED_INVENTORY,
        )
        con.execute(
            """
            INSERT INTO rebrickable_sets(set_num,set_name,theme,year,owned_qty,complete,storage_notes,rebrickable_url)
            VALUES('DEMO-001','LEGO Pi Demonstration Set','LEGO Pi Demo',2026,1,'No','Demonstration-only set','')
            """
        )
        con.commit()
    finally:
        con.close()


def _reset_catalog() -> None:
    # A demo catalog is a private copy. It may contain the public Rebrickable catalog but
    # never writes back to the real catalog. We clear the user's owned-set/session state.
    if not DEMO_CATALOG_DB.exists():
        if not REAL_CATALOG_DB.exists():
            # Nothing to reset and no catalog to bootstrap a demo copy from yet.
            return
        shutil.copy2(REAL_CATALOG_DB, DEMO_CATALOG_DB)
    con = sqlite3.connect(DEMO_CATALOG_DB)
    try:
        con.execute("DELETE FROM build_required_parts")
        con.execute("DELETE FROM build_scan_history")
        con.execute("DELETE FROM build_sessions")
        con.execute("DELETE FROM user_owned_sets")
        con.execute("INSERT OR REPLACE INTO sets(set_num,name,year,num_parts) VALUES('DEMO-001','LEGO Pi Demonstration Set',2026,6)")
        # Use existing catalog parts/colors when available.
        demo_parts = [("3001", 4, 4), ("3003", 4, 2), ("3039", 4, 1)]
        inv_id = con.execute("SELECT COALESCE(MAX(id),0)+1 FROM inventories").fetchone()[0]
        con.execute("INSERT OR REPLACE INTO inventories(id,set_num,version) VALUES(?,?,1)", (inv_id, "DEMO-001"))
        con.execute("DELETE FROM inventory_parts WHERE inventory_id=?", (inv_id,))
        for part_num, color_id, qty in demo_parts:
            con.execute("INSERT INTO inventory_parts(inventory_id,part_num,color_id,quantity,is_spare) VALUES(?,?,?,?,0)", (inv_id,part_num,color_id,qty))
        con.execute("INSERT OR REPLACE INTO user_owned_sets(set_num,acquired_date) VALUES('DEMO-001','2026-08-29')")
        con.commit()
    finally:
        con.close()


def reset_demo() -> bool:
    _reset_inventory()
    _reset_catalog()
    set_demo(False)
    return True


get_inventory_db = inventory_db_path
get_catalog_db = catalog_db_path


if __name__ == "__main__":
    print(f"MODE: {get_mode()}")
    print(f"INVENTORY DATABASE: {get_inventory_db()}")
    print(f"CATALOG DATABASE: {get_catalog_db()}")
