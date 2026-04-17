"""
FileDrop v2.0 — config.py
Central configuration. Edit this file to change defaults.
"""

from pathlib import Path


class Config:
    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str         = "0.0.0.0"
    PORT: int         = 8765
    VERSION: str      = "2.0.0"

    # ── Transfer ──────────────────────────────────────────────────────────────
    CHUNK_SIZE: int   = 4 * 1024 * 1024   # 4 MB per chunk
    MAX_FILE_SIZE: int = 100 * 1024 ** 3  # 100 GB hard limit

    # ── Storage ───────────────────────────────────────────────────────────────
    UPLOAD_DIR: Path  = Path("./received_files")

    # ── UI ────────────────────────────────────────────────────────────────────
    REFRESH_INTERVAL_MS: int = 2000       # Receiver page poll interval
