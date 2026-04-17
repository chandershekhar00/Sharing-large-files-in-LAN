"""
FileDrop v2.0 — transfers.py
In-memory transfer state manager.
Tracks active (in-progress) and completed transfers with thread safety.
"""

import threading
import time
from typing import Dict, List, Optional


class TransferStore:
    """Thread-safe store for active and completed file transfers."""

    def __init__(self):
        self._lock = threading.Lock()
        # active: { file_id -> dict }
        self._active: Dict[str, dict] = {}
        # completed: list of dicts
        self._completed: List[dict] = []

    # ── Active transfers ──────────────────────────────────────────────────────

    def init_transfer(self, file_id: str, filename: str, size: int, total_chunks: int) -> None:
        """Register a new incoming transfer."""
        with self._lock:
            self._active[file_id] = {
                "file_id":        file_id,
                "filename":       filename,
                "size":           size,
                "received":       0,
                "total_chunks":   total_chunks,
                "chunks_received": set(),
                "started":        time.time(),
            }

    def record_chunk(self, file_id: str, chunk_index: int, chunk_size: int) -> bool:
        """Mark a chunk as received. Returns False if file_id unknown."""
        with self._lock:
            if file_id not in self._active:
                return False
            info = self._active[file_id]
            info["chunks_received"].add(chunk_index)
            # Estimate received bytes (final chunk may be smaller)
            info["received"] = min(
                len(info["chunks_received"]) * chunk_size,
                info["size"]
            )
            return True

    def get_active(self, file_id: str) -> Optional[dict]:
        with self._lock:
            return dict(self._active[file_id]) if file_id in self._active else None

    def is_active(self, file_id: str) -> bool:
        with self._lock:
            return file_id in self._active

    def complete_transfer(self, file_id: str) -> Optional[dict]:
        """Move a transfer from active → completed. Returns the entry or None."""
        with self._lock:
            if file_id not in self._active:
                return None
            info = self._active.pop(file_id)
            entry = {
                "file_id":  file_id,
                "filename": info["filename"],
                "size":     info["size"],
                "received": info["size"],
                "elapsed":  round(time.time() - info["started"], 2),
            }
            self._completed.append(entry)
            return entry

    # ── Status snapshots (safe copies for JSON) ───────────────────────────────

    def snapshot_active(self) -> List[dict]:
        with self._lock:
            return [
                {
                    "file_id":  fid,
                    "filename": info["filename"],
                    "size":     info["size"],
                    "received": info["received"],
                    "status":   "active",
                }
                for fid, info in self._active.items()
            ]

    def snapshot_completed(self) -> List[dict]:
        with self._lock:
            return [{**c, "status": "complete"} for c in self._completed]

    def find_completed(self, file_id: str) -> Optional[dict]:
        with self._lock:
            return next((c for c in self._completed if c["file_id"] == file_id), None)


# Singleton — imported by handler.py and used across all requests
store = TransferStore()
