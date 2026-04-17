"""
FileDrop v2.0 — utils.py
Helper functions: networking, formatting, file assembly.
"""

import os
import socket
import mimetypes
from pathlib import Path

from config import Config


# ── Network ───────────────────────────────────────────────────────────────────

def get_local_ip() -> str:
    """Detect the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ── Formatting ────────────────────────────────────────────────────────────────

def format_size(b: int) -> str:
    """Human-readable file size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def get_mime(filename: str) -> str:
    """Guess MIME type from filename."""
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


# ── File assembly ─────────────────────────────────────────────────────────────

def assemble_chunks(file_id: str, filename: str, total_chunks: int) -> Path:
    """
    Concatenate all chunk_XXXXXX files in UPLOAD_DIR/file_id/
    into the final output file, then delete the chunk files.
    Returns path to assembled file.
    """
    tmp_dir  = Config.UPLOAD_DIR / file_id
    out_path = tmp_dir / filename

    with open(out_path, "wb") as out:
        for i in range(total_chunks):
            chunk_path = tmp_dir / f"chunk_{i:06d}"
            if chunk_path.exists():
                with open(chunk_path, "rb") as cf:
                    out.write(cf.read())
                os.remove(chunk_path)

    return out_path


# ── Console ───────────────────────────────────────────────────────────────────

def banner(local_ip: str, port: int) -> None:
    """Print startup banner with access URLs."""
    v = Config.VERSION
    print()
    print("  ╔══════════════════════════════════════════╗")
    print(f"  ║      FileDrop  v{v}  — File Transfer     ║")
    print("  ╚══════════════════════════════════════════╝")
    print()
    print(f"  📡  Listening on  {Config.HOST}:{port}")
    print(f"  📂  Saving to     {Config.UPLOAD_DIR.resolve()}")
    print()
    print("  ── LAN (same network) ──────────────────────")
    print(f"  Sender:    http://{local_ip}:{port}/")
    print(f"  Receiver:  http://{local_ip}:{port}/receive")
    print()
    print("  ── Internet (different networks) ───────────")
    print("  1. Install ngrok: https://ngrok.com/download")
    print(f"  2. Run:  ngrok http {port}")
    print("  3. Share the https://xxxx.ngrok.io URL:")
    print(f"     Sender:    https://<ngrok-url>/")
    print(f"     Receiver:  https://<ngrok-url>/receive")
    print()
    print("  Press Ctrl+C to stop.")
    print()
