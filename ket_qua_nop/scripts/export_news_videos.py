"""Fetch public video metadata/statistics and export the official news corpus to CSV."""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
import tempfile
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


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("YouTube timestamps must include a timezone")
    return result


def jsonl_lines(path: Path):
    if path.exists():
        with path.open(encoding="utf-8-sig") as source:
            yield from source


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


def store_latest(connection: sqlite3.Connection, row: dict, is_batch_stats: bool) -> None:
    connection.execute("""
        INSERT INTO selected VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(channel_id, title_key) DO UPDATE SET
            published_at_utc=excluded.published_at_utc, video_id=excluded.video_id,
            row_json=excluded.row_json, is_batch_stats=excluded.is_batch_stats
        WHERE (excluded.published_at_utc, excluded.video_id) > (selected.published_at_utc, selected.video_id)
    """, (row["channel_id"], row["title"].casefold(), row["published_at_utc"], row["video_id"],
          json.dumps(row, ensure_ascii=False), int(is_batch_stats)))


def build_index(connection: sqlite3.Connection, now: datetime) -> tuple[int, int]:
    connection.executescript("""
        CREATE TABLE requested (video_id TEXT PRIMARY KEY);
        CREATE TABLE raw_video (
            video_id TEXT PRIMARY KEY, channel_id TEXT, title TEXT, created_at TEXT
        );
        CREATE TABLE metadata (video_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE pending_metadata (video_id TEXT PRIMARY KEY);
    """)
    with RECORDS.open(encoding="utf-8-sig") as source:
        batch = []
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("record_type") != "video":
                continue
            video_id = record["uri"].rsplit(":", 1)[-1]
            batch.append((video_id, record["channel_id"], record["text"], record["created_at"]))
            if len(batch) >= 5000:
                connection.executemany("INSERT OR REPLACE INTO raw_video VALUES (?, ?, ?, ?)", batch)
                batch.clear()
        if batch:
            connection.executemany("INSERT OR REPLACE INTO raw_video VALUES (?, ?, ?, ?)", batch)
    connection.execute("INSERT INTO requested SELECT video_id FROM raw_video")
    connection.commit()

    cached = 0
    for line in jsonl_lines(CACHE):
        if not line.strip():
            continue
        video = json.loads(line)
        collected = video.get("collected_at_utc")
        if not collected or not now - timedelta(days=30) < timestamp(collected) <= now:
            continue
        connection.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)",
                           (video["id"], json.dumps(video, ensure_ascii=False)))
        cached += 1
        if cached % 5000 == 0:
            connection.commit()
    connection.execute("""
        DELETE FROM metadata
        WHERE NOT EXISTS (SELECT 1 FROM requested WHERE requested.video_id = metadata.video_id)
    """)
    connection.execute("""
        INSERT INTO pending_metadata
        SELECT requested.video_id FROM requested
        LEFT JOIN metadata USING (video_id) WHERE metadata.video_id IS NULL
    """)
    connection.commit()
    requested_count = connection.execute("SELECT COUNT(*) FROM requested").fetchone()[0]
    pending_count = connection.execute("SELECT COUNT(*) FROM pending_metadata").fetchone()[0]
    return requested_count, pending_count


def export(connection: sqlite3.Connection, channels: list[dict], news: dict, status: str,
           pending_metadata_count: int = 0) -> int:
    allowed = {channel["id"] for channel in channels}
    connection.execute("""
        CREATE TABLE selected (
            channel_id TEXT NOT NULL, title_key TEXT NOT NULL, published_at_utc TEXT NOT NULL,
            video_id TEXT NOT NULL, row_json TEXT NOT NULL, is_batch_stats INTEGER NOT NULL,
            PRIMARY KEY (channel_id, title_key)
        )
    """)
    connection.execute("CREATE TABLE selected_titles (title_key TEXT, channel_id TEXT, PRIMARY KEY (title_key, channel_id))")
    eligible_video_ids = missing_like_video_ids = unavailable_video_ids = 0
    batch_stats_ids = metadata_checked = 0

    for video_id, payload, is_pending in connection.execute("""
        SELECT requested.video_id, metadata.payload,
               EXISTS(SELECT 1 FROM pending_metadata WHERE pending_metadata.video_id = requested.video_id)
        FROM requested LEFT JOIN metadata USING (video_id)
    """):
        if payload is None:
            continue
        video = json.loads(payload)
        metadata_checked += not is_pending
        is_batch = "videos.batchGetStats" in video.get("metadata_source", "")
        batch_stats_ids += is_batch
        if not video.get("snippet"):
            unavailable_video_ids += 1
        row = csv_row(video, allowed, news["start"], news["end"])
        if row is None:
            continue
        eligible_video_ids += 1
        if row["like_count"] == "":
            missing_like_video_ids += 1
            continue
        store_latest(connection, row, is_batch)
    connection.execute("INSERT OR IGNORE INTO selected_titles SELECT title_key, channel_id FROM selected")
    connection.commit()

    row_count, distinct_ids = connection.execute(
        "SELECT COUNT(*), COUNT(DISTINCT video_id) FROM selected").fetchone()
    if row_count != distinct_ids:
        raise ValueError("Selected export contains duplicate video IDs")

    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    temporary = EXPORT.with_suffix(".tmp")
    by_channel, by_month = Counter(), Counter()
    title_channel_count = connection.execute(
        "SELECT COUNT(*) FROM (SELECT title_key FROM selected_titles GROUP BY title_key HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    batch_stats_csv_rows = 0
    missing_view_count = missing_like_count = 0
    metrics_earliest = metrics_latest = None
    with temporary.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=COLUMNS)
        writer.writeheader()
        for payload, is_batch_stats in connection.execute("""
            SELECT row_json, is_batch_stats FROM selected ORDER BY published_at_utc, channel_id, video_id
        """):
            row = json.loads(payload)
            writer.writerow(row)
            by_channel[row["channel_id"]] += 1
            by_month[row["published_at_vn"][:7]] += 1
            missing_view_count += row["view_count"] == ""
            missing_like_count += row["like_count"] == ""
            batch_stats_csv_rows += is_batch_stats
            measured = row["metrics_collected_at_utc"]
            if measured:
                metrics_earliest = measured if metrics_earliest is None else min(metrics_earliest, measured)
                metrics_latest = measured if metrics_latest is None else max(metrics_latest, measured)
    temporary.replace(EXPORT)

    source = "YouTube Data API v3: videos.list (snippet,statistics)"
    if pending_metadata_count or batch_stats_ids:
        source = "YouTube Data API v3: playlistItems.list, channels.list, cached videos.list"
        if batch_stats_ids:
            source += ", videos.batchGetStats and supplemental search.list"
    full_scan_path = ROOT / "data/raw/youtube/news_titles_full_scan_state.json"
    full_scan = json.loads(full_scan_path.read_text(encoding="utf-8")) if full_scan_path.exists() else None
    report = {
        "source": source,
        "batch_stats_video_ids": batch_stats_ids,
        "batch_stats_csv_rows": batch_stats_csv_rows,
        "batch_stats_note": "For these IDs, title/date/channel come from playlistItems.list or supplemental search.list (see cache metadata_source), author from the channel registry, and actual statistics from videos.batchGetStats.",
        "status": "partial_metadata" if pending_metadata_count else (status if news["status"] == "complete" else "partial_collection"),
        "collection_status": news["status"], "target_rows": 100000, "target_reached": row_count >= 100000,
        "supplementary_full_scan": ({"status": full_scan["status"], "pages": full_scan["pages"],
                                      "new_video_ids": full_scan["new_video_ids"],
                                      "note": "Independent scan without the normal old-page cutoff; partial coverage is recorded separately from the regular uploads pass."}
                                     if full_scan else None),
        "csv_rows": row_count, "raw_video_ids": connection.execute("SELECT COUNT(*) FROM requested").fetchone()[0],
        "metadata_checked": metadata_checked,
        "metadata_pending_video_ids": pending_metadata_count,
        "csv_rows_pending_metadata": connection.execute("""
            SELECT COUNT(*) FROM selected WHERE EXISTS (
                SELECT 1 FROM pending_metadata WHERE pending_metadata.video_id = selected.video_id)
        """).fetchone()[0],
        "pending_metadata_note": "Uncached rows use the collected title/publication/channel and registry author; statistics and measurement time are blank. Fallbacks are not written to the API cache.",
        "start_utc": news["start"], "end_utc_exclusive": news["end"],
        "deduplication": "Videos without like_count are excluded first; among remaining videos, one normalized title per channel is kept, choosing the newest. Same titles from different channels are retained.",
        "author_definition": "The YouTube publishing channel title; not an individual reporter.",
        "statistics_definition": "Public cumulative counts at metrics_collected_at_utc, not counts on the publication date. Rows without like_count are excluded; a real zero is retained.",
        "title_groups_retained_across_channels": title_channel_count,
        "missing_view_count": missing_view_count,
        "missing_like_count": missing_like_count,
        "eligible_video_ids_before_like_filter": eligible_video_ids,
        "video_ids_excluded_missing_like_count": missing_like_video_ids,
        "unavailable_video_ids": unavailable_video_ids,
        "records_by_month_vn": dict(sorted(by_month.items())),
        "channels": [{**channel, "csv_rows": by_channel[channel["id"]]} for channel in channels],
        "export": str(EXPORT.relative_to(ROOT)), "columns": COLUMNS,
        "metrics_earliest_utc": metrics_earliest,
        "metrics_latest_utc": metrics_latest,
        "retention_note": "Refresh or delete YouTube API metadata within 30 calendar days.",
    }
    report_temporary = REPORT.with_suffix(".tmp")
    report_temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report_temporary.replace(REPORT)
    print(f"[CSV] {row_count:,} rows; {len(by_channel)} channels; {title_channel_count:,} cross-channel title groups retained.", flush=True)
    return row_count


def self_check() -> None:
    def sample(video_id, channel, published, likes):
        return {"id": video_id, "snippet": {"title": " Cùng  một vấn đề ", "channelId": channel,
                "channelTitle": "Kênh thử", "publishedAt": published},
                "statistics": {"viewCount": "0", "likeCount": likes}, "collected_at_utc": "2026-10-14T00:00:00Z"}
    values = [sample("a", "one", "2026-06-01T18:00:00Z", None), sample("b", "two", "2026-06-01T18:00:00Z", "0"),
              sample("c", "one", "2026-06-02T18:00:00Z", "5"),
              sample("d", "one", "2026-06-03T18:00:00Z", "6")]
    rows = select_rows({v["id"]: v for v in values}, {"one", "two"}, "2026-06-01", "2026-10-15")
    assert {r["video_id"] for r in rows} == {"b", "d"}
    assert rows[0]["published_at_vn"] == "2026-06-02T01:00:00+07:00"
    assert count(None) == "" and count("0") == "0"
    assert csv_row(values[0], {"one"}, "2026-06-02", "2026-10-15") is None
    connection = sqlite3.connect(":memory:")
    connection.execute("""
        CREATE TABLE selected (
            channel_id TEXT, title_key TEXT, published_at_utc TEXT,
            video_id TEXT, row_json TEXT, is_batch_stats INTEGER,
            PRIMARY KEY (channel_id, title_key)
        )
    """)
    for video in values[2:]:
        store_latest(connection, csv_row(video, {"one"}, "2026-06-01", "2026-10-15"), False)
    assert json.loads(connection.execute("SELECT row_json FROM selected").fetchone()[0])["video_id"] == "d"
    connection.close()
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
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="youtube-export-", dir=CACHE.parent) as work_dir:
        connection = sqlite3.connect(Path(work_dir) / "index.sqlite3")
        try:
            requested_count, pending_count = build_index(connection, datetime.now(timezone.utc))
            if args.cached_only:
                authors = {channel["id"]: channel["name"] for channel in channels}
                for video_id, channel_id, title, published in connection.execute("""
                    SELECT raw_video.video_id, raw_video.channel_id, raw_video.title, raw_video.created_at
                    FROM raw_video JOIN pending_metadata USING (video_id)
                """):
                    if channel_id not in authors:
                        continue
                    fallback = {
                        "id": video_id,
                        "snippet": {"title": title, "publishedAt": published,
                                    "channelId": channel_id, "channelTitle": authors[channel_id]},
                        "statistics": {}, "collected_at_utc": "",
                    }
                    connection.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)",
                                       (video_id, json.dumps(fallback, ensure_ascii=False)))
                connection.commit()
                export(connection, channels, news, "complete", pending_count)
                print(f"[CSV] Offline export: {pending_count:,} video IDs still need API metadata.", flush=True)
                return

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
                        found = {video["id"]: {**video, "collected_at_utc": collected}
                                 for video in result.get("items", [])}
                        return [found.get(video_id, {"id": video_id, "collected_at_utc": collected,
                                                     "unavailable": True}) for video_id in ids]
                    except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                        transient = isinstance(exc, (urllib.error.URLError, TimeoutError)) or any(
                            f"API {code}" in str(exc) for code in (500, 502, 503, 504))
                        if not transient or attempt == 2:
                            raise
                        time.sleep(2 ** (attempt + 1))

            print(f"[CSV] Fetching metadata/statistics for {pending_count:,} videos; "
                  f"{requested_count - pending_count:,} cached.", flush=True)
            status = "interrupted"
            try:
                last_video_id = ""
                with ThreadPoolExecutor(max_workers=4) as pool, CACHE.open("a", encoding="utf-8") as output:
                    while True:
                        ids = [row[0] for row in connection.execute("""
                            SELECT requested.video_id FROM requested
                            LEFT JOIN metadata USING (video_id)
                            WHERE metadata.video_id IS NULL AND requested.video_id > ?
                            ORDER BY requested.video_id LIMIT 200
                        """, (last_video_id,))]
                        if not ids:
                            break
                        last_video_id = ids[-1]
                        futures = [pool.submit(fetch, ids[offset:offset + 50])
                                   for offset in range(0, len(ids), 50)]
                        errors = []
                        for future in as_completed(futures):
                            try:
                                for video in future.result():
                                    output.write(json.dumps(video, ensure_ascii=False) + "\n")
                                    connection.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)",
                                                       (video["id"], json.dumps(video, ensure_ascii=False)))
                                    connection.execute("DELETE FROM pending_metadata WHERE video_id = ?",
                                                       (video["id"],))
                                output.flush()
                                connection.commit()
                            except Exception as exc:
                                errors.append(exc)
                        if errors:
                            raise errors[0]
                        checked = requested_count - connection.execute(
                            "SELECT COUNT(*) FROM requested LEFT JOIN metadata USING (video_id) "
                            "WHERE metadata.video_id IS NULL").fetchone()[0]
                        print(f"[CSV] {checked:,}/{requested_count:,} videos checked.", flush=True)
                status = "complete"
            finally:
                # Keep the existing CSV until every metadata batch has been handled.
                if status == "complete":
                    total = export(connection, channels, news, status)
            if total < 100000:
                print(f"[CSV] Need {100000 - total:,} more valid rows to reach the requested target.", flush=True)
        finally:
            connection.close()


if __name__ == "__main__":
    main()
