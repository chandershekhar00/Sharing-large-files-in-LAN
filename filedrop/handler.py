"""
FileDrop v2.0 — handler.py
HTTP request handler. Routes all GET and POST endpoints.

Routes:
  GET  /              → sender UI
  GET  /receive       → receiver UI
  GET  /api/status    → JSON transfer status
  GET  /download/<id> → stream completed file
  GET  /static/*      → serve CSS/JS static assets

  POST /api/upload/init     → register new transfer
  POST /api/upload/chunk    → receive a chunk
  POST /api/upload/complete → assemble final file
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from config import Config
from transfers import store
from utils import get_mime, format_size, assemble_chunks
from templates import render_sender, render_receiver

STATIC_DIR = Path(__file__).parent / "static"


class FiledropHandler(BaseHTTPRequestHandler):

    # ── Logging ───────────────────────────────────────────────────────────────

    def log_message(self, fmt, *args):
        # Print a compact single-line log instead of default verbose output
        method = self.command
        path   = self.path.split("?")[0]
        print(f"  {method:4s}  {path}")

    # ── Response helpers ──────────────────────────────────────────────────────

    def send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, filepath: Path) -> None:
        if not filepath.exists():
            self.send_response(404)
            self.end_headers()
            return
        mime = get_mime(filepath.name)
        data = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", len(data))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)

    def not_found(self) -> None:
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not found")

    # ── GET ───────────────────────────────────────────────────────────────────

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/") or "/"

        if path in ("/", "/send"):
            self.send_html(render_sender())

        elif path == "/receive":
            self.send_html(render_receiver())

        elif path == "/api/status":
            self.send_json({
                "active":    store.snapshot_active(),
                "completed": store.snapshot_completed(),
            })

        elif path.startswith("/download/"):
            self._handle_download(path.split("/download/", 1)[1])

        elif path.startswith("/static/"):
            rel = path[len("/static/"):]
            self.send_static(STATIC_DIR / rel)

        else:
            self.not_found()

    def _handle_download(self, file_id: str) -> None:
        entry = store.find_completed(file_id)
        if not entry:
            self.not_found()
            return

        filepath = Config.UPLOAD_DIR / file_id / entry["filename"]
        if not filepath.exists():
            self.not_found()
            return

        size = filepath.stat().st_size
        mime = get_mime(entry["filename"])
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", size)
        self.send_header("Content-Disposition",
                         f'attachment; filename="{entry["filename"]}"')
        self.end_headers()

        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(Config.CHUNK_SIZE)
                if not chunk:
                    break
                self.wfile.write(chunk)

    # ── POST ──────────────────────────────────────────────────────────────────

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/upload/init":
            self._handle_init()
        elif path == "/api/upload/chunk":
            self._handle_chunk()
        elif path == "/api/upload/complete":
            self._handle_complete()
        else:
            self.not_found()

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length))

    def _handle_init(self) -> None:
        body    = self._read_json_body()
        file_id = body["file_id"]
        size    = body["size"]
        name    = body["filename"]

        store.init_transfer(file_id, name, size, body["total_chunks"])

        tmp_dir = Config.UPLOAD_DIR / file_id
        tmp_dir.mkdir(parents=True, exist_ok=True)

        print(f"  📥 Incoming: {name} ({format_size(size)})")
        self.send_json({"ok": True, "file_id": file_id})

    def _handle_chunk(self) -> None:
        content_type = self.headers.get("Content-Type", "")
        if "boundary=" not in content_type:
            self.send_json({"error": "expected multipart/form-data"}, 400)
            return

        boundary = content_type.split("boundary=")[1].encode()
        length   = int(self.headers.get("Content-Length", 0))
        raw      = self.rfile.read(length)

        parts = _parse_multipart(raw, boundary)

        file_id     = parts.get("file_id", b"").decode()
        chunk_index = int(parts.get("chunk_index", b"0").decode())
        chunk_data  = parts.get("chunk", b"")

        if not file_id or not store.is_active(file_id):
            self.send_json({"error": "unknown file_id"}, 400)
            return

        # Persist chunk to disk immediately
        chunk_path = Config.UPLOAD_DIR / file_id / f"chunk_{chunk_index:06d}"
        with open(chunk_path, "wb") as f:
            f.write(chunk_data)

        store.record_chunk(file_id, chunk_index, Config.CHUNK_SIZE)
        self.send_json({"ok": True})

    def _handle_complete(self) -> None:
        body    = self._read_json_body()
        file_id = body["file_id"]
        name    = body["filename"]

        info = store.get_active(file_id)
        if not info:
            self.send_json({"error": "unknown file_id"}, 400)
            return

        print(f"  🔧 Assembling: {name}…")
        assemble_chunks(file_id, name, info["total_chunks"])

        entry   = store.complete_transfer(file_id)
        elapsed = entry["elapsed"]
        speed   = format_size(info["size"] / max(elapsed, 0.001))
        print(f"  ✅ Done: {name}  ({format_size(info['size'])}  {speed}/s  {elapsed}s)")

        self.send_json({"ok": True, "file_id": file_id})


# ── Multipart parser ──────────────────────────────────────────────────────────

def _parse_multipart(raw: bytes, boundary: bytes) -> dict:
    """
    Minimal multipart/form-data parser.
    Returns {field_name: bytes} for each part.
    """
    parts = {}
    for segment in raw.split(b"--" + boundary):
        if b"Content-Disposition" not in segment:
            continue
        header_end = segment.find(b"\r\n\r\n")
        if header_end == -1:
            continue
        headers_raw = segment[:header_end].decode(errors="replace")
        body_raw    = segment[header_end + 4:]
        if body_raw.endswith(b"\r\n"):
            body_raw = body_raw[:-2]

        name = ""
        for part in headers_raw.split(";"):
            part = part.strip()
            if part.startswith("name="):
                name = part.split("=", 1)[1].strip('"')
        if name:
            parts[name] = body_raw

    return parts
