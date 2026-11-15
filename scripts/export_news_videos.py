"""Fetch public video metadata/statistics and export the official news corpus to CSV."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import threading
import time
import urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.collect_news_titles import DAILY_BUDGET, RECORDS, STATE as NEWS_STATE, METADATA_STATE as STATE, clean_title, recorded_regular_calls
from scripts.youtube_api import get_json, load_key

CACHE = ROOT / "reports/youtube_news_video_details.jsonl"
EXPORT = ROOT / "data/exports/youtube_news_videos_clean.csv"
REPORT = ROOT / "reports/youtube_news_videos_manifest.json"
COLUMNS = ["video_id", "title", "published_at_utc", "published_at_vn", "author",
           "channel_id", "video_url", "view_count", "like_count", "metrics_collected_at_utc"]
VN = ZoneInfo("Asia/Ho_Chi_Minh")
PACIFIC = ZoneInfo("America/Los_Angeles")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as source:
        return [json.loads(line) for line in source if line.strip()]


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("YouTube timestamps must include a timezone")
    return result


def count(value):
    if value is None:
        return ""
    if isinstance(value, bool) or not str(value).isascii() or not str(value).isdigit():
        raise ValueError("YouTube metrics must be nonnegative integers or absent")
    return str(value)


def csv_row(video: dict, allowed: set[str], start: str, end: str) -> dict | None:
    snippet = video.get("snippet", {})
    title = clean_title(snippet.get("title", ""))
    published = snippet.get("publishedAt", "")
    channel_id = snippet.get("channelId")
    author = clean_title(snippet.get("channelTitle", ""))
    if not title or not published or not author or channel_id not in allowed:
        return None
    published_time = timestamp(published).astimezone(timezone.utc)
    if not start <= published_time.date().isoformat() < end:
        return None
    statistics = video.get("statistics", {})
    return dict(zip(COLUMNS, [video["id"], title,
                             published_time.isoformat().replace("+00:00", "Z"),
                             published_time.astimezone(VN).isoformat(), author, channel_id,
                             f"https://www.youtube.com/watch?v={video['id']}",
                             count(statistics.get("viewCount")), count(statistics.get("likeCount")),
                             video["collected_at_utc"]]))


def select_rows(details: dict[str, dict], allowed: set[str], start: str, end: str) -> list[dict]:
    selected = {}
    for video in details.values():
        row = csv_row(video, allowed, start, end)
        # Keep a real zero, but omit rows where the API did not provide likes.
        if row is None or row["like_count"] == "":
            continue
        key = row["channel_id"], row["title"].casefold()
        current = selected.get(key)
        if current is None or (row["published_at_utc"], row["video_id"]) > (current["published_at_utc"], current["video_id"]):
            selected[key] = row
    return sorted(selected.values(), key=lambda row: (row["published_at_utc"], row["channel_id"], row["video_id"]))


def export(details: dict[str, dict], channels: list[dict], news: dict, status: str, requested: set[str],
           pending_metadata: set[str] | None = None) -> int:
    pending_metadata = pending_metadata or set()
    allowed = {c["id"] for c in channels}
    selected_details = {key: value for key, value in details.items() if key in requested}
    eligible_video_ids = set()
    missing_like_video_ids = set()
    for video_id, video in selected_details.items():
        candidate = csv_row(video, allowed, news["start"], news["end"])
        if candidate is None:
            continue
        eligible_video_ids.add(video_id)
        if candidate["like_count"] == "":
            missing_like_video_ids.add(video_id)
    rows = select_rows(selected_details, allowed, news["start"], news["end"])
    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    temporary = EXPORT.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    with temporary.open(encoding="utf-8-sig", newline="") as source:
        reread = list(csv.DictReader(source))
    assert reread == rows
    assert len(rows) == len({r["video_id"] for r in rows})
    assert len(rows) == len({(r["channel_id"], r["title"].casefold()) for r in rows})
    temporary.replace(EXPORT)
    by_channel = Counter(row["channel_id"] for row in rows)
    by_month = Counter(row["published_at_vn"][:7] for row in rows)
    title_channels = {}
    for row in rows:
        title_channels.setdefault(row["title"].casefold(), set()).add(row["channel_id"])
    batch_stats_ids = {key for key in requested & details.keys()
                       if "videos.batchGetStats" in details[key].get("metadata_source", "")}
    source = "YouTube Data API v3: videos.list (snippet,statistics)"
    if pending_metadata or batch_stats_ids:
        source = "YouTube Data API v3: playlistItems.list, channels.list, cached videos.list"
        if batch_stats_ids:
            source += ", videos.batchGetStats and supplemental search.list"
    full_scan_path = ROOT / "data/raw/youtube/news_titles_full_scan_state.json"
    full_scan = json.loads(full_scan_path.read_text(encoding="utf-8")) if full_scan_path.exists() else None
    report = {
        "source": source,
        "batch_stats_video_ids": len(batch_stats_ids),
        "batch_stats_csv_rows": sum(row["video_id"] in batch_stats_ids for row in rows),
        "batch_stats_note": "For these IDs, title/date/channel come from playlistItems.list or supplemental search.list (see cache metadata_source), author from the channel registry, and actual statistics from videos.batchGetStats.",
        "status": "partial_metadata" if pending_metadata else (status if news["status"] == "complete" else "partial_collection"),
        "collection_status": news["status"], "target_rows": 100000, "target_reached": len(rows) >= 100000,
        "supplementary_full_scan": ({"status": full_scan["status"], "pages": full_scan["pages"],
                                      "new_video_ids": full_scan["new_video_ids"],
                                      "note": "Independent scan without the normal old-page cutoff; partial coverage is recorded separately from the regular uploads pass."}
                                     if full_scan else None),
        "csv_rows": len(rows), "raw_video_ids": len(requested),
        "metadata_checked": len((requested & details.keys()) - pending_metadata),
        "metadata_pending_video_ids": len(pending_metadata),
        "csv_rows_pending_metadata": sum(row["video_id"] in pending_metadata for row in rows),
        "pending_metadata_note": "Uncached rows use the collected title/publication/channel and registry author; statistics and measurement time are blank. Fallbacks are not written to the API cache.",
        "start_utc": news["start"], "end_utc_exclusive": news["end"],
        "deduplication": "Videos without like_count are excluded first; among remaining videos, one normalized title per channel is kept, choosing the newest. Same titles from different channels are retained.",
        "author_definition": "The YouTube publishing channel title; not an individual reporter.",
        "statistics_definition": "Public cumulative counts at metrics_collected_at_utc, not counts on the publication date. Rows without like_count are excluded; a real zero is retained.",
        "title_groups_retained_across_channels": sum(len(ids) > 1 for ids in title_channels.values()),
        "missing_view_count": sum(row["view_count"] == "" for row in rows),
        "missing_like_count": sum(row["like_count"] == "" for row in rows),
        "eligible_video_ids_before_like_filter": len(eligible_video_ids),
        "video_ids_excluded_missing_like_count": len(missing_like_video_ids),
        "unavailable_video_ids": sum(not details[key].get("snippet") for key in requested & details.keys()),
        "records_by_month_vn": dict(sorted(by_month.items())),
        "channels": [{**c, "csv_rows": by_channel[c["id"]]} for c in channels],
        "export": str(EXPORT.relative_to(ROOT)), "columns": COLUMNS,
        "metrics_earliest_utc": min((r["metrics_collected_at_utc"] for r in rows if r["metrics_collected_at_utc"]), default=None),
        "metrics_latest_utc": max((r["metrics_collected_at_utc"] for r in rows if r["metrics_collected_at_utc"]), default=None),
        "retention_note": "Refresh or delete YouTube API metadata within 30 calendar days.",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[CSV] {len(rows):,} rows; {len(by_channel)} channels; {report['title_groups_retained_across_channels']:,} cross-channel title groups retained.", flush=True)
    return len(rows)


def self_check() -> None:
    def sample(video_id, channel, published, likes):
        return {"id": video_id, "snippet": {"title": " Cùng  một vấn đề ", "channelId": channel,
                "channelTitle": "Kênh thử", "publishedAt": published},
                "statistics": {"viewCount": "0", "likeCount": likes}, "collected_at_utc": "2026-10-14T00:00:00Z"}
    values = [sample("a", "one", "2026-06-01T18:00:00Z", None), sample("b", "two", "2026-06-01T18:00:00Z", "0"),
              sample("c", "one", "2026-06-02T18:00:00Z", "5")]
    rows = select_rows({v["id"]: v for v in values}, {"one", "two"}, "2026-06-01", "2026-10-15")
    assert {r["video_id"] for r in rows} == {"b", "c"}
    assert rows[0]["published_at_vn"] == "2026-06-02T01:00:00+07:00"
    assert count(None) == "" and count("0") == "0"
    assert csv_row(values[0], {"one"}, "2026-06-02", "2026-10-15") is None
    for invalid in (-1, True, "3.5", "unknown"):
        try:
            count(invalid)
        except ValueError:
            continue
        raise AssertionError("Malformed API statistics must be rejected")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cached-only", action="store_true",
                        help="Export without API calls; leave uncached statistics and measurement time blank")
    args = parser.parse_args()
    self_check()
    channels = json.loads((ROOT / "config/youtube_news_channels.json").read_text(encoding="utf-8"))
    news = json.loads(NEWS_STATE.read_text(encoding="utf-8"))
    if news["status"] not in ("complete", "budget_limited") and not (args.cached_only and news["status"] == "interrupted"):
        raise SystemExit("Finish or intentionally budget-limit the news uploads collection before fetching statistics")
    requested = {r["uri"].rsplit(":", 1)[-1] for r in load_jsonl(RECORDS)}
    now = datetime.now(timezone.utc)
    details = {v["id"]: v for v in load_jsonl(CACHE)
               if now - timedelta(days=30) < timestamp(v["collected_at_utc"]) <= now}
    pending = sorted(requested - details.keys())
    if args.cached_only:
        pending_ids = set(pending)
        authors = {c["id"]: c["name"] for c in channels}
        with RECORDS.open(encoding="utf-8-sig") as source:
            for line in source:
                if not line.strip():
                    continue
                record = json.loads(line)
                video_id = record["uri"].rsplit(":", 1)[-1]
                if video_id in pending_ids and record["channel_id"] in authors:
                    details[video_id] = {
                        "id": video_id,
                        "snippet": {"title": record["text"], "publishedAt": record["created_at"],
                                    "channelId": record["channel_id"], "channelTitle": authors[record["channel_id"]]},
                        "statistics": {}, "collected_at_utc": "",
                    }
        export(details, channels, news, "complete", requested, pending_ids)
        print(f"[CSV] Offline export: {len(pending_ids):,} video IDs still need API metadata.", flush=True)
        return
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"calls": 0, "quota_day_pt": ""}
    lock = threading.Lock()
    key = load_key()

    def fetch(ids):
        for attempt in range(3):
            with lock:
                day = datetime.now(PACIFIC).date().isoformat()
                if state["quota_day_pt"] != day:
                    state.update(quota_day_pt=day, calls=0)
                if state["calls"] + recorded_regular_calls(day, exclude=STATE) >= DAILY_BUDGET:
                    raise RuntimeError("Combined news/statistics daily safety budget reached; resume after quota reset")
                state["calls"] += 1
                temporary = STATE.with_suffix(".tmp")
                temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
                temporary.replace(STATE)
            try:
                result = get_json(key, "videos", part="snippet,statistics", id=",".join(ids),
                                  fields="items(id,snippet/title,snippet/publishedAt,snippet/channelId,snippet/channelTitle,statistics/viewCount,statistics/likeCount)")
                collected = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                found = {v["id"]: {**v, "collected_at_utc": collected} for v in result.get("items", [])}
                return [found.get(video_id, {"id": video_id, "collected_at_utc": collected, "unavailable": True}) for video_id in ids]
            except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                transient = isinstance(exc, (urllib.error.URLError, TimeoutError)) or any(f"API {code}" in str(exc) for code in (500, 502, 503, 504))
                if not transient or attempt == 2:
                    raise
                time.sleep(2 ** (attempt + 1))

    status = "interrupted"
    print(f"[CSV] Fetching metadata/statistics for {len(pending):,} videos; {len(requested & details.keys()):,} cached.", flush=True)
    try:
        with ThreadPoolExecutor(max_workers=4) as pool, CACHE.open("a", encoding="utf-8") as output:
            for offset in range(0, len(pending), 200):
                futures = [pool.submit(fetch, pending[i:i + 50]) for i in range(offset, min(offset + 200, len(pending)), 50)]
                errors = []
                for future in as_completed(futures):
                    try:
                        for video in future.result():
                            output.write(json.dumps(video, ensure_ascii=False) + "\n")
                            details[video["id"]] = video
                        output.flush()
                    except Exception as exc:
                        errors.append(exc)
                if errors:
                    raise errors[0]
                if offset % 4000 == 0:
                    print(f"[CSV] {len(requested & details.keys()):,}/{len(requested):,} videos checked.", flush=True)
        status = "complete"
    finally:
        # Preserve the previous CSV when a refresh fails; successful batches remain cached.
        if status == "complete":
            total = export(details, channels, news, status, requested)
    if total < 100000:
        print(f"[CSV] Need {100000 - total:,} more valid rows to reach the requested target.", flush=True)


if __name__ == "__main__":
    main()
