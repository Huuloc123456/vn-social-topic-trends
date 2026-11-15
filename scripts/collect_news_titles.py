"""Collect title-only uploads from the news channels in config, with page checkpoints."""
from __future__ import annotations

import argparse
import html
import http.client
import json
import sys
import time
import unicodedata
import urllib.error
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.youtube_api import get_json, load_key

OUT = ROOT / "data/raw/youtube"
RECORDS = OUT / "news_title_records.jsonl"
STATE = OUT / "news_titles_state.json"
METADATA_STATE = ROOT / "reports/youtube_news_details_state.json"
REPORT = ROOT / "reports/youtube_news_titles_manifest.json"
PACIFIC = ZoneInfo("America/Los_Angeles")
DAILY_BUDGET = 10000


def recorded_regular_calls(day: str, exclude: Path | None = None) -> int:
    """Count the shared ordinary bucket across uploads, metadata and full scans."""
    total = 0
    for path in (STATE, METADATA_STATE, OUT / "news_titles_full_scan_state.json"):
        if path == exclude or not path.exists():
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("quota_day_pt") == day:
            total += value.get("calls", 0)
    return total


def save_state(state: dict) -> None:
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(STATE)


def clean_title(text: str) -> str:
    text = unicodedata.normalize("NFC", html.unescape(text))
    text = "".join(c for c in text if c not in "\u200b\ufeff" and
                   (not unicodedata.category(c).startswith("C") or c.isspace() or c in "\u200c\u200d"))
    return " ".join(text.split())


def export_results(channels: list[dict], state: dict) -> None:
    seen = set()
    by_channel, by_month = Counter(), Counter()
    retrieval_methods = Counter()
    records = 0
    with RECORDS.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            assert record["record_type"] == "video" and state["start"] <= record["created_at"][:10] < state["end"]
            records += 1
            retrieval_methods[record.get("retrieval_method", "playlistItems.list")] += 1
            by_channel[record["channel_id"]] += 1
            by_month[record["created_at"][:7]] += 1
            title = clean_title(record["text"])
            key = record["channel_id"], title.casefold()
            if title and key not in seen:
                seen.add(key)
    manifest = {
        "source": "YouTube Data API v3: channel uploads and supplemental Search" if retrieval_methods["search.list"] else "YouTube Data API v3: channel uploads",
        "retrieval_methods": dict(retrieval_methods),
        "start_utc": state["start"], "end_utc_exclusive": state["end"],
        "status": state["status"], "video_records": records,
        "channel_title_pairs": len(seen),
        "records_by_month": dict(sorted(by_month.items())),
        "channels": [{**c, "video_records": by_channel[c["id"]]} for c in channels],
        "content": "titles only; raw records retain video ID, publication date, and channel ID",
        "scan_start_utc": state.get("scan_start", state["start"]),
        "cutoff": "stop an uploads playlist when a whole dated page is older than scan_start_utc",
        "retention_note": "Refresh or delete YouTube API metadata within 30 calendar days.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[NEWS] {state['status']}: {records:,} videos; {len(seen):,} channel/title pairs.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2026-01-01")
    parser.add_argument("--end", default=(datetime.now(ZoneInfo("Asia/Bangkok")).date() + timedelta(days=1)).isoformat())
    parser.add_argument("--refresh", action="store_true", help="Rescan completed channels for new uploads, keeping existing records")
    parser.add_argument("--max-pages", type=int, help="Stop after this many additional pages and keep the checkpoint")
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end <= start:
        raise SystemExit("End must be after start")
    if args.max_pages is not None and args.max_pages < 1:
        raise SystemExit("Max pages must be positive")
    channels = json.loads((ROOT / "config/youtube_news_channels.json").read_text(encoding="utf-8"))
    channel_ids = [c["id"] for c in channels]
    OUT.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {
        "start": args.start, "end": args.end, "channels": channel_ids,
        "channel_index": 0, "page_token": None, "pages": 0,
        "quota_day_pt": datetime.now(PACIFIC).date().isoformat(), "calls": 10,
    }
    if args.refresh:
        if (state.get("status") != "complete" or args.start > state["start"]
                or args.end < state["end"] or channel_ids[:len(state["channels"])] != state["channels"]):
            raise SystemExit("Refresh requires a completed crawl, unchanged channel order, an unchanged or earlier start, and an unchanged or later end")
        # An earlier start requires a history scan; otherwise overlap the last partial day.
        scan_start = args.start if args.start < state["start"] else (date.fromisoformat(state["end"]) - timedelta(days=1)).isoformat()
        state.update(start=args.start, end=args.end, scan_start=scan_start, channel_index=0, page_token=None)
    if (state["start"], state["end"]) != (args.start, args.end) or channel_ids[:len(state["channels"])] != state["channels"]:
        raise SystemExit("Keep the saved date range and channel order; append new channels to resume")
    if len(channel_ids) != len(set(channel_ids)):
        raise SystemExit("Channel IDs must be unique")
    if len(channel_ids) > len(state["channels"]):
        state["scan_start"] = args.start
    state["channels"] = channel_ids
    seen_ids = set()
    counts = Counter()
    if RECORDS.exists():
        with RECORDS.open(encoding="utf-8-sig") as source:
            for line in source:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("record_type") != "video":
                    continue
                seen_ids.add(record["uri"])
                counts[record["channel_id"]] += 1
    key = load_key()
    state["status"] = "in_progress"
    pages_at_start = state["pages"]
    save_state(state)
    print(f"[NEWS] {len(channels)} channels; {args.start} to {args.end} UTC exclusive.", flush=True)
    try:
        with RECORDS.open("a", encoding="utf-8") as output:
            while state["channel_index"] < len(channels):
                if args.max_pages is not None and state["pages"] - pages_at_start >= args.max_pages:
                    state["status"] = "budget_limited"
                    break
                channel = channels[state["channel_index"]]
                day = datetime.now(PACIFIC).date().isoformat()
                if state["quota_day_pt"] != day:
                    state.update(quota_day_pt=day, calls=0)
                if state["calls"] + recorded_regular_calls(day, exclude=STATE) >= DAILY_BUDGET:
                    raise RuntimeError("Combined news/statistics daily safety budget reached; resume after quota reset")
                for attempt in range(5):
                    state["calls"] += 1
                    save_state(state)
                    try:
                        page = get_json(key, "playlistItems", part="snippet,contentDetails",
                                        playlistId=channel["uploads"], maxResults=50,
                                        fields="nextPageToken,items(snippet/title,contentDetails/videoId,contentDetails/videoPublishedAt)",
                                        **({"pageToken": state["page_token"]} if state["page_token"] else {}))
                        break
                    except RuntimeError as exc:
                        if ("API 404 at playlistItems" in str(exc)
                                and "playlistNotFound" in str(exc)):
                            skipped = state.setdefault("unavailable_channels", [])
                            if not any(item.get("id") == channel["id"] for item in skipped):
                                skipped.append({"id": channel["id"], "name": channel["name"],
                                                "reason": "uploads playlist not found"})
                            print(f"[NEWS] {channel['name']}: uploads playlist not found; skipping source.", flush=True)
                            state["channel_index"] += 1
                            state["page_token"] = None
                            save_state(state)
                            page = None
                            break
                        transient = any(f"API {code}" in str(exc) for code in (500, 502, 503, 504))
                        if not transient or attempt == 2:
                            raise
                        time.sleep(2 ** (attempt + 1))
                    except (urllib.error.URLError, TimeoutError, http.client.RemoteDisconnected, ConnectionResetError, RuntimeError) as exc:
                        transient = isinstance(exc, (urllib.error.URLError, TimeoutError)) or any(
                            f"API {code}" in str(exc) for code in (500, 502, 503, 504))
                        if not transient or attempt == 2:
                            raise
                        time.sleep(2 ** (attempt + 1))
                if page is None:
                    continue
                dates = []
                for item in page.get("items", []):
                    details = item.get("contentDetails", {})
                    published, video_id = details.get("videoPublishedAt"), details.get("videoId")
                    if not published or not video_id:
                        continue
                    datetime.fromisoformat(published.replace("Z", "+00:00"))
                    published_day = published[:10]
                    dates.append(published_day)
                    title = clean_title(item.get("snippet", {}).get("title", ""))
                    uri = f"youtube:video:{video_id}"
                    if not title or uri in seen_ids or not args.start <= published_day < args.end:
                        continue
                    output.write(json.dumps({"uri": uri, "source": "youtube", "record_type": "video",
                                             "topic_query": "thoi_su", "created_at": published,
                                             "channel_id": channel["id"], "text": title}, ensure_ascii=False) + "\n")
                    seen_ids.add(uri)
                    counts[channel["id"]] += 1
                output.flush()
                state["pages"] += 1
                next_page = page.get("nextPageToken")
                # shortcut: assumes uploads are newest first; scan full history if a channel reorders old uploads.
                if not next_page or (dates and max(dates) < state.get("scan_start", args.start)):
                    print(f"[NEWS] {channel['name']}: {counts[channel['id']]:,} titles; channel finished.", flush=True)
                    state["channel_index"] += 1
                    state["page_token"] = None
                else:
                    state["page_token"] = next_page
                save_state(state)
                if state["pages"] % 25 == 0:
                    print(f"[NEWS] {len(seen_ids):,} videos; {state['pages']:,} pages; {channel['name']}.", flush=True)
        if state["channel_index"] == len(channels):
            state["status"] = "complete"
    except Exception:
        state["status"] = "interrupted"
        raise
    finally:
        save_state(state)
        export_results(channels, state)


if __name__ == "__main__":
    main()
