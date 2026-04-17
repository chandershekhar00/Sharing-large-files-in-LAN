#!/usr/bin/env python3
"""
FileDrop v2.0 — server.py
Entry point. Parses CLI args, starts the HTTP server.
"""

import argparse
from pathlib import Path
from http.server import HTTPServer

from config import Config
from handler import FiledropHandler
from utils import get_local_ip, banner


def main():
    parser = argparse.ArgumentParser(
        description="FileDrop — Large file transfer server (LAN + Internet)"
    )
    parser.add_argument("--port",  type=int, default=8765,             help="Port to listen on (default: 8765)")
    parser.add_argument("--host",  type=str, default="0.0.0.0",        help="Host/IP to bind (default: 0.0.0.0)")
    parser.add_argument("--dir",   type=str, default="./received_files", help="Directory to save received files")
    args = parser.parse_args()

    # Apply config
    Config.UPLOAD_DIR = Path(args.dir)
    Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Config.PORT = args.port
    Config.HOST = args.host

    local_ip = get_local_ip()
    banner(local_ip, args.port)

    server = HTTPServer((args.host, args.port), FiledropHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  👋  FileDrop stopped.\n")


if __name__ == "__main__":
    main()
