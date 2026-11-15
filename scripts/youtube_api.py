"""YouTube Data API access shared by the official news collectors."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://www.googleapis.com/youtube/v3"


def load_key() -> str:
    if os.environ.get("YOUTUBE_API_KEY"):
        return os.environ["YOUTUBE_API_KEY"].strip()
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip().lstrip("\ufeff") == "YOUTUBE_API_KEY":
                return value.strip().strip("\"'")
    raise SystemExit("Missing YOUTUBE_API_KEY. Add it to .env (see .env.example).")


def get_json(key: str, path: str, **params):
    request = urllib.request.Request(
        f"{API}/{path}?{urllib.parse.urlencode(params)}", headers={"X-Goog-Api-Key": key}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"YouTube API {exc.code} at {path}: {detail[:500]}") from None
