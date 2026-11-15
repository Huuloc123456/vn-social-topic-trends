"""Wait for the next Pacific quota day, then resume the 2023 news crawl once."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "data/raw/youtube/news_titles_state.json"
LOG = ROOT / "reports/youtube_2023_backfill_resume.log"
PACIFIC = ZoneInfo("America/Los_Angeles")


def main() -> int:
    state = json.loads(STATE.read_text(encoding="utf-8-sig"))
    saved_day = state.get("quota_day_pt")
    while datetime.now(PACIFIC).date().isoformat() == saved_day:
        time.sleep(30)

    state = json.loads(STATE.read_text(encoding="utf-8-sig"))
    if state.get("status") == "complete":
        return 0
    if state.get("start") != "2023-01-01" or state.get("end") != "2026-10-30":
        raise RuntimeError("The saved crawl checkpoint no longer matches the 2023 backfill.")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    command = [sys.executable, str(ROOT / "scripts/collect_news_titles.py"),
               "--start", "2023-01-01", "--end", "2026-10-30"]
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as output:
        output.write(f"\n[RESUME] {datetime.now(PACIFIC).isoformat()}\n")
        output.flush()
        return subprocess.run(command, cwd=ROOT, env=env, stdout=output,
                              stderr=subprocess.STDOUT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
