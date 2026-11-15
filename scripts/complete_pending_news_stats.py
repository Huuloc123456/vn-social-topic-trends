"""Fetch statistics only for newly collected IDs absent from the metadata cache.

Uses the documented videos.batchGetStats method and its separate quota ledger.
Title/publication/channel come from uploads or Search; author comes from the registry.
Existing cached videos are never refreshed by this command.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.export_news_videos import CACHE, RECORDS, PACIFIC
from scripts.youtube_api import get_json, load_key

LEDGER = ROOT / "reports/youtube_batch_stats_state.json"
RESPONSES = ROOT / "reports/youtube_batch_stats_responses.jsonl"


def main() -> None:
    cached = set()
    if CACHE.exists():
        with CACHE.open(encoding="utf-8-sig") as source:
            for line in source:
                item = json.loads(line)
                cached.add(item["id"])
    authors = {c["id"]: c["name"] for c in json.loads(
        (ROOT / "config/youtube_news_channels.json").read_text(encoding="utf-8"))}
    pending = {}
    with RECORDS.open(encoding="utf-8-sig") as source:
        for line in source:
            record = json.loads(line)
            video_id = record["uri"].rsplit(":", 1)[-1]
            if video_id not in cached and record["channel_id"] in authors:
                pending[video_id] = record
    print(f"[STATS] {len(pending):,} new IDs without cached metadata.", flush=True)
    if not pending:
        return
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
    day = datetime.now(PACIFIC).date().isoformat()
    if ledger.get("quota_day_pt") != day:
        ledger = {"quota_day_pt": day, "calls": 0, "method": "videos.batchGetStats"}
    key = load_key()
    ids = sorted(pending)
    for offset in range(0, len(ids), 50):
        batch = ids[offset:offset + 50]
        if ledger["calls"] >= 10000:
            raise SystemExit("Dedicated batch statistics safety budget reached")
        ledger["calls"] += 1
        ledger["last_requested_at_utc"] = datetime.now(timezone.utc).isoformat()
        LEDGER.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        # Stop on the first error; this is a data request, never a quota probe.
        response = get_json(key, "videos:batchGetStats", part="statistics", id=",".join(batch))
        measured = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with RESPONSES.open("a", encoding="utf-8") as output:
            output.write(json.dumps({"collected_at_utc": measured, "requested_ids": batch,
                                     "response": response}, ensure_ascii=False) + "\n")
        saved = 0
        with CACHE.open("a", encoding="utf-8") as output:
            for item in response.get("items", []):
                if item.get("id") not in batch or not isinstance(item.get("statistics"), dict):
                    continue
                raw = pending[item["id"]]
                video = {"id": item["id"], "snippet": {
                    "title": raw["text"], "publishedAt": raw["created_at"],
                    "channelId": raw["channel_id"], "channelTitle": authors[raw["channel_id"]]},
                    "statistics": item["statistics"], "collected_at_utc": measured,
                    "metadata_source": raw.get("retrieval_method", "playlistItems.list") + " + channel registry + videos.batchGetStats"}
                output.write(json.dumps(video, ensure_ascii=False) + "\n")
                saved += 1
        print(f"[STATS] Saved {saved}/{len(batch)} new video statistics.", flush=True)


if __name__ == "__main__":
    main()
