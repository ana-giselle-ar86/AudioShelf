# db_layer/equalizer_repo.py
# Copyright (c) 2025-2026 Mehdi Rajabi
# License: GNU General Public License v3.0 (See LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import logging
import sqlite3
from typing import Dict, Optional, List, Any
from i18n import _

def _translate_metadata():
    _("Flat")
    _("Vocal Clarity")
    _("Fullness")
    _("Reduce Boominess")
    _("De-Esser")

class EqualizerRepository:
    def __init__(self, conn: sqlite3.Connection, default_presets: Dict[str, str]):
        self.conn = conn
        self.default_presets = default_presets
        self._initialize_default_presets()

    def _initialize_default_presets(self):
        if self.conn is None:
            return
        try:
            presets_data = [(name, settings) for name, settings in self.default_presets.items()]
            with self.conn:
                self.conn.executemany(
                    "INSERT OR IGNORE INTO eq_presets (name, settings) VALUES (?, ?)",
                    presets_data
                )
        except sqlite3.Error as e:
            logging.error(f"Error initializing default EQ presets: {e}", exc_info=True)

    def get_all_presets(self) -> List[Dict[str, Any]]:
        if self.conn is None:
            return []

        results = []
        cur = None
        try:
            cur = self.conn.cursor()
            query = """
                SELECT id, name, settings FROM eq_presets 
                ORDER BY 
                    CASE name
                        WHEN 'Flat' THEN 0
                        WHEN 'Vocal Clarity' THEN 1
                        WHEN 'Fullness' THEN 2
                        WHEN 'Reduce Boominess' THEN 3
                        WHEN 'De-Esser' THEN 4
                        ELSE 5
                    END, 
                    name
            """
            cur.execute(query)
            for row in cur.fetchall():
                results.append({
                    "id": row[0],
                    "name": _(row[1]),
                    "settings": row[2]
                })
            return results
        except sqlite3.Error as e:
            logging.error(f"Error getting all EQ presets: {e}", exc_info=True)
            return []
        finally:
            if cur:
                cur.close()

    def save_preset(self, name: str, settings: str) -> Optional[int]:
        if self.conn is None:
            return None
        cur = None
        try:
            with self.conn:
                cur = self.conn.cursor()
                cur.execute(
                    "INSERT INTO eq_presets (name, settings) VALUES (?, ?)",
                    (name, settings)
                )
                return cur.lastrowid
        except sqlite3.IntegrityError:
            logging.warning(f"Error saving EQ preset: Name '{name}' already exists.")
            return None
        except sqlite3.Error as e:
            logging.error(f"Error saving EQ preset: {e}", exc_info=True)
            return None
        finally:
            if cur:
                cur.close()

    def delete_preset(self, preset_id: int):
        if self.conn is None:
            return
        try:
            with self.conn:
                self.conn.execute("DELETE FROM eq_presets WHERE id = ?", (preset_id,))
        except sqlite3.Error as e:
            logging.error(f"Error deleting EQ preset ID {preset_id}: {e}", exc_info=True)