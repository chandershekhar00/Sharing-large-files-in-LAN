"""
FileDrop v2.0 — templates.py
Loads HTML files from the templates/ directory and injects runtime config.
"""

from pathlib import Path
from config import Config

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _load(name: str) -> str:
    path = TEMPLATE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def _inject(html: str) -> str:
    """Replace template placeholders with config values."""
    return (
        html
        .replace("{{VERSION}}",          Config.VERSION)
        .replace("{{CHUNK_SIZE}}",        str(Config.CHUNK_SIZE))
        .replace("{{REFRESH_INTERVAL}}", str(Config.REFRESH_INTERVAL_MS))
    )


def render_sender() -> str:
    return _inject(_load("sender.html"))


def render_receiver() -> str:
    return _inject(_load("receiver.html"))
